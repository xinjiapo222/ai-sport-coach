import cv2
import numpy as np
from exercises.base_exercise import BaseExercise
from utils.config_manager import ConfigManager

class PullUp(BaseExercise):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager().config['pullup']
        self.ready_up = False
        self.threshold_arm_straight = self.config['threshold_arm_straight'] # 手臂伸直阈值
        self.threshold_arm_flex = 85      # 手臂弯曲阈值
        
    def _get_primary_angle(self):
        return getattr(self, 'current_angle', 0)

    def _check_pose(self, img):
        # 关键点
        right_arm = self._get_angle(12, 14, 16)
        left_arm = self._get_angle(11, 13, 15)
        
        nose = self._get_point(0)
        l_wrist = self._get_point(15)
        r_wrist = self._get_point(16)
        
        arm_angle = None
        wrist_y = None
        elbow_pos = None
        
        if right_arm:
            arm_angle = right_arm
            elbow_pos = self._get_point(14)
        elif left_arm:
            arm_angle = left_arm
            elbow_pos = self._get_point(13)

        if r_wrist and l_wrist:
            wrist_y = min(r_wrist[1], l_wrist[1])
        elif r_wrist:
            wrist_y = r_wrist[1]
        elif l_wrist:
            wrist_y = l_wrist[1]
            
        if arm_angle is None:
            self.feedback = "未检测到手臂"
            self.current_angle = 0
            return
            
        self.current_angle = arm_angle
        
        # --- 计数逻辑 ---
        # 下巴过手判断 (鼻子Y < 手腕Y，坐标越小越高)
        is_chin_up = False
        if nose and wrist_y:
            if nose[1] < wrist_y:
                is_chin_up = True

        # 1. 下放到位，进入准备上拉状态
        if arm_angle >= self.threshold_arm_straight and not is_chin_up:
            self.ready_up = True
            self.feedback = "用力拉起"

        # 2. 上拉到位：下巴过手 或 手臂充分弯曲
        is_angle_ok = arm_angle <= self.threshold_arm_flex
        if self.ready_up and (is_chin_up or is_angle_ok):
            self.count += 1
            self.ready_up = False
            self.feedback = "完成一次"

        # --- 纠错 ---
        if not self.ready_up:
            if arm_angle < self.threshold_arm_straight and arm_angle > self.threshold_arm_flex:
                self.feedback = "请完全伸直手臂"

        # 调试显示
        if elbow_pos:
            cv2.putText(img, str(int(arm_angle)), (int(elbow_pos[0]), int(elbow_pos[1])+20), 
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
