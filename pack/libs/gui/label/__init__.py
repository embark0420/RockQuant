from pack.libs.gui.QtPack import *

class Label(QLabel):
    def __init__(self, text: str = "", parent: QWidget = None, font_size: int = 11, 
                 text_alignment: Qt.AlignmentFlag = Qt.AlignLeft):
        super().__init__(text, parent)
        self.font_size = font_size
        self.text_alignment = text_alignment

        self.setAlignment(self.text_alignment)
        self.update_colors()
        QApplication.instance().paletteChanged.connect(self.update_colors)
    
    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128
        text_color = "#ffffff" if is_dark else "#000000"
        
        # 🔥 使用 !important 强制覆盖父控件样式
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color} !important;
                font-size: {self.font_size}px !important;
                border-radius: 0px !important;
                background: transparent !important;
            }}
        """)
class LabelWidget(QPushButton):
    def __init__(self, text: str = '', parent=None, border_radius: int = 3,alpha : int = 255,text_alignment:str="left", font_size : int = 11):
        super().__init__(text, parent)
        self.alpha = alpha
        self.font_size = font_size
        self.text_alignment = text_alignment
        self.animation_value = 0
        self.pressed_animation_value = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        self.hovered = False
        self.pressed_state = False
        QApplication.instance().paletteChanged.connect(self.update_colors)
        self.update_colors()
        self.border_radius = border_radius

    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128

        if is_dark:
            self.start_color = QColor(39, 39, 39, self.alpha)  # 半透明黑色
            self.end_color = QColor(65, 65, 65, self.alpha)    # 半透明深灰色
            self.border_color = QColor(57, 57, 57, self.alpha)  # 半透明边框颜色
            self.end_border_color = QColor(68, 68, 68, self.alpha)  # 半透明边框颜色
            self.pressed_color = QColor(35, 35, 35, self.alpha)  # 半透明按下颜色
        else:
            self.start_color = QColor(255, 255, 255, self.alpha)  # 半透明白色
            self.end_color = QColor(222, 222, 222, self.alpha)  # 半透明浅灰色
            self.border_color = QColor(173, 173, 173, self.alpha)  # 半透明边框颜色
            self.end_border_color = QColor(222, 222, 222, self.alpha)  # 半透明边框颜色
            self.pressed_color = QColor(70, 169, 255, self.alpha)  # 半透明按下颜色

    def enterEvent(self, event):
        self.hovered = False
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        super().leaveEvent(event)

    def setOpacity(self, Opacity_num: float):
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(Opacity_num)
        self.setGraphicsEffect(effect)

    def update_animation(self):
        if self.pressed_state and self.pressed_animation_value < 1:
            self.pressed_animation_value += 0.08
            if self.pressed_animation_value > 1:
                self.pressed_animation_value = 1
        elif not self.pressed_state and self.pressed_animation_value > 0:
            self.pressed_animation_value -= 0.08
            if self.pressed_animation_value < 0:
                self.pressed_animation_value = 0

        if self.hovered and self.animation_value < 1:
            self.animation_value += 0.05
            if self.animation_value > 1:
                self.animation_value = 1
        elif not self.hovered and self.animation_value > 0:
            self.animation_value -= 0.05
            if self.animation_value < 0:
                self.animation_value = 0

        # 计算基础颜色（悬停效果）
        base_color = QColor(
            self.start_color.red() + int((self.end_color.red() - self.start_color.red()) * self.animation_value),
            self.start_color.green() + int((self.end_color.green() - self.start_color.green()) * self.animation_value),
            self.start_color.blue() + int((self.end_color.blue() - self.start_color.blue()) * self.animation_value),
            self.start_color.alpha()  # 保持透明度不变
        )

        # 计算当前颜色（按下效果）
        current_color = QColor(
            base_color.red() + int((self.pressed_color.red() - base_color.red()) * self.pressed_animation_value),
            base_color.green() + int((self.pressed_color.green() - base_color.green()) * self.pressed_animation_value),
            base_color.blue() + int((self.pressed_color.blue() - base_color.blue()) * self.pressed_animation_value),
            base_color.alpha()  # 保持透明度不变
        )

        # 计算边框颜色
        border_color = QColor(
            self.border_color.red() + int((self.end_border_color.red() - self.border_color.red()) * self.animation_value),
            self.border_color.green() + int((self.end_border_color.green() - self.border_color.green()) * self.animation_value),
            self.border_color.blue() + int((self.end_border_color.blue() - self.border_color.blue()) * self.animation_value),
            self.border_color.alpha()  # 保持透明度不变
        )

        # 动态修改样式表，同时设置背景颜色和边框样式
        style = f"background-color: rgba({current_color.red()}, {current_color.green()}, {current_color.blue()}, {current_color.alpha()});" \
                f"border-color : rgba({border_color.red()}, {border_color.green()}, {border_color.blue()}, {border_color.alpha()});" \
                f"border-style: solid; border-width: 1px; border-radius: {self.border_radius}px;text-align: {self.text_alignment};font-size:{self.font_size}"

        self.setStyleSheet(style)