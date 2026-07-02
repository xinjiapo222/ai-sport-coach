import os
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QImage
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from core.pose_detector import PoseDetector
from exercises.pushup import PushUp
from exercises.squat import Squat
from exercises.jump_rope import JumpRope
from exercises.situp import SitUp
from exercises.pullup import PullUp
from utils.voice_feedback import VoiceAssistant
from utils.config_manager import ConfigManager

class VideoThread(QThread):
    change_pixmap_signal = Signal(QImage)
    update_data_signal = Signal(int, str, float) # count, feedback, chart_value
    
    def __init__(self, video_source=0, exercise_type="pushup"):
        super().__init__()
        self.video_source = video_source
        self.exercise_type = exercise_type
        self._run_flag = True
        self.detector = PoseDetector()
        self.voice = VoiceAssistant() # 语音助手
        self.current_exercise = None
        self._init_exercise()

    def _init_exercise(self):
        if self.exercise_type == "pushup":
            self.current_exercise = PushUp()
        elif self.exercise_type == "squat":
            self.current_exercise = Squat()
        elif self.exercise_type == "jumprope":
            self.current_exercise = JumpRope()
        elif self.exercise_type == "situp":
            self.current_exercise = SitUp()
        elif self.exercise_type == "pullup":
            self.current_exercise = PullUp()
        else:
            self.current_exercise = None

    def set_exercise(self, exercise_type):
        self.exercise_type = exercise_type
        self._init_exercise()
        
    def set_source(self, source):
        self.video_source = source
        self.stop()
        self.wait() # 等待当前线程结束
        self._run_flag = True
        self.start()

    def run(self):
        actual_source = self.video_source
        if self.video_source == 0:
            actual_source = int(os.environ.get("AI_SPORT_CAMERA", "0"))
        cap = cv2.VideoCapture(actual_source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Set resolution if using camera (source 0)
        if self.video_source == 0:
            config = ConfigManager().config['camera']
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['width'])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['height'])
        
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pose")
        inference = None
        latest_landmarks = []
        latest_stats = (0, "正在识别动作…", 0.0)
        frame_history = deque(maxlen=120)
        frame_id = 0
        tracked_gray = None
        ui_emit_counter = 0

        while self._run_flag:
            ret, cv_img = cap.read()
            if not ret:
                # 视频播放结束，如果是文件则循环
                if isinstance(self.video_source, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break # 摄像头断开

            frame_id += 1
            current_gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            frame_history.append((frame_id, current_gray))

            # 在两次 AI 推理之间，用稀疏光流把骨架连续跟到当前帧。
            if latest_landmarks and tracked_gray is not None:
                latest_landmarks = self._track_landmarks(
                    latest_landmarks, tracked_gray, current_gray
                )
            tracked_gray = current_gray
            
            # 推理在独立线程执行；摄像头采集和界面刷新不再等待 CPU 模型。
            if inference is None:
                inference = executor.submit(self._process_pose, cv_img.copy(), frame_id)
            elif inference.done():
                try:
                    source_id, source_gray, detected_landmarks = inference.result()
                    latest_landmarks = detected_landmarks
                    previous_gray = source_gray
                    for history_id, history_gray in frame_history:
                        if history_id > source_id and latest_landmarks:
                            latest_landmarks = self._track_landmarks(
                                latest_landmarks, previous_gray, history_gray
                            )
                            previous_gray = history_gray
                    tracked_gray = current_gray
                except Exception as exc:
                    print(f"Pose inference error: {exc}")
                inference = executor.submit(self._process_pose, cv_img.copy(), frame_id)

            # 计数状态机在每个实时跟踪帧运行，避免漏掉动作的最高点和最低点。
            if self.current_exercise and latest_landmarks:
                cv_img, count, feedback, chart_val = self.current_exercise.process(
                    cv_img, latest_landmarks, draw_info=False
                )
                latest_stats = (count, feedback, chart_val)
                ui_emit_counter += 1
                if ui_emit_counter % 3 == 0:
                    self.update_data_signal.emit(int(count), feedback, float(chart_val or 0))
                ignore_list = [
                    "动作标准", "节奏不错", "准备就绪", "请开始跳跃", "准备起身",
                    "完成一次", "用力拉起", "", "未检测到身体", "未检测到腿部",
                    "未检测到双脚", "未检测到侧身", "未检测到手臂"
                ]
                if feedback not in ignore_list:
                    self.voice.speak(feedback)

            self._draw_cached_pose(cv_img, latest_landmarks)
            
            # 4. 转换图像格式给 Qt
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            p = convert_to_qt_format.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio)
            
            self.change_pixmap_signal.emit(p)
            
            # 稍微控制帧率，避免 CPU 占用过高
            time.sleep(0.01)
            
        cap.release()
        executor.shutdown(wait=False, cancel_futures=True)

    def _process_pose(self, frame, frame_id):
        source_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.detector.find_pose(frame, draw=False)
        landmarks = self.detector.find_position(frame, draw=False)
        return frame_id, source_gray, landmarks

    @staticmethod
    def _track_landmarks(landmarks, previous_gray, current_gray):
        if not landmarks or previous_gray.shape != current_gray.shape:
            return landmarks
        old_points = np.float32([[item[1], item[2]] for item in landmarks]).reshape(-1, 1, 2)
        new_points, status, error = cv2.calcOpticalFlowPyrLK(
            previous_gray,
            current_gray,
            old_points,
            None,
            winSize=(31, 31),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 0.03),
        )
        if new_points is None:
            return landmarks
        h, w = current_gray.shape[:2]
        tracked = []
        for item, point, ok, point_error in zip(landmarks, new_points, status, error):
            x, y = point.ravel()
            if ok and point_error[0] < 40 and 0 <= x < w and 0 <= y < h:
                tracked.append([item[0], int(x), int(y)])
            else:
                # Keep the last known joint until the next fast MoveNet refresh;
                # dropping IDs breaks angle calculations and exercise state.
                tracked.append(item)
        return tracked

    @staticmethod
    def _draw_cached_pose(frame, landmarks):
        if not landmarks:
            return
        points = {item[0]: (item[1], item[2]) for item in landmarks}
        connections = (
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
            (11, 23), (12, 24), (23, 24), (23, 25), (25, 27),
            (24, 26), (26, 28),
        )
        for a, b in connections:
            if a in points and b in points:
                cv2.line(frame, points[a], points[b], (0, 255, 0), 2)
        for point in points.values():
            cv2.circle(frame, point, 4, (255, 0, 0), cv2.FILLED)

    def stop(self):
        self._run_flag = False
        self.wait()
