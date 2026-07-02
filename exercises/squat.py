import cv2
import numpy as np
from exercises.base_exercise import BaseExercise
from utils.config_manager import ConfigManager

class Squat(BaseExercise):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager().config['squat']
        self.direction = 0  # 0: 站立/下降中, 1: 下蹲到底/上升中
        self.state = "up"   # up, down
        self.threshold_down = self.config['threshold_down']
        self.threshold_up = self.config['threshold_up']
        
    def _get_primary_angle(self):
        # 深蹲主要关注腿部角度
        return getattr(self, 'current_angle', 0)

    def _check_pose(self, img):
        # 1. 关键点获取
        # 23: 左髋, 24: 右髋
        # 25: 左膝, 26: 右膝
        # 27: 左踝, 28: 右踝
        
        # 计算腿部角度 (髋-膝-踝) -> 判断下蹲深度
        right_leg_angle = self._get_angle(24, 26, 28)
        left_leg_angle = self._get_angle(23, 25, 27)
        
        # 计算背部角度 (肩-髋-膝) -> 判断上身前倾或弯腰 (简单近似)
        # 12: 右肩, 24: 右髋, 26: 右膝
        right_back_angle = self._get_angle(12, 24, 26)
        
        # 确定主检测侧 (侧身对镜头)
        leg_angle = None
        side = ""
        
        if right_leg_angle:
            leg_angle = right_leg_angle
            side = "right"
            knee_pos = self._get_point(26)
        elif left_leg_angle:
            leg_angle = left_leg_angle
            side = "left"
            knee_pos = self._get_point(25)
            
        if leg_angle is None:
            self.feedback = "未检测到腿部"
            self.current_angle = 0
            return
            
        self.current_angle = leg_angle

        # --- 纠错逻辑 ---
        # 1. 膝盖内扣检测 (Front view only, 侧面较难)
        # 这里主要检测下蹲深度不够
        
        # 2. 上身前倾过度
        # 正常站立约 180，深蹲时可能到 90-120
        # 如果太小说明趴下了
        if right_back_angle and right_back_angle < 60:
             self.feedback = "请保持上半身直立!"
             self.form_correct = False
        else:
             self.feedback = "动作标准"
             self.form_correct = True
             
        # --- 计数逻辑 ---
        # 站立时膝盖角度约 170-180
        # 标准深蹲大腿平行地面，膝盖角度约 90度左右
        
        # 状态转换阈值
        # angle_down = 100  # 使用配置
        # angle_up = 160    # 使用配置
        
        if leg_angle <= self.threshold_down:
            if self.direction == 0:
                self.direction = 1 # 到底部了，准备上升
                
        if self.direction == 1:
            if leg_angle >= self.threshold_up:
                self.count += 1
                self.direction = 0 # 完成一次
                
        # 调试显示
        if knee_pos:
             cv2.putText(img, str(int(leg_angle)), (knee_pos[0], knee_pos[1]+20), 
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
