from pack.libs.gui.QtPack import *

class ToggleSwitchButton(QWidget):
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None, width=40, height=20):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setMouseTracking(True)  # 必须开启才能捕获悬浮

        # 开关状态
        self._is_checked = False
        self._padding = 3
        self._circle_x = self._padding

        # 滑块滑动动画
        self._slide_anim = QPropertyAnimation(self, b"circlePosition")
        self._slide_anim.setDuration(350)
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutExpo)

        # 背景颜色（完全沿用你按钮的风格）
        self._bg_color = QColor()
        self._default_color = QColor()
        self._hover_color = QColor()
        self._pressed_color = QColor()
        self._checked_color = QColor()
        self._checked_hover = QColor()
        self._checked_pressed = QColor()

        # 颜色渐变动画
        self._color_anim = QPropertyAnimation(self, b"bgColor")
        self._color_anim.setDuration(400)
        self._color_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        QApplication.instance().paletteChanged.connect(self.update_colors)
        self.update_colors()
    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128

        if is_dark:
            # 深色模式
            self._default_color = QColor("#494949")
            self._hover_color = QColor("#3F3F3F")
            self._pressed_color = QColor("#313131")
            self._checked_color = QColor("#108cff")
            self._checked_hover = QColor("#40a3ff")
            self._checked_pressed = QColor("#0084ff")
        else:
            # 浅色模式
            self._default_color = QColor("#E5E5E5")
            self._hover_color = QColor("#d1d1d1")
            self._pressed_color = QColor("#adadad")
            self._checked_color = QColor("#1990ff")
            self._checked_hover = QColor("#40a3ff")
            self._checked_pressed = QColor("#0787ff")

        self._bg_color = self._checked_color if self._is_checked else self._default_color
        self.update()

    def isChecked(self):
        return self._is_checked

    def setChecked(self, checked: bool):
        if self._is_checked == checked:
            return
        self._is_checked = checked
        self._slide_animation()
        self._animate_to_state_color()
        self.stateChanged.emit(self._is_checked)

    def toggle(self):
        self.setChecked(not self._is_checked)

    # --------------------- 动画 ---------------------
    def _slide_animation(self):
        end_x = self._padding if not self._is_checked else self.width() - self.height() + self._padding
        self._slide_anim.stop()
        self._slide_anim.setStartValue(self._circle_x)
        self._slide_anim.setEndValue(end_x)
        self._slide_anim.start()

    def _animate_color(self, target):
        self._color_anim.stop()
        self._color_anim.setStartValue(self._bg_color)
        self._color_anim.setEndValue(target)
        self._color_anim.start()

    def _animate_to_state_color(self):
        target = self._checked_color if self._is_checked else self._default_color
        self._animate_color(target)

    # --------------------- 绘制 ---------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        painter.setBrush(QBrush(self._bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, rect.height() // 2, rect.height() // 2)

        circle_size = self.height() - self._padding * 2
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(QPen(QColor("#D0D0D0"), 1))
        painter.drawEllipse(int(self._circle_x), self._padding, circle_size, circle_size)

    # --------------------- 鼠标交互 ---------------------
    def enterEvent(self, event):
        if self._is_checked:
            self._animate_color(self._checked_hover)
        else:
            self._animate_color(self._hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_to_state_color()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._is_checked:
                self._animate_color(self._checked_pressed)
            else:
                self._animate_color(self._pressed_color)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
        super().mouseReleaseEvent(event)

    def showEvent(self, event):
        self.update_colors()
        super().showEvent(event)

    # --------------------- 属性动画 ---------------------
    def get_circle_pos(self):
        return self._circle_x

    def set_circle_pos(self, x):
        self._circle_x = x
        self.update()

    circlePosition = pyqtProperty(int, get_circle_pos, set_circle_pos)

    def get_bg_color(self):
        return self._bg_color

    def set_bg_color(self, color):
        self._bg_color = color
        self.update()

    bgColor = pyqtProperty(QColor, get_bg_color, set_bg_color)