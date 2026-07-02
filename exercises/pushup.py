import cv2
import numpy as np
from exercises.base_exercise import BaseExercise
from utils.config_manager import ConfigManager

class PushUp(BaseExercise):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager().config['pushup']
        self.is_bottom = False # 是否已经下放到位
        self.threshold_bottom = self.config['threshold_bottom']
        self.threshold_top = self.config['threshold_top']
        
    def _get_primary_angle(self):
        return getattr(self, 'current_angle', 0)
        
    def _dist(self, p1, p2):
        """计算欧几里得距离"""
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    def _check_pose(self, img):
        # ... (保持关键点获取代码不变) ...
        right_arm_angle = self._get_angle(12, 14, 16)
        left_arm_angle = self._get_angle(11, 13, 15)
        
        right_body_angle = self._get_angle(12, 24, 28)
        left_body_angle = self._get_angle(11, 23, 27)
        
        # 获取肩部和手腕坐标用于计算间距
        l_shoulder = self._get_point(11)
        r_shoulder = self._get_point(12)
        l_wrist = self._get_point(15)
        r_wrist = self._get_point(16)

        # 选择检测到的一侧
        arm_angle = None
        body_angle = None
        side = "" 

        if right_arm_angle and right_body_angle:
            arm_angle = right_arm_angle
            body_angle = right_body_angle
            side = "right"
            elbow_pos = self._get_point(14)
        elif left_arm_angle and left_body_angle:
            arm_angle = left_arm_angle
            body_angle = left_body_angle
            side = "left"
            elbow_pos = self._get_point(13)
        
        if arm_angle is None or body_angle is None:
            self.feedback = "未检测到身体"
            self.current_angle = 0
            return

        self.current_angle = arm_angle

        # --- 纠错逻辑 ---
        # 1. 身体平直度检查
        is_body_straight = True
        if body_angle < 155:
            self.feedback = "请挺直背部!"
            is_body_straight = False
            # 画出错误的身体线
            p_shoulder = self._get_point(12 if side=="right" else 11)
            p_hip = self._get_point(24 if side=="right" else 23)
            p_ankle = self._get_point(28 if side=="right" else 27)
            if p_shoulder and p_hip:
                cv2.line(img, tuple(p_shoulder), tuple(p_hip), (0, 0, 255), 4)
            if p_hip and p_ankle:
                cv2.line(img, tuple(p_hip), tuple(p_ankle), (0, 0, 255), 4)
        
        # 2. 手间距检查 (新)
        is_hands_wide_enough = True
        if l_shoulder and r_shoulder and l_wrist and r_wrist:
            shoulder_width = self._dist(l_shoulder, r_shoulder)
            hand_width = self._dist(l_wrist, r_wrist)
            
            # 阈值：手宽应该至少是肩宽的 0.7 倍 (窄距俯卧撑通常 < 0.5-0.6)
            # 标准俯卧撑通常 > 1.0
            if shoulder_width > 0:
                ratio = hand_width / shoulder_width
                # 在画面上显示比例调试用 (可选)
                # cv2.putText(img, f"Ratio: {ratio:.2f}", (20, 200), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
                
                if ratio < 0.8: # 认为太窄
                    self.feedback = "请加宽双手间距" # 优先级高，覆盖掉塌腰提示
                    is_hands_wide_enough = False
                    # 画连接线提示
                    cv2.line(img, tuple(l_wrist), tuple(r_wrist), (0, 0, 255), 3)

        if is_body_straight and is_hands_wide_enough:
            self.feedback = "动作标准"
            self.form_correct = True
        else:
            self.form_correct = False
            
        # --- 计数逻辑 (宽松版) ---
        # 即使动作不标准，只要完成了幅度，也计数 (体测时通常有人工计数，机器可以宽容一点但给警告)
        # 或者严格一点：必须身体直才算。
        # 考虑到 fwc2.mp4 可能只是手窄，计数应该还是要走的。
        
        # 1. 检测下放
        if arm_angle <= self.threshold_bottom:
            self.is_bottom = True # 标记已触底
        
        # 2. 检测回升
        if self.is_bottom and arm_angle >= self.threshold_top:
            self.count += 1
            self.is_bottom = False # 重置标记
        
        # 显示角度
        if elbow_pos:
            cv2.putText(img, str(int(arm_angle)), (elbow_pos[0], elbow_pos[1]+20), 
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
