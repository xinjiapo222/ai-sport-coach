"""Pose detection with MediaPipe on PCs and ONNX Runtime on RISC-V boards."""

import os

import cv2
import numpy as np


class PoseDetector:
    # COCO keypoints produced by YOLO pose -> MediaPipe indices used by exercises.
    COCO_TO_MEDIAPIPE = {
        0: 0, 1: 2, 2: 5, 3: 7, 4: 8,
        5: 11, 6: 12, 7: 13, 8: 14, 9: 15, 10: 16,
        11: 23, 12: 24, 13: 25, 14: 26, 15: 27, 16: 28,
    }
    CONNECTIONS = (
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
        (5, 11), (6, 12), (11, 12), (11, 13), (13, 15),
        (12, 14), (14, 16),
    )

    def __init__(self, mode=False, complexity=1, smooth_landmarks=True,
                 enable_segmentation=False, smooth_segmentation=True,
                 detection_con=0.5, track_con=0.5):
        self.detection_con = detection_con
        self._positions = []
        self.backend = "mediapipe"
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=mode,
                model_complexity=complexity,
                smooth_landmarks=smooth_landmarks,
                enable_segmentation=enable_segmentation,
                smooth_segmentation=smooth_segmentation,
                min_detection_confidence=detection_con,
                min_tracking_confidence=track_con,
            )
            self.mp_drawing = mp.solutions.drawing_utils
        except ImportError:
            self.backend = "onnx"
            self._init_onnx()

    def _init_onnx(self):
        import onnxruntime as ort

        model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        movenet_model = os.path.join(model_dir, "movenet-lightning.onnx")
        default_model = (
            movenet_model if os.path.exists(movenet_model)
            else os.path.join(model_dir, "yolov8n-pose.onnx")
        )
        model = os.environ.get("AI_SPORT_POSE_MODEL", default_model)
        if not os.path.exists(model):
            raise FileNotFoundError(f"Pose model not found: {model}")
        available = ort.get_available_providers()
        preferred = [
            name for name in ("SpacemitExecutionProvider", "SpaceMITExecutionProvider")
            if name in available
        ]
        preferred.append("CPUExecutionProvider")
        options = ort.SessionOptions()
        options.intra_op_num_threads = int(os.environ.get("AI_SPORT_ORT_THREADS", "8"))
        options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(model, sess_options=options, providers=preferred)
        self.input_name = self.session.get_inputs()[0].name
        model_input = self.session.get_inputs()[0]
        shape = model_input.shape
        output_shape = self.session.get_outputs()[0].shape
        self.model_kind = "movenet" if len(output_shape) == 4 and output_shape[-2:] == [17, 3] else "yolo"
        if self.model_kind == "movenet":
            self.input_h = int(shape[1])
            self.input_w = int(shape[2])
            self.input_dtype = np.int32 if "int32" in model_input.type else np.float32
        else:
            self.input_h = int(shape[2]) if isinstance(shape[2], int) else 640
            self.input_w = int(shape[3]) if isinstance(shape[3], int) else 640
            self.input_dtype = np.float32
        print(
            f"Pose backend: ONNX Runtime/{self.model_kind} "
            f"({self.session.get_providers()[0]}, {self.input_w}x{self.input_h})"
        )

    def find_pose(self, img, draw=True):
        if self.backend == "mediapipe":
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.results = self.pose.process(img_rgb)
            if self.results.pose_landmarks and draw:
                self.mp_drawing.draw_landmarks(
                    img, self.results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS
                )
            return img

        self._positions = self._infer_onnx(img)
        if draw and self._positions:
            points = {p[0]: (p[1], p[2]) for p in self._positions}
            coco_points = {coco: points[mp] for coco, mp in self.COCO_TO_MEDIAPIPE.items()
                           if mp in points}
            for a, b in self.CONNECTIONS:
                if a in coco_points and b in coco_points:
                    cv2.line(img, coco_points[a], coco_points[b], (0, 255, 0), 2)
            for _, x, y in self._positions:
                cv2.circle(img, (x, y), 4, (255, 0, 0), cv2.FILLED)
        return img

    def _infer_onnx(self, img):
        h, w = img.shape[:2]
        scale = min(self.input_w / w, self.input_h / h)
        nw, nh = int(round(w * scale)), int(round(h * scale))
        resized = cv2.resize(img, (nw, nh))
        pad_x, pad_y = (self.input_w - nw) // 2, (self.input_h - nh) // 2
        canvas = np.full((self.input_h, self.input_w, 3), 114, dtype=np.uint8)
        canvas[pad_y:pad_y + nh, pad_x:pad_x + nw] = resized
        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        if self.model_kind == "movenet":
            tensor = np.ascontiguousarray(rgb, dtype=self.input_dtype)[None]
        else:
            tensor = np.ascontiguousarray(rgb.transpose(2, 0, 1), dtype=np.float32)[None] / 255.0
        output = np.asarray(self.session.run(None, {self.input_name: tensor})[0])
        if self.model_kind == "movenet":
            keypoints = output.reshape(17, 3)
            positions = []
            for coco_id, (y, x, confidence) in enumerate(keypoints):
                if confidence < 0.20 or coco_id not in self.COCO_TO_MEDIAPIPE:
                    continue
                input_x, input_y = x * self.input_w, y * self.input_h
                px = int(np.clip((input_x - pad_x) / scale, 0, w - 1))
                py = int(np.clip((input_y - pad_y) / scale, 0, h - 1))
                positions.append([self.COCO_TO_MEDIAPIPE[coco_id], px, py])
            return positions

        pred = output[0]
        if pred.ndim != 2:
            return []
        # Ultralytics exports channels-first [56, anchors].
        if pred.shape[0] < pred.shape[1] and pred.shape[0] <= 128:
            pred = pred.T
        if pred.shape[1] < 56:
            return []
        best = pred[int(np.argmax(pred[:, 4]))]
        if float(best[4]) < self.detection_con:
            return []
        keypoints = best[5:56].reshape(17, 3)
        positions = []
        for coco_id, (x, y, confidence) in enumerate(keypoints):
            if confidence < 0.35 or coco_id not in self.COCO_TO_MEDIAPIPE:
                continue
            px = int(np.clip((x - pad_x) / scale, 0, w - 1))
            py = int(np.clip((y - pad_y) / scale, 0, h - 1))
            positions.append([self.COCO_TO_MEDIAPIPE[coco_id], px, py])
        return positions

    def find_position(self, img, draw=True):
        if self.backend == "onnx":
            if draw:
                for _, x, y in self._positions:
                    cv2.circle(img, (x, y), 5, (255, 0, 0), cv2.FILLED)
            return self._positions

        positions = []
        if self.results.pose_landmarks:
            h, w = img.shape[:2]
            for idx, landmark in enumerate(self.results.pose_landmarks.landmark):
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                positions.append([idx, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
        return positions
