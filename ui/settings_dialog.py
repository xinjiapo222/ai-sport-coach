from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QSpinBox, 
                               QDoubleSpinBox, QSlider, QComboBox, QDialogButtonBox,
                               QTabWidget, QWidget, QLabel)
from PySide6.QtCore import Qt
from utils.config_manager import ConfigManager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置 (Settings)")
        self.resize(500, 400)
        # Bianbu may use a dark system theme. Give this top-level dialog a
        # complete palette instead of relying on inherited application colors.
        self.setStyleSheet("""
            QDialog, QTabWidget::pane, QWidget {
                background-color: #f4f6f8;
                color: #202124;
                font-family: 'Droid Sans Fallback', 'Noto Sans CJK SC', sans-serif;
            }
            QLabel {
                background-color: transparent;
                color: #202124;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #aeb4bb;
                border-radius: 3px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #dfe3e8;
                color: #202124;
                border: 1px solid #aeb4bb;
                padding: 7px 14px;
                min-width: 72px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #0056b3;
                font-weight: bold;
                border-bottom-color: #ffffff;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                color: #202124;
                background-color: #ffffff;
                selection-color: #ffffff;
                selection-background-color: #007bff;
                border: 1px solid #8b929a;
                border-radius: 3px;
                padding: 4px 6px;
                min-height: 22px;
            }
            QComboBox QAbstractItemView {
                color: #202124;
                background-color: #ffffff;
                selection-color: #ffffff;
                selection-background-color: #007bff;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background-color: #c7ccd1;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background-color: #007bff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -5px 0;
                background-color: #ffffff;
                border: 2px solid #007bff;
                border-radius: 8px;
            }
            QPushButton {
                color: #ffffff;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                padding: 7px 12px;
                font-weight: bold;
                min-width: 64px;
            }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:pressed { background-color: #004085; }
        """)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # --- Tab 1: 运动阈值 ---
        self.tab_thresholds = QWidget()
        form_layout = QFormLayout()
        
        # PushUp
        self.spin_pushup_bottom = QSpinBox()
        self.spin_pushup_bottom.setRange(0, 180)
        self.spin_pushup_bottom.setValue(self.config['pushup']['threshold_bottom'])
        form_layout.addRow("俯卧撑-底部角度 (小于):", self.spin_pushup_bottom)
        
        self.spin_pushup_top = QSpinBox()
        self.spin_pushup_top.setRange(0, 180)
        self.spin_pushup_top.setValue(self.config['pushup']['threshold_top'])
        form_layout.addRow("俯卧撑-顶部角度 (大于):", self.spin_pushup_top)
        
        # Squat
        self.spin_squat_down = QSpinBox()
        self.spin_squat_down.setRange(0, 180)
        self.spin_squat_down.setValue(self.config['squat']['threshold_down'])
        form_layout.addRow("深蹲-下蹲角度 (小于):", self.spin_squat_down)
        
        # SitUp
        self.spin_situp_angle = QSpinBox()
        self.spin_situp_angle.setRange(0, 180)
        self.spin_situp_angle.setValue(self.config['situp']['threshold_up_angle'])
        form_layout.addRow("仰卧起坐-起身角度 (小于):", self.spin_situp_angle)
        
        self.spin_situp_ratio = QDoubleSpinBox()
        self.spin_situp_ratio.setRange(0.0, 1.0)
        self.spin_situp_ratio.setSingleStep(0.05)
        self.spin_situp_ratio.setValue(self.config['situp']['threshold_up_ratio'])
        form_layout.addRow("仰卧起坐-起身高度比 (大于):", self.spin_situp_ratio)
        
        # PullUp
        self.spin_pullup_straight = QSpinBox()
        self.spin_pullup_straight.setRange(0, 180)
        self.spin_pullup_straight.setValue(self.config['pullup']['threshold_arm_straight'])
        form_layout.addRow("引体向上-手臂伸直 (大于):", self.spin_pullup_straight)
        
        self.tab_thresholds.setLayout(form_layout)
        self.tabs.addTab(self.tab_thresholds, "运动阈值")
        
        # --- Tab 2: 系统设置 ---
        self.tab_system = QWidget()
        sys_layout = QFormLayout()
        
        # Audio Volume
        self.slider_volume = QSlider(Qt.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(int(self.config['audio']['volume'] * 100))
        sys_layout.addRow("语音音量:", self.slider_volume)
        
        # Camera
        self.combo_resolution = QComboBox()
        self.combo_resolution.addItems(["640x480", "1280x720", "1920x1080"])
        current_res = f"{self.config['camera']['width']}x{self.config['camera']['height']}"
        idx = self.combo_resolution.findText(current_res)
        if idx >= 0: self.combo_resolution.setCurrentIndex(idx)
        sys_layout.addRow("摄像头分辨率:", self.combo_resolution)
        
        self.tab_system.setLayout(sys_layout)
        self.tabs.addTab(self.tab_system, "系统设置")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)

    def save_settings(self):
        # Update config object
        self.config_manager.set("pushup", "threshold_bottom", self.spin_pushup_bottom.value())
        self.config_manager.set("pushup", "threshold_top", self.spin_pushup_top.value())
        
        self.config_manager.set("squat", "threshold_down", self.spin_squat_down.value())
        
        self.config_manager.set("situp", "threshold_up_angle", self.spin_situp_angle.value())
        self.config_manager.set("situp", "threshold_up_ratio", self.spin_situp_ratio.value())
        
        self.config_manager.set("pullup", "threshold_arm_straight", self.spin_pullup_straight.value())
        
        self.config_manager.set("audio", "volume", self.slider_volume.value() / 100.0)
        
        res_text = self.combo_resolution.currentText()
        w, h = map(int, res_text.split('x'))
        self.config_manager.set("camera", "width", w)
        self.config_manager.set("camera", "height", h)
        
        self.config_manager.save_config()
        self.accept()
