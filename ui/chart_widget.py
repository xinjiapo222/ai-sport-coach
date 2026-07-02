from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
import numpy as np
import os

# 设置中文字体 (尝试自动寻找可用字体，避免中文乱码)
plt.rcParams['font.sans-serif'] = ['Droid Sans Fallback', 'Noto Sans CJK SC', 'SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

class RealTimeChart(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        cjk_path = next((path for path in (
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "C:/Windows/Fonts/msyh.ttc",
        ) if os.path.exists(path)), None)
        self.cjk_font = FontProperties(fname=cjk_path) if cjk_path else FontProperties()
        self.tick_font = FontProperties(family="DejaVu Sans")
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Data buffers
        self.max_points = 100
        self.data_y = []
        self.data_x = []
        self._update_counter = 0
        
        # Initial plot
        self.line, = self.axes.plot([], [], 'g-', linewidth=2)
        self.axes.set_title("实时动作波形分析", fontproperties=self.cjk_font)
        self.axes.set_xlabel("时间（帧）", fontproperties=self.cjk_font)
        self.axes.set_ylabel("动作幅度（角度/高度）", fontproperties=self.cjk_font)
        self.axes.set_xlim(0, self.max_points)
        self.axes.set_ylim(0, 180)
        self.axes.grid(True)
        for label in self.axes.get_xticklabels() + self.axes.get_yticklabels():
            label.set_fontproperties(self.tick_font)

    def update_chart(self, new_value):
        if new_value is None:
            return

        self.data_y.append(new_value)
        # Keep x consistent
        if len(self.data_x) < len(self.data_y):
            self.data_x.append(len(self.data_y))
            
        # Trim buffers
        if len(self.data_y) > self.max_points:
            self.data_y = self.data_y[-self.max_points:]
            self.data_x = list(range(len(self.data_y))) # reset x to 0..100 relative

        self.line.set_data(self.data_x, self.data_y)
        self.axes.set_xlim(0, max(len(self.data_y), 50))
        self._update_counter += 1
        if self._update_counter % 3 == 0:
            self.draw_idle()
