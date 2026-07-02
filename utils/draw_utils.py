import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from functools import lru_cache


@lru_cache(maxsize=16)
def _load_font(size):
    candidates = [
        os.environ.get("AI_SPORT_FONT", ""),
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for font_path in candidates:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

def put_chinese_text(img, text, position, color=(0, 255, 0), size=30):
    """
    在 OpenCV 图片上绘制中文
    :param img: OpenCV 图片 (BGR)
    :param text: 要绘制的文字
    :param position: (x, y) 坐标
    :param color: (b, g, r) 颜色
    :param size: 字体大小
    :return: 绘制后的 OpenCV 图片
    """
    if (isinstance(img, np.ndarray)):
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # 字体对象创建成本较高，按字号缓存，并优先使用 Linux 的中文字体。
        font = _load_font(size)
            
        # PIL 的颜色是 RGB，OpenCV 是 BGR，所以传入的 color 需要对应
        # cv2 传入的是 (B, G, R)，这里 PIL 需要 (R, G, B)
        rgb_color = (color[2], color[1], color[0])
        
        draw.text(position, text, font=font, fill=rgb_color)
        
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    
    return img
