import cv2
import numpy as np
from core.geometry_utils import calculate_angle
from utils.draw_utils import put_chinese_text

class BaseExercise:
    def __init__(self):
        self.landmarks = []
        self.count = 0
        self.state = None  # 'up', 'down', etc.
        self.feedback = ""
        self.form_correct = True
        
    def process(self, img, lm_list, draw_info=True):
        """
        处理每一帧
        :param img: 当前视频帧
        :param lm_list: MediaPipe 识别出的关键点列表 [[id, x, y], ...]
        :return: 处理后的图像, 当前计数, 反馈信息
        """
        self.landmarks = lm_list
        if len(self.landmarks) == 0:
            return img, self.count, self.feedback, 0
        
        # 执行子类定义的特定逻辑
        self._check_pose(img)
        
        # 绘制通用信息
        if draw_info:
            img = self._draw_info(img)
        
        # 返回需要绘制图表的数据 (例如主要关注的角度)
        chart_val = self._get_primary_angle()
        
        return img, self.count, self.feedback, chart_val

    def _get_primary_angle(self):
        """子类返回用于绘图的主要角度值"""
        return None

    def _check_pose(self, img):
        """需要子类实现具体的姿态检测逻辑"""
        raise NotImplementedError

    def _get_point(self, idx):
        """安全获取关键点坐标"""
        try:
            point = [p for p in self.landmarks if p[0] == idx][0][1:]
            return point
        except IndexError:
            return None

    def _get_angle(self, idx1, idx2, idx3):
        """获取三个关键点的角度"""
        p1 = self._get_point(idx1)
        p2 = self._get_point(idx2)
        p3 = self._get_point(idx3)
        
        if p1 is None or p2 is None or p3 is None:
            return None
        
        return calculate_angle(p1, p2, p3)

    def _draw_info(self, img):
        """绘制计数板和反馈框"""
        # 绘制半透明背景板
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (300, 180), (245, 117, 16), -1) # 加宽一点适应中文
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

        # 状态/反馈标题
        img = put_chinese_text(img, "完成次数", (20, 20), (255, 255, 255), 30)
        
        # 计数 (数字)
        cv2.putText(img, str(int(self.count)), (30, 120), 
                    cv2.FONT_HERSHEY_DUPLEX, 3, (255, 255, 255), 5)
        
        # 反馈文字颜色：正确绿色，错误红色
        color = (0, 255, 0) if self.form_correct else (0, 0, 255)
        
        # 绘制反馈
        img = put_chinese_text(img, self.feedback, (20, 140), color, 30)
        
        # 由于 put_chinese_text 返回的是新图片引用，BaseExercise.process 里的 self._draw_info(img) 调用方式
        # 如果是 img = self._draw_info(img) 最好，但现在 _draw_info 是 void 风格修改 img
        # 但 put_chinese_text 可能会返回新对象。
        # 这是一个潜在问题。PIL 转换会生成新 numpy 数组。
        # 所以我需要修改 _draw_info 让它返回 img，并在 process 里接收。
        return img
