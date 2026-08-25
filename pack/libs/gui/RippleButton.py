from pack.libs.gui.QtPack import *
from pack.libs.gui.button import *
from pack.libs.gui.shadow import *
from pack.libs.gui.widget import PopupWidget
from pack.libs.gui.QtPack import *
from pack.libs.gui.ReadConfigFile import *
import re

Dark_Theme = (read_config_value("Theme_Dark","button_theme_color"))
Dark_Theme_hover = (read_config_value("Theme_Dark","button_theme_hover_color"))
Dark_Theme_press = (read_config_value("Theme_Dark","button_theme_pressed_color"))

Light_Theme = (read_config_value("Theme_Light","button_theme_color"))
Light_Theme_hover = (read_config_value("Theme_Light","button_theme_hover_color"))
Light_Theme_press = (read_config_value("Theme_Light","button_theme_pressed_color"))
class RippleButton(QPushButton):
    presseds = pyqtSignal(object)
    clicked_with_data = pyqtSignal(object)
    def __init__(self, text="", parent=None,
                 border_width: int = 0, corner_radius: int = 3,
                 text_align = Qt.AlignCenter,text_color = Qt.white):
        
        super().__init__(text, parent)
        self.text_align = text_align
        self._text_color = text_color
        self.ripples = []
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.border_width = border_width
        self.hovered = False
        self.pressed = False
        self.animation_value = 0
        self.press_animation = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        self.corner_radius = corner_radius
        
        # 初始更新颜色
        self.update_colors()
        # 监听系统主题变化，自动刷新颜色
        QApplication.instance().paletteChanged.connect(self._on_palette_changed)
    
    def _on_palette_changed(self, palette):
        """系统调色板改变时刷新颜色"""
        self.update_colors()
        self.update()
    def _emit_clicked(self):
        self.clicked_with_data.emit(self._data)
    
    @property
    def data(self):
        return self._data
    
    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128

        if is_dark:
            self.text_color = self._text_color
            self.hover_border = QColor(re.findall(r'border_color:(.+?);',Dark_Theme_hover)[0])
            self.start_color = QColor(0,0,0,0)  # 半透明黑色
            self.hover_color = QColor(re.findall(r'button_color:(.+?);',Dark_Theme_hover)[0])  # 半透明深灰色
            self.press_color = QColor(re.findall(r'button_color:(.+?);',Dark_Theme_press)[0])  # 半透明灰色
            # 涟漪色：读取 button_theme_pressed_color 的 button_color
            press_btn_color = QColor(re.findall(r'button_color:(.+?);',Dark_Theme_press)[0])
            self.ripple_center = QColor(
                min(press_btn_color.red() + 80, 255),
                min(press_btn_color.green() + 80, 255),
                min(press_btn_color.blue() + 80, 255),
                128
            )
            self.ripple_outer = QColor(press_btn_color.red(), press_btn_color.green(), press_btn_color.blue(), 1)
        else:
            self.text_color = self._text_color
            self.hover_border = QColor(re.findall(r'border_color:(.+?);',Light_Theme_hover)[0])
            self.start_color = QColor(0,0,0,0)  # 半透明黑色
            self.hover_color = QColor(re.findall(r'button_color:(.+?);',Light_Theme_hover)[0])  # 半透明深灰色
            self.press_color = QColor(re.findall(r'button_color:(.+?);',Light_Theme_press)[0])  # 半透明灰色
            # 涟漪色：读取 button_theme_pressed_color 的 button_color
            press_btn_color = QColor(re.findall(r'button_color:(.+?);',Light_Theme_press)[0])
            self.ripple_center = QColor(
                max(press_btn_color.red() - 40, 0),
                max(press_btn_color.green() - 40, 0),
                max(press_btn_color.blue() - 40, 0),
                128
            )
            self.ripple_outer = QColor(press_btn_color.red(), press_btn_color.green(), press_btn_color.blue(), 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressed = True
            self.presseds.emit(True)
            pos = event.localPos()
            self.ripples.append({"pos": pos, "radius": 0, "opacity": 1})
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressed = False
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        super().leaveEvent(event)

    def update_animation(self):
        if self.hovered and self.animation_value < 1:
            self.animation_value += 0.1
            if self.animation_value > 1:
                self.animation_value = 1
        elif not self.hovered and self.animation_value > 0:
            self.animation_value -= 0.1
            if self.animation_value < 0:
                self.animation_value = 0

        new_ripples = []
        for ripple in self.ripples:
            ripple["radius"] += self.width()//10
            if not self.pressed:
                ripple["opacity"] -= 0.03
            if ripple["opacity"] > 0:
                new_ripples.append(ripple)
        self.ripples = new_ripples
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 创建裁剪区域（圆角矩形）
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(self.rect()), self.corner_radius, self.corner_radius)
        painter.setClipPath(clip_path)

        base_bg_color = QColor(
            self.start_color.red() + int((self.hover_color.red() - self.start_color.red()) * self.animation_value),
            self.start_color.green() + int((self.hover_color.green() - self.start_color.green()) * self.animation_value),
            self.start_color.blue() + int((self.hover_color.blue() - self.start_color.blue()) * self.animation_value),
            self.start_color.alpha()  # 保持透明度不变
        )

        final_bg_color = QColor(
            base_bg_color.red() + int((self.press_color.red() - base_bg_color.red()) * self.press_animation),
            base_bg_color.green() + int((self.press_color.green() - base_bg_color.green()) * self.press_animation),
            base_bg_color.blue() + int((self.press_color.blue() - base_bg_color.blue()) * self.press_animation),
            base_bg_color.alpha()  # 保持透明度不变
        )
        # 绘制背景
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.corner_radius, self.corner_radius)
        painter.fillPath(path, final_bg_color)

        # 绘制边框（不应用裁剪，确保边框完整显示）
        painter.save()
        painter.setClipRect(self.rect())  # 重置裁剪区域为整个按钮
        if self.border_width > 0:
            painter.setPen(QPen(self.hover_border, int(self.border_width)))
            painter.drawRoundedRect(self.rect(), self.corner_radius, self.corner_radius)
        painter.restore()

        # 绘制光源效果（涟漪效果）—— 颜色取自 config.toml button_theme_pressed_color
        for ripple in self.ripples:
            gradient = QRadialGradient(
                ripple["pos"],
                ripple["radius"],
                ripple["pos"]
            )
            center_alpha = int(ripple["opacity"] * self.ripple_center.alpha())
            center_color = QColor(
                self.ripple_center.red(),
                self.ripple_center.green(),
                self.ripple_center.blue(),
                center_alpha
            )
            gradient.setColorAt(0, center_color)
            gradient.setColorAt(1, self.ripple_outer)

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(ripple["pos"].toPoint(), int(ripple["radius"]), int(ripple["radius"]))

        # 绘制按钮文本
        painter.setPen(self.text_color)
        painter.drawText(self.rect(), self.text_align, self.text())
