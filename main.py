import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QComboBox, 
                             QGroupBox, QFrame)
from PySide6.QtGui import QPixmap, QFont, QImage
from PySide6.QtCore import Slot, Qt
from ui.video_thread import VideoThread
from ui.settings_dialog import SettingsDialog
from utils.path_utils import get_resource_path

from ui.chart_widget import RealTimeChart

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Cloud Sport Coach - 智能体测系统")
        self.setGeometry(100, 100, 1400, 850) # Widen window for chart
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f2f5; color: #202124; }
            QWidget { font-family: 'Droid Sans Fallback', 'Noto Sans CJK SC', sans-serif; color: #202124; }
            QLabel { color: #202124; background-color: transparent; }
            QGroupBox { color: #202124; font-weight: bold; border: 1px solid #b8bec6; border-radius: 5px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }
            QPushButton { background-color: #007bff; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #0056b3; }
            QComboBox { color: white; background-color: #343a40; padding: 5px; border-radius: 3px; border: 1px solid #666; }
            QComboBox QAbstractItemView { color: white; background-color: #343a40; selection-background-color: #007bff; }
        """)

        # State
        self.is_running = True
        self.current_video_file = None # 存储当前选择的视频路径

        # Layouts
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout() # 左右结构
        main_widget.setLayout(main_layout)

        # --- Left Panel: Controls & Stats ---
        left_panel = QFrame()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # 1. 标题区
        title_label = QLabel("AI Sport Coach")
        title_label.setFont(QFont('Droid Sans Fallback', 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title_label)
        
        # 2. 运动选择
        mode_group = QGroupBox("选择运动模式")
        mode_layout = QVBoxLayout()
        
        self.combo_exercise = QComboBox()
        self.combo_exercise.addItems(["俯卧撑 (Push Up)", "深蹲 (Squat)", "跳绳 (Jump Rope)", "仰卧起坐 (Sit Up)", "引体向上 (Pull Up)"])
        self.combo_exercise.currentIndexChanged.connect(self.change_exercise)
        mode_layout.addWidget(self.combo_exercise)
        
        self.combo_source = QComboBox()
        self.combo_source.addItems(["摄像头 (Camera)", "视频: 俯卧撑 (Push Up)", "视频: 深蹲 (Squat)", "视频: 跳绳 (Jump Rope)", "视频: 仰卧起坐 (Sit Up)", "视频: 引体向上 (Pull Up)"])
        self.combo_source.currentIndexChanged.connect(self.change_source)
        mode_layout.addWidget(self.combo_source)
        
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)
        
        # 3. 实时数据板
        stats_group = QGroupBox("实时数据监控")
        stats_layout = QVBoxLayout()
        
        self.label_count = QLabel("0")
        self.label_count.setFont(QFont('Arial', 48, QFont.Weight.Bold))
        self.label_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_count.setStyleSheet("color: #28a745;") # Green
        stats_layout.addWidget(QLabel("当前计数:"))
        stats_layout.addWidget(self.label_count)
        
        self.label_feedback = QLabel("准备就绪")
        self.label_feedback.setFont(QFont('Droid Sans Fallback', 14))
        self.label_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_feedback.setStyleSheet("color: #dc3545; font-weight: bold;") # Red
        self.label_feedback.setWordWrap(True)
        stats_layout.addWidget(QLabel("AI 纠错指导:"))
        stats_layout.addWidget(self.label_feedback)
        
        stats_group.setLayout(stats_layout)
        left_layout.addWidget(stats_group)

        # 5. 图表区域 (新增)
        self.chart = RealTimeChart(self, width=4, height=3)
        left_layout.addWidget(self.chart)
        
        left_layout.addStretch() # 弹簧占位
        
        # 4. 控制按钮
        btn_settings = QPushButton("设置 (Settings)")
        btn_settings.clicked.connect(self.open_settings)
        left_layout.addWidget(btn_settings)

        main_layout.addWidget(left_panel)

        # --- Right Panel: Video Display ---
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        self.video_label = QLabel(self)
        self.video_label.setStyleSheet("background-color: #000; border-radius: 10px;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        right_layout.addWidget(self.video_label)
        
        main_layout.addWidget(right_panel)

        # --- Video Thread ---
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.update_data_signal.connect(self.update_stats)
        
        # 默认启动
        self.change_source(0) # 默认选中第一个(摄像头)
        # 如果你想默认用视频，可以修改这里逻辑
        # self.thread.start() # 在 change_source 里启动

    def get_video_path(self, index):
        """根据下拉菜单索引返回文件路径"""
        # 使用 get_resource_path 确保打包后能找到资源
        base_dir = get_resource_path(os.path.join("assets", "videos"))
        
        if index == 1: return os.path.join(base_dir, "pushup.mp4")
        if index == 2: return os.path.join(base_dir, "squat.mp4")
        if index == 3: return os.path.join(base_dir, "jumprope.mp4")
        if index == 4: return os.path.join(base_dir, "situp.mp4")
        if index == 5: return os.path.join(base_dir, "pullup.mp4")
        return 0 # Camera

    def change_exercise(self, index):
        if index == 0: ex_type = "pushup"
        elif index == 1: ex_type = "squat"
        elif index == 2: ex_type = "jumprope"
        elif index == 3: ex_type = "situp"
        elif index == 4: ex_type = "pullup"
        self.thread.set_exercise(ex_type)
        print(f"Switched to {ex_type}")

    def change_source(self, index):
        source = self.get_video_path(index)
        
        # 智能切换运动类型 (如果选了视频，自动切到对应的运动类型)
        if index == 1: # PushUp
            self.combo_exercise.setCurrentIndex(0)
        elif index == 2: # Squat
            self.combo_exercise.setCurrentIndex(1)
        elif index == 3: # Jump Rope
            self.combo_exercise.setCurrentIndex(2)
        elif index == 4: # Sit Up
            self.combo_exercise.setCurrentIndex(3)
        elif index == 5: # Pull Up
            self.combo_exercise.setCurrentIndex(4)
            
        self.thread.set_source(source)

    @Slot(QImage)
    def update_image(self, qt_img):
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

    @Slot(int, str, float)
    def update_stats(self, count, feedback, chart_val):
        self.label_count.setText(str(count))
        self.label_feedback.setText(feedback)
        
        # 更新图表
        self.chart.update_chart(chart_val)
        
        # 简单的颜色反馈
        if feedback == "动作标准" or feedback == "节奏不错":
            self.label_feedback.setStyleSheet("color: #28a745; font-weight: bold;")
        elif feedback == "请开始跳跃" or feedback == "准备就绪":
            self.label_feedback.setStyleSheet("color: #ffc107; font-weight: bold;") # Yellow
        else:
            self.label_feedback.setStyleSheet("color: #dc3545; font-weight: bold;")

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Settings saved. Reload exercise to apply new thresholds.
            current_exercise_type = self.thread.exercise_type
            self.thread.set_exercise(current_exercise_type)
            
            # If using camera, restart to apply resolution
            if self.combo_source.currentIndex() == 0:
                self.thread.set_source(0)
            
            print("Settings updated and applied.")

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Droid Sans Fallback", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
