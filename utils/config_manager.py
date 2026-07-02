import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "pushup": {
        "threshold_bottom": 110,
        "threshold_top": 150
    },
    "squat": {
        "threshold_down": 100,
        "threshold_up": 160
    },
    "situp": {
        "threshold_up_angle": 90,
        "threshold_up_ratio": 0.4
    },
    "pullup": {
        "threshold_arm_straight": 145,
        "threshold_arm_flex": 85
    },
    "camera": {
        "id": 0,
        "width": 1280,
        "height": 720
    },
    "audio": {
        "volume": 1.0
    }
}

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = DEFAULT_CONFIG.copy()
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self._merge_config(self.config, data)
            except Exception as e:
                print(f"Error loading config: {e}")

    def _merge_config(self, current, new_data):
        for key, value in new_data.items():
            if key in current and isinstance(current[key], dict) and isinstance(value, dict):
                self._merge_config(current[key], value)
            elif key in current:
                current[key] = value

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, section, key):
        return self.config.get(section, {}).get(key)

    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
