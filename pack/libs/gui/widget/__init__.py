from pack.libs.gui.QtPack import *
from pack.libs.gui.ReadConfigFile import *
# from BlurWindow.blurWindow import GlobalBlur
import os
import re
class ThemeColors:
    """存储主题颜色配置"""
    def __init__(self, theme_data: dict):
        self.default_color = QColor(theme_data.get('frame_color', '#232323'))
        self.border_color = QColor(theme_data.get('border_color', '#2B2B2B'))
        self.top_border_color = QColor(theme_data.get('top_border_color', '#424242'))
        self.bottom_border_color = QColor(theme_data.get('bottom_border_color', '#D1D1D1'))
        self.left_border_color = QColor(theme_data.get('left_border_color', '#D1D1D1'))
        self.right_border_color = QColor(theme_data.get('right_border_color', '#D1D1D1'))
        self.text_color = QColor(theme_data.get('text_color', '#FFFFFF'))

def parse_theme_config(section: str, key: str) -> dict:
    """解析主题配置字符串为字典"""
    value = read_config_value(section, key)
    if not value:
        return {}
    
    # 匹配 key:value; 格式
    pattern = r'([^:;]+):([^;]+);'
    matches = re.findall(pattern, value)
    return {key.strip(): value.strip() for key, value in matches}

def load_theme_colors(theme: str) -> dict:
    """
    加载指定主题的所有按钮颜色配置
    theme: 'dark' 或 'light'
    返回: {'normal': ThemeColors, 'hover': ThemeColors, 'pressed': ThemeColors}
    """
    section = f'Theme_{theme.capitalize()}'
    
    normal_data = parse_theme_config(section, 'frame_theme_color')
    hover_data = parse_theme_config(section, 'frame_theme_hover_color')
    pressed_data = parse_theme_config(section, 'frame_theme_pressed_color')
    
    return {
        'normal': ThemeColors(normal_data),
        'hover': ThemeColors(hover_data),
        'pressed': ThemeColors(pressed_data)
    }

# 预加载主题（也可以延迟加载）
_dark_theme = load_theme_colors('dark')
_light_theme = load_theme_colors('light')
_dark_input_event = read_config_value("Theme_Dark","frame_Input_event")
_light_input_event = read_config_value("Theme_Light","frame_Input_event")



class Widget(QWidget):
    PressEvent = pyqtSignal(bool)
    ReleaseEvent = pyqtSignal(bool)
    
    def __init__(self, parent=None, border_radius: int = 3, border_width: int = 1, 
                 shadow: bool = False, transparent: int = 255):
        super().__init__(parent)
        self.border_width = border_width
        self.border_radius = border_radius
        self.shadow = shadow
        self._transparent = max(0, min(255, transparent))
        
        # 颜色存储
        self._current_theme = None  # 'dark' 或 'light'
        self._state = 'normal'  # 'normal', 'hover', 'pressed'
        self._bg_color = QColor()
        self._theme_colors = {'normal': None, 'hover': None, 'pressed': None}
        
        self.update_colors()
        QApplication.instance().paletteChanged.connect(self.update_colors)
        
        # 颜色动画
        self._animation = QPropertyAnimation(self, b"bgColor")
        self._animation.setDuration(240)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def _is_dark_mode(self) -> bool:
        """检测当前是否为深色模式"""
        palette = QApplication.palette()
        return palette.window().color().lightness() < 128
    
    def update_colors(self):
        """更新颜色方案"""
        is_dark = self._is_dark_mode()
        self._current_theme = 'dark' if is_dark else 'light'
        
        # 加载对应主题
        theme_data = _dark_theme if is_dark else _light_theme
        self._theme_colors = theme_data
        
        # 设置当前颜色
        self._apply_state_colors('normal')
        self._update_style()
    
    def _apply_state_colors(self, state: str):
        """应用指定状态的颜色"""
        self._state = state
        colors = self._theme_colors.get(state)
        if colors:
            self._bg_color = self._apply_transparency(colors.default_color)
    
    def _apply_transparency(self, color: QColor) -> QColor:
        """应用透明度到颜色"""
        new_color = QColor(color)
        new_color.setAlpha(self._transparent)
        return new_color
    
    def _get_border_style(self, colors) -> str:
        """生成边框样式字符串"""
        if self.border_width == 0:
            return ""
        
        return f"""
            border: {self.border_width}px solid {colors.border_color.name()};
            border-top: {self.border_width}px solid {colors.top_border_color.name()};
            border-bottom: {self.border_width}px solid {colors.bottom_border_color.name()};
            border-left: {self.border_width}px solid {colors.left_border_color.name()};
            border-right: {self.border_width}px solid {colors.right_border_color.name()};
        """
    
    def _update_style(self):
        """更新按钮样式表"""
        colors = self._theme_colors.get(self._state, self._theme_colors['normal'])
        if not colors:
            return
        
        # 背景色（支持透明度）
        bg_color = self._bg_color
        bg_color_str = f"rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, {bg_color.alpha()/255})"
        
        # 文本颜色
        text_color = colors.text_color.name()
        
        # 边框样式
        border_style = self._get_border_style(colors) if self.border_width > 0 else ""
        
        style = f"""
        Widget {{
            background-color: {bg_color_str};
            {border_style}
            color: {text_color};
            border-radius: {self.border_radius}px;
        }}
        """
        
        self.setStyleSheet(style)
    
    def getBgColor(self):
        return self._bg_color
    
    def setBgColor(self, color):
        if isinstance(color, QColor):
            new_color = QColor(color)
            new_color.setAlpha(self._transparent)
            self._bg_color = new_color
        else:
            self._bg_color = self._apply_transparency(color)
        self._update_style()
    
    bgColor = pyqtProperty(QColor, getBgColor, setBgColor)
    
    def getTransparent(self) -> int:
        return self._transparent
    
    def setTransparent(self, value: int):
        new_value = max(0, min(255, value))
        if self._transparent == new_value:
            return
        
        self._transparent = new_value
        self._apply_state_colors(self._state)
        self._update_style()
    
    transparent = pyqtProperty(int, getTransparent, setTransparent)
    
    def enterEvent(self, event):
        if _light_input_event or _dark_input_event == "False":
            pass
        else:
            hover_color = self._apply_transparency(self._theme_colors['hover'].default_color)
            self._animate_color(hover_color)
            self._state = 'hover'
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if _light_input_event or _dark_input_event == "False":
            pass
        else:

            normal_color = self._apply_transparency(self._theme_colors['normal'].default_color)
            self._animate_color(normal_color)
            self._state = 'normal'
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if _light_input_event or _dark_input_event == "False":
            pass
        else:

            if event.button() == Qt.LeftButton:
                pressed_color = self._apply_transparency(self._theme_colors['pressed'].default_color)
                self._animate_color(pressed_color)
                self._state = 'pressed'
                self.PressEvent.emit(True)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if _light_input_event or _dark_input_event == "False":
            pass
        else:
            self.ReleaseEvent.emit(False)
            if event.button() == Qt.LeftButton:
                if self.underMouse():
                    target = self._apply_transparency(self._theme_colors['hover'].default_color)
                    self._state = 'hover'
                else:
                    target = self._apply_transparency(self._theme_colors['normal'].default_color)
                    self._state = 'normal'
                self._animate_color(target)
        super().mouseReleaseEvent(event)
    
    def _animate_color(self, target_color):
        self._animation.stop()
        self._animation.setStartValue(self._bg_color)
        self._animation.setEndValue(target_color)
        self._animation.start()
    
    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        if not enabled:
            disabled_color = self._apply_transparency(self._theme_colors['normal'].default_color)
            disabled_color.setAlpha(int(self._transparent * 0.5))
            self.setBgColor(disabled_color)
        else:
            self._apply_state_colors('normal')
            self._update_style()
class PopupWidget(QWidget):
    focusOut = pyqtSignal()
    
    def __init__(self, parent: QWidget,GlobalBlurS:bool=False):
        super().__init__(parent)
        # 使用正确的窗口标志，允许焦点
        self.setWindowFlags(
            Qt.Popup |
            Qt.FramelessWindowHint |
            Qt.NoDropShadowWindowHint
        )
        # 关键：设置这些属性允许焦点
        # self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.setFocusPolicy(Qt.StrongFocus)
            
    def showEvent(self, event):
        """显示时确保可以获得焦点"""
        super().showEvent(event)
        self.setFocus()
        
    def focusOutEvent(self, event):
        """焦点离开事件"""
        self.focusOut.emit()
        super().focusOutEvent(event)
        
    def closeEvent(self, event):
        self.focusOut.emit()
        super().closeEvent(event)
class ImageWidget(QWidget):
    def __init__(self, parent=None, image: str = "", blur_radius: int = 0):
        super().__init__(parent)
        self.image_path = image
        self.pixmap = QPixmap()
        # 模糊半径（像素）。0 表示不模糊。
        self._blur_radius = blur_radius
        self._blurred_cache = QPixmap()  # 缩放＋模糊后的缓存，避免每次重绘都重算
        self._cache_size = QSize()
        self._pixmap_key = -1

        if self.image_path:
            self.load_image(self.image_path)

    def set_blur_radius(self, radius: int):
        """设置背景模糊半径（>0 生效），并立即刷新。"""
        radius = max(0, int(radius))
        if radius != self._blur_radius:
            self._blur_radius = radius
            self._blurred_cache = QPixmap()  # 使缓存失效
            self.update()

    def blur_radius(self) -> int:
        return self._blur_radius

    def load_image(self, image_path: str):
        """加载图片"""
        # QPixmap 只接受字符串路径，需将 pathlib.Path 等转换为字符串
        self.image_path = image_path
        self.pixmap = QPixmap(os.fspath(image_path))
        self._blurred_cache = QPixmap()  # 使缓存失效
        self.update()

    def _get_scaled_pixmap(self, widget_size):
        """返回按控件大小等比放大填满（居中裁剪）的 pixmap。"""
        return self.pixmap.scaled(
            widget_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,  # 核心：拉伸填满
            Qt.TransformationMode.SmoothTransformation
        )

    def _cropped_rect(self, full_size, widget_size):
        """返回从 full_size 图中居中裁剪出 widget_size 的 QRect。"""
        x = (full_size.width() - widget_size.width()) // 2
        y = (full_size.height() - widget_size.height()) // 2
        return QRect(max(0, x), max(0, y), widget_size.width(), widget_size.height())

    def _get_draw_pixmap(self, widget_size):
        """返回（缩放，必要时模糊+回裁）后、与控件同尺寸、可直接绘制的 pixmap。"""
        # 缓存命中：尺寸与图片均未变，直接复用
        if (not self._blurred_cache.isNull()
                and self._cache_size == widget_size
                and self._pixmap_key == self.pixmap.cacheKey()):
            return self._blurred_cache

        scaled = self._get_scaled_pixmap(widget_size)

        if self._blur_radius > 0:
            # 高斯模糊会把边缘像素向外扩散，item 边缘一圈会与透明背景混合而
            # 变淡/泛白。为避免 crop 时裁到这条模糊边缘，要求「居中裁剪区」的
            # 四周到原图边缘至少保留 blur_radius 的余量。
            # 若 Expanding 放大后的图不够大（某维度贴紧控件），则先把图再放大，
            # 保证任意方向至少有 blur_radius 的富余。
            need = self._blur_radius * 2          # 四周所需余量（>= 模糊半径才有保障）
            pad_x = (scaled.width() - widget_size.width()) // 2
            pad_y = (scaled.height() - widget_size.height()) // 2

            # 若某方向余量不足（可能贴边），先把原图等比放大，保证四周足够富余
            if pad_x < need or pad_y < need:
                ratio_w = (widget_size.width() + 2 * need) / max(1, widget_size.width())
                ratio_h = (widget_size.height() + 2 * need) / max(1, widget_size.height())
                ratio = max(ratio_w, ratio_h)
                scaled = scaled.scaled(
                    scaled.size() * ratio,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
                pad_x = (scaled.width() - widget_size.width()) // 2
                pad_y = (scaled.height() - widget_size.height()) // 2

            # 外扩画布：四周额外留出 blur_radius（模糊扩散区）
            margin = self._blur_radius
            canvas_size = scaled.size() + QSize(2 * margin, 2 * margin)

            scene = QGraphicsScene(0, 0, canvas_size.width(), canvas_size.height())
            item = QGraphicsPixmapItem(scaled)
            item.setOffset(margin, margin)
            effect = QGraphicsBlurEffect()
            effect.setBlurRadius(self._blur_radius)
            item.setGraphicsEffect(effect)
            scene.addItem(item)

            canvas = QPixmap(canvas_size)
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            scene.render(painter)
            painter.end()

            # 从模糊画布中，裁回与控件同尺寸的居中区域：复用上面算好的 pad_x/pad_y，
            # 且距画布边缘保留 margin（>= blur），确保不含模糊边缘泛白区。
            blur_crop = QRect(
                margin + pad_x,
                margin + pad_y,
                min(widget_size.width(), scaled.width()),
                min(widget_size.height(), scaled.height()),
            )
            self._blurred_cache = canvas.copy(blur_crop)
        else:
            # 不模糊：直接从放大图居中裁出控件尺寸
            self._blurred_cache = scaled.copy(self._cropped_rect(scaled.size(), widget_size))

        self._cache_size = widget_size
        self._pixmap_key = self.pixmap.cacheKey()
        return self._blurred_cache

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap.isNull():
            return

        # 控件大小（目标区域）
        widget_size = self.size()

        draw_pixmap = self._get_draw_pixmap(widget_size)

        # 现在 draw_pixmap 与控件同尺寸，直接铺满绘制（居中裁剪已在内部完成）
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, draw_pixmap)

    def resizeEvent(self, event):
        self._cache_size = QSize()  # 尺寸变化，缓存失效
        self.update()
        super().resizeEvent(event)
class AnimatedWidget(QWidget):
    """具有缩放动画和透明度动画效果的交互控件，支持窗口化模式"""
    
    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    DISABLED = 3
    
    EDGE_NONE = 0
    EDGE_LEFT = 1
    EDGE_RIGHT = 2
    EDGE_TOP = 3
    EDGE_BOTTOM = 4
    EDGE_TOP_LEFT = 5
    EDGE_TOP_RIGHT = 6
    EDGE_BOTTOM_LEFT = 7
    EDGE_BOTTOM_RIGHT = 8
    
    ATTR_DRAG = "Drag"
    ATTR_ZOOM = "Zoom"
    
    hover = pyqtSignal(bool)
    pressed = pyqtSignal(bool)
    unhover = pyqtSignal(bool)
    mouseReleased = pyqtSignal(bool)
    mousePressed = pyqtSignal(bool)
    focusOut = pyqtSignal()
    
    windowResized = pyqtSignal(QRect)
    windowMoved = pyqtSignal(QPoint)
    windowClosed = pyqtSignal()
    
    def __init__(self, parent=None, windowed: bool = False, Attribute: tuple = ()):
        super().__init__(parent)
        
        self.windowed = windowed
        self.attribute = Attribute
        
        self._drag_enabled = self.windowed and self.ATTR_DRAG not in self.attribute
        self._zoom_enabled = self.windowed and self.ATTR_ZOOM not in self.attribute
        
        self._is_dragging = False
        self._is_resizing = False
        self._drag_position = None
        self._resize_edge = self.EDGE_NONE
        self._resize_start_rect = None
        
        self.resize_margin = 8
        self.minimum_width = 100
        self.minimum_height = 60
        
        self._current_state = self.NORMAL
        self._scale_factor = 1.0
        self._opacity = 1.0
        self._pulse_radius = 0.0
        self._pulse_opacity = 1.0

        self._scale_children = False
        self._is_animating_scale = False
        self._saved_geometries = {}
        self._child_opacity_effects = {}
        
        self.border_radius = 3
        self.animation_duration = 300
        
        QApplication.instance().paletteChanged.connect(self.update_colors)
        self.update_colors()
        
        self.scale_animation = QPropertyAnimation(self, b"scale_factor")
        self.scale_animation.setDuration(300)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutExpo)
        self.scale_animation.finished.connect(self._on_scale_animation_finished)
        
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if self.windowed and self._zoom_enabled:
            self.setMouseTracking(True)
    
    def _on_scale_animation_finished(self):
        self._is_animating_scale = False
        if self._scale_factor == 1.0:
            self._restore_layout_control()
    
    def _restore_layout_control(self):
        for child in list(self._saved_geometries.keys()):
            try:
                if child and not child.isHidden() and child.parent() == self:
                    if hasattr(child, '_manual_geometry_set'):
                        child.setParent(None)
                        child.setParent(self)
                        delattr(child, '_manual_geometry_set')
            except (RuntimeError, AttributeError):
                pass
        self._saved_geometries.clear()
        self.updateGeometry()
        if hasattr(self, 'main_layout') and self.main_layout:
            self.main_layout.activate()
    
    def add_widget(self, widget):
        if hasattr(self, 'main_layout'):
            self.main_layout.addWidget(widget)
    
    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128

        if is_dark:
            self.normal_bg_color = QColor(40, 40, 40)
            self.hover_bg_color = QColor(40, 40, 40)
            self.pressed_bg_color = QColor(40, 40, 40)
            self.disabled_bg_color = QColor(40, 40, 40)
        else:
            self.normal_bg_color = QColor(255, 255, 255)
            self.hover_bg_color = QColor(240, 240, 240)
            self.pressed_bg_color = QColor(255, 255, 255)
            self.disabled_bg_color = QColor(255, 255, 255)
    
    def focusInEvent(self, event):
        self.raise_()
        return super().focusInEvent(event)
    
    def set_scale_animation(self, start: float, end: float, duration: int = 300, 
                           finished=None, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
        self._is_animating_scale = True
        self.scale_animation.stop()
        
        if start != 1.0 and end == 1.0:
            self._save_children_geometries()
        
        self.scale_animation.setStartValue(start)
        self.scale_animation.setEndValue(end)
        self.scale_animation.setDuration(duration)
        self.scale_animation.setEasingCurve(easing)
        
        try:
            self.scale_animation.finished.disconnect()
        except:
            pass
        
        if finished:
            self.scale_animation.finished.connect(finished)
        
        self.scale_animation.start()
    
    def _save_children_geometries(self):
        self._saved_geometries.clear()
        for child in self.findChildren(QWidget):
            try:
                if child is self or child.parent() != self:
                    continue
                if not child.isHidden():
                    self._saved_geometries[child] = child.geometry()
            except (RuntimeError, AttributeError):
                continue
    
    def set_opacity_animation(self, start: float, end: float, duration: int = 300,
                             finished=None, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(start)
        self.opacity_animation.setEndValue(end)
        self.opacity_animation.setDuration(duration)
        self.opacity_animation.setEasingCurve(easing)
        self.opacity_animation.start()
        if finished is not None:
            self.opacity_animation.finished.connect(finished)

    def get_scale_factor(self):
        return self._scale_factor

    def set_scale_factor(self, value):
        old_value = self._scale_factor
        self._scale_factor = value
        try:
            self._update_children_geometry()
        except RuntimeError:
            pass
        self.update()
    
    def _update_children_geometry(self):
        if not self._scale_children or self._scale_factor == 1.0:
            return
        
        if not self._saved_geometries:
            return
        
        cx, cy = self.width() / 2, self.height() / 2
        
        for child, orig_geom in list(self._saved_geometries.items()):
            try:
                if child is None:
                    continue
                if child.parent() != self:
                    continue
                if child.isHidden():
                    continue
                
                x = (orig_geom.x() - cx) * self._scale_factor + cx
                y = (orig_geom.y() - cy) * self._scale_factor + cy
                w = orig_geom.width() * self._scale_factor
                h = orig_geom.height() * self._scale_factor
                
                child.setGeometry(int(x), int(y), int(w), int(h))
                child._manual_geometry_set = True
            except (RuntimeError, AttributeError):
                continue
    
    def get_opacity(self) -> float:
        return self._opacity
    
    def set_opacity(self, value: float):
        self._opacity = max(0.0, min(1.0, value))
        self._update_children_opacity()
        self.update()
    
    def _update_children_opacity(self):
        """更新所有子控件的透明度"""
        for child in self.findChildren(QWidget):
            try:
                if child is self or child.parent() != self:
                    continue
                if child.isHidden():
                    continue
                
                if self._opacity >= 0.99:
                    if child in self._child_opacity_effects:
                        effect = self._child_opacity_effects.pop(child)
                        if effect:
                            effect.deleteLater()
                    child.setGraphicsEffect(None)
                else:
                    if child not in self._child_opacity_effects:
                        effect = QGraphicsOpacityEffect(child)
                        effect.setOpacity(self._opacity)
                        child.setGraphicsEffect(effect)
                        self._child_opacity_effects[child] = effect
                    else:
                        effect = self._child_opacity_effects[child]
                        if effect:
                            effect.setOpacity(self._opacity)
                    
            except (RuntimeError, AttributeError):
                continue
    
    def childEvent(self, event):
        """监听子控件添加事件，自动添加透明度效果"""
        if event.type() == QEvent.ChildAdded:
            child = event.child()
            if isinstance(child, QWidget) and child != self:
                if self._opacity < 0.99:
                    effect = QGraphicsOpacityEffect(child)
                    effect.setOpacity(self._opacity)
                    child.setGraphicsEffect(effect)
                    self._child_opacity_effects[child] = effect
        super().childEvent(event)

    scale_factor = pyqtProperty(float, get_scale_factor, set_scale_factor)
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def setFocusOutEvent(self, handler):
        self.focusOut.connect(handler)
    
    def set_windowed_mode(self, windowed: bool, Attribute: tuple = None):
        self.windowed = windowed
        
        if Attribute is not None:
            self.attribute = Attribute
        
        self._drag_enabled = self.windowed and self.ATTR_DRAG not in self.attribute
        self._zoom_enabled = self.windowed and self.ATTR_ZOOM not in self.attribute
        
        self.setMouseTracking(self.windowed and self._zoom_enabled)
        
        if not windowed:
            self._is_dragging = False
            self._is_resizing = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def get_resize_edge(self, pos: QPoint) -> int:
        if not self.windowed or not self._zoom_enabled:
            return self.EDGE_NONE
        
        rect = self.rect()
        margin = self.resize_margin
        
        left = pos.x() <= margin
        right = pos.x() >= rect.width() - margin
        top = pos.y() <= margin
        bottom = pos.y() >= rect.height() - margin
        
        if left and top:
            return self.EDGE_TOP_LEFT
        elif right and top:
            return self.EDGE_TOP_RIGHT
        elif left and bottom:
            return self.EDGE_BOTTOM_LEFT
        elif right and bottom:
            return self.EDGE_BOTTOM_RIGHT
        elif left:
            return self.EDGE_LEFT
        elif right:
            return self.EDGE_RIGHT
        elif top:
            return self.EDGE_TOP
        elif bottom:
            return self.EDGE_BOTTOM
        else:
            return self.EDGE_NONE
    
    def update_cursor(self, edge: int):
        if not self.windowed or not self._zoom_enabled:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        
        cursor_map = {
            self.EDGE_LEFT: Qt.CursorShape.SizeHorCursor,
            self.EDGE_RIGHT: Qt.CursorShape.SizeHorCursor,
            self.EDGE_TOP: Qt.CursorShape.SizeVerCursor,
            self.EDGE_BOTTOM: Qt.CursorShape.SizeVerCursor,
            self.EDGE_TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
            self.EDGE_BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
            self.EDGE_TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
            self.EDGE_BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
        }
        self.setCursor(cursor_map.get(edge, Qt.CursorShape.ArrowCursor))
    
    def mouseMoveEvent(self, event):
        if not self.windowed:
            return super().mouseMoveEvent(event)
        
        pos = event.pos()
        
        if self._zoom_enabled and self._is_resizing and event.buttons() == Qt.MouseButton.LeftButton:
            self.resize_widget(pos)
        elif self._drag_enabled and self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move_widget(event.globalPos())
        elif self._zoom_enabled:
            edge = self.get_resize_edge(pos)
            self.update_cursor(edge)
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        self.mousePressed.emit(True)
        self.raise_()
        
        if self.windowed and event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            edge = self.get_resize_edge(pos)
            
            if self._zoom_enabled and edge != self.EDGE_NONE:
                self._is_resizing = True
                self._resize_edge = edge
                self._resize_start_rect = self.geometry()
                self._drag_position = event.globalPos()
            elif self._drag_enabled:
                self._is_dragging = True
                self._drag_position = event.globalPos()
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.mouseReleased.emit(True)
        
        if self.windowed:
            self._is_dragging = False
            self._is_resizing = False
            
            if self._zoom_enabled:
                pos = event.pos()
                edge = self.get_resize_edge(pos)
                self.update_cursor(edge)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        
        super().mouseReleaseEvent(event)
    
    def move_widget(self, global_pos: QPoint):
        if not self.windowed or not self._drag_enabled or self._drag_position is None:
            return
        
        delta = global_pos - self._drag_position
        new_pos = self.pos() + delta
        self.move(new_pos)
        self._drag_position = global_pos
        
        self.windowMoved.emit(self.pos())
    
    def resize_widget(self, pos: QPoint):
        if not self.windowed or not self._zoom_enabled or self._resize_start_rect is None or self._drag_position is None:
            return
        
        global_delta = self.mapToGlobal(pos) - self._drag_position
        
        new_rect = QRect(self._resize_start_rect)
        
        if self._resize_edge in [self.EDGE_LEFT, self.EDGE_TOP_LEFT, self.EDGE_BOTTOM_LEFT]:
            new_width = max(self.minimum_width, self._resize_start_rect.width() - global_delta.x())
            new_rect.setLeft(new_rect.right() - new_width)
        
        if self._resize_edge in [self.EDGE_RIGHT, self.EDGE_TOP_RIGHT, self.EDGE_BOTTOM_RIGHT]:
            new_width = max(self.minimum_width, self._resize_start_rect.width() + global_delta.x())
            new_rect.setWidth(new_width)
        
        if self._resize_edge in [self.EDGE_TOP, self.EDGE_TOP_LEFT, self.EDGE_TOP_RIGHT]:
            new_height = max(self.minimum_height, self._resize_start_rect.height() - global_delta.y())
            new_rect.setTop(new_rect.bottom() - new_height)
        
        if self._resize_edge in [self.EDGE_BOTTOM, self.EDGE_BOTTOM_LEFT, self.EDGE_BOTTOM_RIGHT]:
            new_height = max(self.minimum_height, self._resize_start_rect.height() + global_delta.y())
            new_rect.setHeight(new_height)
        
        self.setGeometry(new_rect)
        self.windowResized.emit(new_rect)
    
    def enterEvent(self, event):
        self._current_state = self.HOVER
        self.hover.emit(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._current_state = self.NORMAL
        self.unhover.emit(True)
        if self.windowed:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center = QPoint(width // 2, height // 2)
        
        if not self.isEnabled():
            bg_color = self.disabled_bg_color
        elif self._current_state == self.PRESSED:
            bg_color = self.pressed_bg_color
        elif self._current_state == self.HOVER:
            bg_color = self.hover_bg_color
        else:
            bg_color = self.normal_bg_color
        
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, bg_color.lighter(110))
        gradient.setColorAt(1, bg_color)
        
        painter.save()
        
        transform = QTransform()
        transform.translate(center.x(), center.y())
        transform.scale(self._scale_factor, self._scale_factor)
        transform.translate(-center.x(), -center.y())
        painter.setTransform(transform)
        
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, self.border_radius, self.border_radius)
        
        painter.setOpacity(self._opacity)
        painter.fillPath(path, gradient)
        
        border_color = bg_color.darker(120)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)
        
        painter.restore()
        
        if self.windowed and self._zoom_enabled and self.hasFocus():
            painter.save()
            painter.setOpacity(self._opacity)
            painter.setPen(QPen(QColor(100, 100, 255, 100), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            margin = self.resize_margin
            rect = self.rect().adjusted(margin, margin, -margin, -margin)
            painter.drawRect(rect)
            painter.restore()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_animating_scale and self._scale_factor != 1.0:
            try:
                self._update_children_geometry()
            except RuntimeError:
                pass