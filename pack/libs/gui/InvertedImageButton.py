from pack.libs.gui.QtPack import *
from pack.libs.gui.TaskButton import *
from pack.libs.gui.RippleButton import *
from pack.libs.gui.ReadConfigFile import *
import re
from PIL import Image
import numpy as np
import os
class InvertedImageButton(QPushButton):
    """带反色开关的图片按钮 - 图片在上方，文字在下方"""
    
    PressEvent = pyqtSignal(bool)
    ReleaseEvent = pyqtSignal(bool)
    InvertedChanged = pyqtSignal(bool)
    
    def __init__(self, image_path="", text="", parent=None, border_radius: int = 5, border_width: int = 1,
                 transparent: int = 255, invert_on_hover: bool = False):
        super().__init__(text, parent)
        self.border_width = border_width
        self.border_radius = border_radius
        self._transparent = max(0, min(255, transparent))
        self.invert_on_hover = invert_on_hover
        self._inverted_enabled = False
        self._is_hover = False
        self._is_pressed = False
        
        self.original_pixmap = QPixmap()
        self.inverted_pixmap = QPixmap()
        self.image_path = image_path
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        if image_path and os.path.exists(image_path):
            self.load_image(image_path)
        elif image_path:
            print(f"Warning: Image file not found: {image_path}")
        
        self.update_colors()
        QApplication.instance().paletteChanged.connect(self.update_colors)
    
    def load_image(self, image_path: str):
        """加载图片"""
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            return False
        
        self.image_path = image_path
        self.original_pixmap = QPixmap(image_path)
        
        if self.original_pixmap.isNull():
            print(f"Error: Failed to load image: {image_path}")
            return False
        
        self.inverted_pixmap = self.create_inverted_pixmap(self.original_pixmap)
        self.update()
        return True
    
    def create_inverted_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """创建反色图片"""
        if pixmap.isNull():
            return QPixmap()
        
        image = pixmap.toImage()
        if image.isNull():
            return QPixmap()
        
        image.invertPixels()
        return QPixmap.fromImage(image)
    
    def set_inverted_enabled(self, enabled: bool):
        """设置反色开关状态"""
        if self._inverted_enabled == enabled:
            return
        
        self._inverted_enabled = enabled
        self.update()
        self.InvertedChanged.emit(enabled)
    
    def is_inverted_enabled(self) -> bool:
        """获取反色开关状态"""
        return self._inverted_enabled
    
    def toggle_inverted(self):
        """切换反色开关"""
        self.set_inverted_enabled(not self._inverted_enabled)
    
    def get_current_pixmap(self) -> QPixmap:
        """获取当前显示的图片"""
        if self._inverted_enabled:
            return self.inverted_pixmap if not self.inverted_pixmap.isNull() else self.original_pixmap
        else:
            return self.original_pixmap
    
    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128
        
        if is_dark:
            self._text_color = QColor("#FFFFFF")
        else:
            self._text_color = QColor("#000000")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(self.rect())
        width = rect.width()
        height = rect.height()
        
        path = QPainterPath()
        path.addRoundedRect(rect, self.border_radius, self.border_radius)
        
        if self._is_pressed:
            alpha = 60
        elif self._is_hover:
            alpha = 30
        else:
            alpha = 0
        
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128
        
        if is_dark:
            bg_color = QColor(255, 255, 255, alpha)
        else:
            bg_color = QColor(0, 0, 0, alpha)
        
        painter.fillPath(path, bg_color)
        
        current_pixmap = self.get_current_pixmap()
        
        if current_pixmap and not current_pixmap.isNull():
            img_size = current_pixmap.size()
            
            max_image_height = height - 40 if self.text() and self.text() != "" else height - 20
            max_image_width = width - 20
            
            if img_size.height() > max_image_height:
                scaled_height = max_image_height
                scaled_width = int(img_size.width() * scaled_height / img_size.height())
            else:
                scaled_height = img_size.height()
                scaled_width = img_size.width()
            
            if scaled_width > max_image_width:
                scaled_width = max_image_width
                scaled_height = int(img_size.height() * scaled_width / img_size.width())
            
            scaled_pixmap = current_pixmap.scaled(
                scaled_width, scaled_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            image_x = (width - scaled_pixmap.width()) // 2
            
            if self.text() and self.text() != "":
                image_y = (height - scaled_pixmap.height() - 25) // 2
            else:
                image_y = (height - scaled_pixmap.height()) // 2
            
            painter.drawPixmap(image_x, image_y, scaled_pixmap)
        
        if self.text() and self.text() != "":
            painter.setPen(self._text_color)
            
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            
            text_rect = QRect(5, height - 22, width - 10, 18)
            
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())
        
        painter.end()
    
    def enterEvent(self, event):
        self._is_hover = True
        if self.invert_on_hover and not self._inverted_enabled:
            self.update()
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._is_hover = False
        if self.invert_on_hover and not self._inverted_enabled:
            self.update()
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.ReleaseEvent.emit(False)
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = False
            if self.underMouse():
                self._is_hover = True
            else:
                self._is_hover = False
            self.update()
        super().mouseReleaseEvent(event)
    
    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        if not enabled:
            self._is_hover = False
            self._is_pressed = False
            self.update()
    
    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)


class TaskButtonWithIcon(QPushButton):
    """带图标的任务栏按钮，支持水波涟漪动画和任务栏内拖动"""
    
    PressEvent = pyqtSignal(bool)
    ReleaseEvent = pyqtSignal(bool)
    
    def __init__(self, text="", image_path="", parent=None, border_radius: int = 3, 
                 border_width: int = 0, invert_on_hover: bool = False):
        super().__init__(text, parent)
        self.border_radius = border_radius
        self.border_width = border_width
        self.invert_on_hover = invert_on_hover
        self._inverted_enabled = False
        self._is_hover = False
        self._is_pressed = False
        self._is_dragging = False
        self._drag_start_pos = None
        self._drag_index = -1
        self._has_focus = False
        self._original_width = -1
        self._is_animating_width = False
        self._state = 'normal'
        self._max_width = 150
        self._min_width = 60
        
        self.original_pixmap = QPixmap()
        self.inverted_pixmap = QPixmap()
        self.image_path = image_path
        self.icon_size = 20
        
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self._ripple_center = QPoint(0, 0)
        self._ripple_animation = None
        
        self._bg_color = QColor()
        self._text_color = QColor()
        self._theme_colors = {'normal': None, 'hover': None, 'pressed': None}
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        if image_path and os.path.exists(image_path):
            self.load_image(image_path)
        elif image_path:
            print(f"Warning: Image file not found: {image_path}")
        
        self.update_colors()
        QApplication.instance().paletteChanged.connect(self.update_colors)
        
        self._fade_opacity = 1.0
        self._fade_animation = QPropertyAnimation(self, b"fadeOpacity")
        self._fade_animation.setDuration(300)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self._width_animation = QPropertyAnimation(self, b"animatableWidth")
        self._width_animation.setDuration(200)
        self._width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self._color_animation = QPropertyAnimation(self, b"bgColor")
        self._color_animation.setDuration(200)
        self._color_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.setFixedWidth(self._min_width)
    
    def set_text(self, text: str):
        """设置文本并自动调整宽度"""
        super().setText(text)
        self._update_width()
    
    def _update_width(self):
        """根据文本内容自动更新宽度"""
        font_metrics = QFontMetrics(self.font())
        text_width = font_metrics.horizontalAdvance(self.text())
        icon_width = self.icon_size if not self.original_pixmap.isNull() else 0
        padding = 32
        new_width = min(self._max_width, max(self._min_width, text_width + icon_width + padding))
        self.setFixedWidth(new_width)
    
    def _is_dark_mode(self) -> bool:
        """检测当前是否为深色模式"""
        palette = QApplication.palette()
        return palette.window().color().lightness() < 128
    
    def update_colors(self):
        """更新颜色方案"""
        is_dark = self._is_dark_mode()
        
        if is_dark:
            # 深色模式颜色 - 透明蒙点白
            self._theme_colors = {
                'normal': QColor(0, 0, 0, 0),
                'hover': QColor(255, 255, 255, 30),
                'pressed': QColor(255, 255, 255, 50)
            }
            self._text_color = QColor("#FFFFFF")
        else:
            # 浅色模式颜色 - 透明蒙点黑
            self._theme_colors = {
                'normal': QColor(0, 0, 0, 0),
                'hover': QColor(0, 0, 0, 20),
                'pressed': QColor(0, 0, 0, 40)
            }
            self._text_color = QColor("#000000")
        
        self._apply_state_colors('normal')
        self._update_width()
    
    def _apply_state_colors(self, state: str):
        """应用指定状态的颜色"""
        self._state = state
        if state in self._theme_colors:
            self._bg_color = QColor(self._theme_colors[state])
    
    def get_bg_color(self):
        return self._bg_color
    
    def set_bg_color(self, color):
        self._bg_color = color
        self.update()
    
    bgColor = pyqtProperty(QColor, get_bg_color, set_bg_color)
    
    def get_animatable_width(self):
        return self.width()
    
    def set_animatable_width(self, value):
        if value <= 0:
            self.setVisible(False)
        self.setFixedWidth(value)
    
    animatableWidth = pyqtProperty(int, get_animatable_width, set_animatable_width)
    
    def set_focus_state(self, has_focus):
        """设置焦点状态 - 透明蒙点淡蓝"""
        if self._has_focus == has_focus:
            return
        self._has_focus = has_focus
        if has_focus:
            self._animate_color(QColor(100, 150, 255, 40))
        else:
            self._animate_color(self._theme_colors.get(self._state, self._theme_colors['normal']))
        self.update()
    
    def get_fade_opacity(self):
        return self._fade_opacity
    
    def set_fade_opacity(self, value):
        self._fade_opacity = value
        self.update()
    
    fadeOpacity = pyqtProperty(float, get_fade_opacity, set_fade_opacity)
    
    def get_ripple_radius(self):
        return self._ripple_radius
    
    def set_ripple_radius(self, value):
        self._ripple_radius = value
        self.update()
    
    rippleRadius = pyqtProperty(float, get_ripple_radius, set_ripple_radius)
    
    def load_image(self, image_path: str, icon_size: int = 20):
        """加载图片"""
        self.icon_size = icon_size
        # 兼容 pathlib.Path 等路径对象，QPixmap 只接受 str
        image_path = str(image_path)
        self.image_path = image_path
        
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            return False
        
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Error: Failed to load image: {image_path}")
            return False
        
        self.original_pixmap = pixmap.scaled(icon_size, icon_size,
                                              Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
        self.inverted_pixmap = self.create_inverted_pixmap(self.original_pixmap)
        
        self._update_width()
        self.update()
        return True
    
    def create_inverted_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """创建反色图片"""
        if pixmap.isNull():
            return QPixmap()
        image = pixmap.toImage()
        image.invertPixels()
        return QPixmap.fromImage(image)
    
    def set_inverted_enabled(self, enabled: bool):
        """设置反色开关状态"""
        self._inverted_enabled = enabled
        self.update()
    
    def toggle_inverted(self):
        """切换反色开关"""
        self.set_inverted_enabled(not self._inverted_enabled)
    
    def get_current_pixmap(self) -> QPixmap:
        """获取当前显示的图片"""
        if self._inverted_enabled:
            return self.inverted_pixmap if not self.inverted_pixmap.isNull() else self.original_pixmap
        elif self.invert_on_hover and self._is_hover and not self._inverted_enabled:
            return self.inverted_pixmap if not self.inverted_pixmap.isNull() else self.original_pixmap
        else:
            return self.original_pixmap
    
    def get_scaled_icon(self) -> QPixmap:
        """获取缩放后的图标"""
        current_pixmap = self.get_current_pixmap()
        if current_pixmap.isNull():
            return QPixmap()
        
        icon_height = self.height() - 8
        if icon_height < 16:
            icon_height = 16
        
        if current_pixmap.height() > icon_height:
            scaled_height = icon_height
            scaled_width = int(current_pixmap.width() * scaled_height / current_pixmap.height())
        else:
            scaled_width = current_pixmap.width()
            scaled_height = current_pixmap.height()
        
        if scaled_width > self.width() * 0.3:
            scaled_width = int(self.width() * 0.3)
            scaled_height = int(current_pixmap.height() * scaled_width / current_pixmap.width())
        
        return current_pixmap.scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    def _animate_color(self, target_color):
        """颜色动画"""
        self._color_animation.stop()
        self._color_animation.setStartValue(self._bg_color)
        self._color_animation.setEndValue(target_color)
        self._color_animation.start()
    
    def animate_ripple(self, pos: QPoint):
        """播放水波涟漪动画"""
        self._ripple_center = pos
        self._ripple_radius = 0
        self._ripple_opacity = 0.4
        
        if self._ripple_animation:
            self._ripple_animation.stop()
        
        self._ripple_animation = QPropertyAnimation(self, b"rippleRadius")
        self._ripple_animation.setDuration(400)
        self._ripple_animation.setStartValue(0)
        self._ripple_animation.setEndValue(max(self.width(), self.height()))
        self._ripple_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        def on_finished():
            self._ripple_opacity = 0
            self.update()
        
        self._ripple_animation.finished.connect(on_finished)
        self._ripple_animation.start()
    
    def animate_fade_in(self):
        """淡入动画（从下方水波涟漪效果）"""
        self.set_fade_opacity(0.0)
        self.setVisible(True)
        
        self._fade_animation.stop()
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.start()
        
        center = QPoint(self.width() // 2, self.height() - 5)
        self.animate_ripple(center)
    
    def animate_fade_out(self, callback=None):
        """淡出动画"""
        self._fade_animation.stop()
        self._fade_animation.setStartValue(self._fade_opacity)
        self._fade_animation.setEndValue(0.0)
        
        if callback:
            self._fade_animation.finished.connect(callback)
        
        self._fade_animation.start()
    
    def animate_width_to_zero(self, callback=None):
        """宽度收缩到0的动画"""
        if self._is_animating_width:
            return
        
        self._is_animating_width = True
        self._original_width = self.width()
        
        self._width_animation.stop()
        self._width_animation.setStartValue(self._original_width)
        self._width_animation.setEndValue(0)
        
        def on_finished():
            self._is_animating_width = False
            if callback:
                callback()
        
        self._width_animation.finished.connect(on_finished)
        self._width_animation.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self.border_radius, self.border_radius)
        
        painter.setOpacity(self._fade_opacity)
        
        # 绘制背景颜色
        if self._has_focus:
            bg_color = QColor(100, 150, 255, 40)
        else:
            bg_color = self._bg_color
        
        painter.fillPath(path, bg_color)
        
        # 绘制水波涟漪
        if self._ripple_radius > 0 and self._ripple_opacity > 0:
            painter.save()
            painter.setClipPath(path)
            
            ripple_color = QColor(100, 150, 255, int(60 * self._ripple_opacity))
            painter.setBrush(ripple_color)
            painter.setPen(Qt.PenStyle.NoPen)
            
            center = self._ripple_center
            painter.drawEllipse(center, int(self._ripple_radius), int(self._ripple_radius))
            painter.restore()
        
        # 绘制图标和文字
        if self.width() > 40:
            scaled_icon = self.get_scaled_icon()
            
            if not scaled_icon.isNull():
                icon_x = 8
                icon_y = (rect.height() - scaled_icon.height()) // 2
                painter.drawPixmap(icon_x, icon_y, scaled_icon)
                
                text_x = scaled_icon.width() + 16
                text_rect = QRect(text_x, 0, rect.width() - text_x - 8, rect.height())
            else:
                text_rect = rect.adjusted(8, 0, -8, 0)
            
            painter.setPen(self._text_color)
            
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        
        painter.end()
    
    def _show_context_menu(self, position):
        """显示右键菜单：终止任务 / 关闭窗口"""
        menu = QMenu(self)

        target = getattr(self, '_target_window', None)

        # 终止任务：立即销毁窗口（绕过关闭动画，用于无响应场景）
        kill_action = menu.addAction("终止任务")
        if target:
            kill_action.triggered.connect(lambda: QTimer.singleShot(0, self._kill_target))
        else:
            kill_action.setEnabled(False)

        menu.addSeparator()

        # 关闭窗口：走关闭动画 + 终止窗口后台线程（公开 API）
        close_action = menu.addAction("关闭窗口")
        if target:
            if hasattr(target, 'close_and_terminate'):
                close_action.triggered.connect(target.close_and_terminate)
            else:
                close_action.triggered.connect(target.close)
        else:
            close_action.setEnabled(False)

        menu.exec(self.mapToGlobal(position))

    def _kill_target(self):
        """强制终止目标窗口（先终止其后台线程，再销毁）"""
        target = getattr(self, '_target_window', None)
        if target is None:
            return
        try:
            if hasattr(target, 'terminate_thread'):
                target.terminate_thread()
            target.hide()
            target.deleteLater()
        except RuntimeError:
            pass
    
    def start_drag(self):
        """开始拖拽（在任务栏内重新排序）"""
        if not self.parent():
            return
        
        layout = self.parent().layout()
        if not layout:
            return
        
        drag_index = -1
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() == self:
                drag_index = i
                break
        
        if drag_index == -1:
            return
        
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.text())
        mime_data.setData("application/x-button-index", str(drag_index).encode())
        drag.setMimeData(mime_data)
        
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(self.width() // 2, self.height() // 2))
        
        drag.exec(Qt.DropAction.MoveAction)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self._drag_start_pos = event.pos()
            self._apply_state_colors('pressed')
            self._animate_color(self._theme_colors['pressed'])
            self.animate_ripple(event.pos())
            self.update()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_start_pos:
            delta = (event.pos() - self._drag_start_pos).manhattanLength()
            if delta > QApplication.startDragDistance():
                self.start_drag()
                self._is_dragging = True
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = False
            if self.underMouse():
                self._apply_state_colors('hover')
                self._animate_color(self._theme_colors['hover'])
            else:
                self._apply_state_colors('normal')
                self._animate_color(self._theme_colors['normal'])
            
            if not self._is_dragging and self.underMouse():
                self.clicked.emit()
            self._is_dragging = False
            self._drag_start_pos = None
            self.update()
        super().mouseReleaseEvent(event)
    
    def setText(self, text: str):
        """重写setText方法，自动调整宽度"""
        super().setText(text)
        self._update_width()
    
    def enterEvent(self, event):
        self._is_hover = True
        self._apply_state_colors('hover')
        self._animate_color(self._theme_colors['hover'])
        if self.invert_on_hover and not self._inverted_enabled:
            self.update()
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._is_hover = False
        self._apply_state_colors('normal')
        self._animate_color(self._theme_colors['normal'])
        if self.invert_on_hover and not self._inverted_enabled:
            self.update()
        self.update()
        super().leaveEvent(event)
    
    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)
    
    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        if not enabled:
            self._is_hover = False
            self._is_pressed = False
            self.update()

            