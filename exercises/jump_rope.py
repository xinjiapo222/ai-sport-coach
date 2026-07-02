import cv2
import numpy as np
import time
from exercises.base_exercise import BaseExercise

class JumpRope(BaseExercise):
    def __init__(self):
        super().__init__()
        self.state = "ground" # ground, air
        self.ground_y = None # 记录地面的 Y 坐标 (踝关节初始位置)
        self.last_jump_time = 0
        self.jump_intervals = []
        self.buffer_y = [] # 简单的平滑缓冲
        
    def _get_primary_angle(self):
        # 跳绳没有主要关注的角度，我们可以返回 踝关节的相对高度 用于画图
        # 为了画图直观，我们返回 (1 - y) * 180 这种模拟值，或者直接返回 0
        return getattr(self, 'current_height_indicator', 0)

    def _check_pose(self, img):
        # 1. 关键点: 左踝(27), 右踝(28)
        left_ankle = self._get_point(27)
        right_ankle = self._get_point(28)
        
        # 还要获取髋部作为参考，防止是全屏抖动
        left_hip = self._get_point(23)
        right_hip = self._get_point(24)
        
        if not left_ankle or not right_ankle:
            self.feedback = "未检测到双脚"
            self.current_height_indicator = 0
            return

        # 计算双脚平均 Y 坐标 (MediaPipe 坐标系：0在顶部，1在底部)
        # 所以跳起来时，Y 值变小
        avg_ankle_y = (left_ankle[1] + right_ankle[1]) / 2.0
        
        # 获取画面高度用于归一化阈值 (img.shape[0])
        h, w, c = img.shape
        # 实际像素 Y
        real_y = avg_ankle_y
        
        # 初始化地面基准 (前30帧的平均值，或者动态更新)
        # 这里简单处理：取前几帧的最低点(数值最大)作为地面
        if self.ground_y is None:
            self.ground_y = avg_ankle_y
        else:
            # 缓慢更新地面位置，适应相机微调，但要排除跳跃过程
            # 只有当 current y > ground_y (更低) 时才大幅更新
            if avg_ankle_y > self.ground_y:
                self.ground_y = avg_ankle_y
            else:
                # 极其缓慢的漂移回归
                self.ground_y = self.ground_y * 0.999 + avg_ankle_y * 0.001

        # 计算跳跃高度差 (相对于地面)
        # 越大约高
        jump_height = self.ground_y - avg_ankle_y
        
        # 归一化高度指标用于画图 (放大 1000 倍方便看)
        self.current_height_indicator = jump_height * 1000 
        if self.current_height_indicator < 0: self.current_height_indicator = 0
        
        # 阈值：假设跳起高度超过 画面高度的 2% ~ 5%
        # MediaPipe 坐标是 0~1 的 float (如果 get_point 返回的是像素，需要转换)
        # 检查 PoseDetector，find_position 返回的是 像素坐标 [id, cx, cy]
        # 所以 jump_height 是像素值
        
        threshold = h * 0.03 # 3% 的屏幕高度作为跳跃阈值
        
        # --- 计数逻辑 (状态机) ---
        if self.state == "ground":
            if jump_height > threshold:
                self.state = "air"
        
        elif self.state == "air":
            if jump_height < threshold / 2: # 回落
                self.state = "ground"
                self.count += 1
                self._analyze_rhythm()

        # --- 反馈逻辑 ---
        # 1. 节奏检测
        if len(self.jump_intervals) > 1:
            recent_intervals = self.jump_intervals[-5:]
            variance = np.var(recent_intervals)
            if variance > 0.05: # 阈值需调试
                self.feedback = "请保持节奏" # 保持节奏
            else:
                self.feedback = "节奏不错"
        else:
            self.feedback = "请开始跳跃"
            
        # 2. 只有脚动身体不动？(暂不处理)
        
        # 绘制地面线
        cv2.line(img, (0, int(self.ground_y)), (w, int(self.ground_y)), (0, 255, 255), 2)

    def _analyze_rhythm(self):
        current_time = time.time()
        if self.last_jump_time != 0:
            interval = current_time - self.last_jump_time
            # 过滤误判 (太快的抖动 < 0.2s)
            if interval > 0.2:
                self.jump_intervals.append(interval)
                if len(self.jump_intervals) > 100:
                    self.jump_intervals.pop(0)
        self.last_jump_time = current_time
