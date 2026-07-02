import cv2
import numpy as np
from exercises.base_exercise import BaseExercise
from utils.config_manager import ConfigManager

class SitUp(BaseExercise):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager().config['situp']
        self.is_down = False
        # 调整阈值
        self.threshold_up_angle = self.config['threshold_up_angle']
        self.threshold_down_angle = 105  # 躺下角度
        self.threshold_up_ratio = self.config['threshold_up_ratio']    # 起身高度比
        self.threshold_down_ratio = 0.15 # 躺下高度比
        
    def _get_primary_angle(self):
        return getattr(self, 'current_angle', 0)

    def _dist(self, p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    def _check_pose(self, img):
        # 侧身检测：肩-髋-膝
        right_angle = self._get_angle(12, 24, 26)
        left_angle = self._get_angle(11, 23, 25)
        
        angle = None
        hip_pos = None
        shoulder_pos = None
        
        # 确定检测侧
        if right_angle: 
            angle = right_angle
            hip_pos = self._get_point(24)
            shoulder_pos = self._get_point(12)
        elif left_angle: 
            angle = left_angle
            hip_pos = self._get_point(23)
            shoulder_pos = self._get_point(11)
        
        if angle is None or hip_pos is None or shoulder_pos is None:
            self.feedback = "未检测到侧身"
            self.current_angle = 0
            return
            
        self.current_angle = angle
        
        # 计算垂直高度比 (Vertical Ratio)
        # 坐标系: Y向下增大。Hip.y > Shoulder.y 说明肩在髋上方
        vert_diff = hip_pos[1] - shoulder_pos[1] 
        torso_len = self._dist(hip_pos, shoulder_pos)
        
        ratio = 0
        if torso_len > 0:
            ratio = vert_diff / torso_len
            
        # --- 计数逻辑 (双重校验) ---
        
        # 1. 检测躺下 (Down)
        # 角度很大 OR 高度差很小
        if angle >= self.threshold_down_angle or ratio < self.threshold_down_ratio:
            self.is_down = True
            self.feedback = "准备起身"
            
        # 2. 检测起身 (Up)
        # 必须同时满足：高度够高 (ratio) AND 身体卷曲 (angle)
        # 或者只由 ratio 主导，angle 辅助
        is_up_pose = (ratio > self.threshold_up_ratio) and (angle < self.threshold_up_angle)
        
        if self.is_down and is_up_pose:
            self.count += 1
            self.is_down = False
            self.feedback = "完成一次"
            
        # --- 纠错逻辑 ---
        if not self.is_down:
             # 在起身保持状态，或者刚下去
             if ratio < self.threshold_up_ratio and ratio > self.threshold_down_ratio:
                 self.feedback = "请完全躺下"
        
        # 调试显示
        # cv2.putText(img, f"R:{ratio:.2f} A:{int(angle)}", (int(hip_pos[0]), int(hip_pos[1])+20), 
        #             cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
        if hip_pos:
             cv2.putText(img, str(int(angle)), (int(hip_pos[0]), int(hip_pos[1])+20), 
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
