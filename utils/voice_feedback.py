import subprocess
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
import threading
import time
import queue
from utils.config_manager import ConfigManager

class VoiceAssistant:
    def __init__(self):
        self.last_speak_time = 0
        self.min_interval = 3.0 # 最短说话间隔(秒)
        self.message_queue = queue.Queue()
        
        # 启动守护线程处理语音
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def speak(self, text, force=False):
        """
        将语音任务加入队列
        """
        current_time = time.time()
        
        # 过滤数字计数，避免限制
        is_count = text.isdigit()
        
        if not is_count and not force:
            if current_time - self.last_speak_time < self.min_interval:
                return

        self.last_speak_time = current_time
        self.message_queue.put(text)

    def _process_queue(self):
        """
        独立线程：初始化 COM 并处理语音队列
        """
        try:
            if pyttsx3 is None:
                while True:
                    text = self.message_queue.get()
                    if text is None:
                        break
                    try:
                        subprocess.run(
                            ["espeak-ng", "-v", "cmn", "-s", "180", text],
                            check=False,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    finally:
                        self.message_queue.task_done()
                return
            # 在当前线程初始化 engine (COM 线程安全要求)
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            
            while True:
                text = self.message_queue.get()
                if text is None:
                    break
                
                try:
                    # Update volume from config
                    vol = ConfigManager().config['audio']['volume']
                    engine.setProperty('volume', vol)
                    
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"Speech error: {e}")
                
                self.message_queue.task_done()
        except Exception as e:
            print(f"Voice engine init failed: {e}")
