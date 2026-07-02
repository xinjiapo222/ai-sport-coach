import sys
import os

def get_resource_path(relative_path):
    """ 
    获取资源的绝对路径
    兼容开发环境 (直接运行) 和 PyInstaller 打包环境 (解压到 _MEIPASS)
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境当前目录
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
