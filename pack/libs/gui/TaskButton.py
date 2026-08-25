from pack.libs.gui.QtPack import *
from pack.libs.gui.ReadConfigFile import *
import re

class TaskButton(QPushButton):
    PressEvent = pyqtSignal(bool)
    ReleaseEvent = pyqtSignal(bool)
    
    def __init__(self, text="", parent=None, border_radius: int = 3, border_width: int = 1, 
                 text_alignment: str = "center", transparent: int = 255,font_size : int = 12):
        super().__init__(text, parent)
        self.border_width = border_width
        self.border_radius = border_radius
        self.text_alignment = text_alignment
        self.font_size = font_size
        self._transparent = max(0, min(255, transparent))
        
        self._hover_alpha = 0
        self._pressed_alpha = 0
        self._is_hover = False
        self._is_pressed = False
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        self.update_colors()
        QApplication.instance().paletteChanged.connect(self.update_colors)
        
        self._alpha_animation = QPropertyAnimation(self, b"hoverAlpha")
        self._alpha_animation.setDuration(200)
        self._alpha_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128
        self.setStyleSheet(f"font-size : {self.font_size};")
        if is_dark:
            self._text_color = QColor("#FFFFFF")
        else:
            self._text_color = QColor("#4B4B4B")
    
    def get_hover_alpha(self):
        return self._hover_alpha
    
    def set_hover_alpha(self, value):
        self._hover_alpha = value
        self.update()
    
    hoverAlpha = pyqtProperty(float, get_hover_alpha, set_hover_alpha)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self.border_radius, self.border_radius)
        
        if self._is_pressed:
            alpha = 60
        elif self._is_hover:
            alpha = self._hover_alpha
        else:
            alpha = 0
        
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128
        
        if is_dark:
            bg_color = QColor(255, 255, 255, int(alpha))
        else:
            bg_color = QColor(0, 0, 0, int(alpha))
        
        painter.fillPath(path, bg_color)
        
        painter.setPen(self._text_color)
        
        if self.text_alignment == "left":
            alignment_flag = Qt.AlignLeft | Qt.AlignVCenter
            text_rect = rect.adjusted(10, 0, -10, 0)
        elif self.text_alignment == "right":
            alignment_flag = Qt.AlignRight | Qt.AlignVCenter
            text_rect = rect.adjusted(10, 0, -10, 0)
        else:
            alignment_flag = Qt.AlignCenter
            text_rect = rect
        
        painter.drawText(text_rect, alignment_flag, self.text())
        
        painter.end()
    
    def enterEvent(self, event):
        self._is_hover = True
        self._alpha_animation.stop()
        self._alpha_animation.setStartValue(self._hover_alpha)
        self._alpha_animation.setEndValue(30)
        self._alpha_animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._is_hover = False
        self._alpha_animation.stop()
        self._alpha_animation.setStartValue(self._hover_alpha)
        self._alpha_animation.setEndValue(0)
        self._alpha_animation.start()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_pressed = True
            self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.ReleaseEvent.emit(False)
        if event.button() == Qt.LeftButton:
            self._is_pressed = False
            if self.underMouse():
                self._is_hover = True
                self._alpha_animation.stop()
                self._alpha_animation.setStartValue(self._hover_alpha)
                self._alpha_animation.setEndValue(30)
                self._alpha_animation.start()
            else:
                self._is_hover = False
                self.update()
        super().mouseReleaseEvent(event)
    
    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        if not enabled:
            self._is_hover = False
            self._is_pressed = False
            self._hover_alpha = 0
            self.update()