from pack.libs.module.gui.QtPack import *
import os

class SegoeIcons:
    font_db = QFontDatabase()
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "SegoeIcons.ttf")
    if os.path.exists(font_path):
        font_id = font_db.addApplicationFont(font_path)
        if font_id != -1:
            families = font_db.applicationFontFamilies(font_id)
            if families:
                font = QFont(families[0], 11)
            else:
                font = QFont("Segoe Icons", 11)
        else:
            font = QFont("Segoe Icons", 11)
    else:
        font = QFont("Segoe Icons", 11)

    @classmethod
    def get_font(cls, font_size: int = 11):
        """获取指定大小的 Segoe Icons 字体"""
        base_font = cls.font
        return QFont(base_font.family(), font_size)