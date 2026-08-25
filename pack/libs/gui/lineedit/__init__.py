from pack.libs.gui.QtPack import *
from pack.libs.gui.ReadConfigFile import *
import re

class ThemeColors:
    """存储主题颜色配置"""
    def __init__(self, theme_data: dict):
        self.default_color = QColor(theme_data.get('lineedit_color', '#232323'))
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
    
    pattern = r'([^:;]+):([^;]+);'
    matches = re.findall(pattern, value)
    return {key.strip(): value.strip() for key, value in matches}

def load_theme_colors(theme: str) -> dict:
    """加载指定主题的所有控件颜色配置"""
    section = f'Theme_{theme.capitalize()}'
    
    # 解析各个控件的配置
    lineedit_normal = parse_theme_config(section, 'lineedit_theme_color')
    lineedit_hover = parse_theme_config(section, 'lineedit_theme_hover_color')
    lineedit_pressed = parse_theme_config(section, 'lineedit_theme_pressed_color')
    lineedit_focus = parse_theme_config(section, 'lineedit_theme_focus_color')  # 改为 focus
    
    return {
        'normal': ThemeColors(lineedit_normal),
        'hover': ThemeColors(lineedit_hover) if lineedit_hover else ThemeColors(lineedit_normal),
        'pressed': ThemeColors(lineedit_pressed) if lineedit_pressed else ThemeColors(lineedit_normal),
        'focus': ThemeColors(lineedit_focus) if lineedit_focus else ThemeColors(lineedit_normal)  # 添加 focus 状态
    }

_dark_theme = load_theme_colors('dark')
_light_theme = load_theme_colors('light')


class LineEdit(QLineEdit):
    hover = pyqtSignal(bool)
    pressed = pyqtSignal(bool)
    Release = pyqtSignal(bool)
    unhover = pyqtSignal(bool)
    focus = pyqtSignal(bool)
    keyPressed = pyqtSignal(QKeyEvent)
    keyReleased = pyqtSignal(QKeyEvent)
    
    def __init__(self, parent=None, border_radius: int = 3, border_width: int = 1, 
                 setCursor: Qt.CursorShape = None, alpha: int = 255,
                 minsize: QSize = None, maxsize: QSize = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        if minsize is not None:
            self.setMinimumSize(minsize)
        if maxsize is not None:
            self.setMaximumSize(maxsize)
    
        self.animation_value = 0
        self.pressed_animation_value = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        self.hovered = False
        self.pressed_state = False
        
        self.border_width = border_width
        self.border_radius = border_radius
        if setCursor is not None:
            self.setCursor(setCursor)
        self.alpha = alpha
        
        # 主题颜色存储
        self._current_theme = None
        self._state = 'normal'  # 'normal', 'hover', 'pressed', 'focus'
        self._theme_colors = {'normal': None, 'hover': None, 'pressed': None, 'focus': None}
        
        QApplication.instance().paletteChanged.connect(self.update_colors)
        self.update_colors()
    
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
        
        self.update_animation()
    
    def _apply_transparency(self, color: QColor) -> QColor:
        """应用透明度到颜色"""
        new_color = QColor(color)
        new_color.setAlpha(self.alpha)
        return new_color

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        self.keyReleased.emit(event)
        super().keyReleaseEvent(event)

    def enterEvent(self, event):
        self.hovered = True
        if self._state != 'focus':
            self._state = 'hover'
        self.hover.emit(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        if self._state != 'focus':
            self._state = 'normal'
        self.unhover.emit(True)
        super().leaveEvent(event)

    def focusInEvent(self, event):
        self._state = 'focus'
        self.focus.emit(True)
        super().focusInEvent(event)
        self.update_animation()

    def focusOutEvent(self, event):
        if self.hovered:
            self._state = 'hover'
        else:
            self._state = 'normal'
        self.focus.emit(False)
        super().focusOutEvent(event)
        self.update_animation()

    def setOpacity(self, Opacity_num: float):
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(Opacity_num)
        self.setGraphicsEffect(effect)
    
    def setPlaceholderColor(self, color):
        self.setStyleSheet(self.styleSheet() + f"""
        QLineEdit::placeholder {{
            color: {color.name()};
        }}
        """)
    
    def _get_current_colors(self):
        """获取当前状态的颜色配置"""
        state_colors = self._theme_colors.get(self._state)
        if not state_colors:
            state_colors = self._theme_colors.get('normal')
        return state_colors
    
    def _get_current_bg_color(self) -> QColor:
        """获取当前背景颜色"""
        # 焦点状态直接返回 focus 颜色（不做过渡动画）
        if self._state == 'focus':
            focus_colors = self._theme_colors.get('focus')
            if focus_colors:
                return QColor(focus_colors.default_color)
        
        normal_colors = self._theme_colors.get('normal')
        hover_colors = self._theme_colors.get('hover')
        pressed_colors = self._theme_colors.get('pressed')
        
        if not normal_colors:
            return QColor(255, 255, 255, self.alpha)
        
        # 基础颜色（normal -> hover 过渡）
        base_color = normal_colors.default_color
        hover_color = hover_colors.default_color if hover_colors else base_color
        
        r = base_color.red() + int((hover_color.red() - base_color.red()) * self.animation_value)
        g = base_color.green() + int((hover_color.green() - base_color.green()) * self.animation_value)
        b = base_color.blue() + int((hover_color.blue() - base_color.blue()) * self.animation_value)
        base_color = QColor(r, g, b, self.alpha)
        
        # 按下颜色过渡
        pressed_color = pressed_colors.default_color if pressed_colors else base_color
        r = base_color.red() + int((pressed_color.red() - base_color.red()) * self.pressed_animation_value)
        g = base_color.green() + int((pressed_color.green() - base_color.green()) * self.pressed_animation_value)
        b = base_color.blue() + int((pressed_color.blue() - base_color.blue()) * self.pressed_animation_value)
        
        return QColor(r, g, b, self.alpha)
    
    def _get_current_border_color(self) -> QColor:
        """获取当前边框颜色"""
        # 焦点状态使用 focus 配置
        if self._state == 'focus':
            focus_colors = self._theme_colors.get('focus')
            if focus_colors:
                return focus_colors.border_color
        
        normal_colors = self._theme_colors.get('normal')
        
        if not normal_colors:
            return QColor(168, 168, 168, self.alpha)
        
        # normal -> hover 边框过渡
        base_color = normal_colors.border_color
        hover_colors = self._theme_colors.get('hover')
        if hover_colors and hover_colors.border_color:
            target_color = hover_colors.border_color
            r = base_color.red() + int((target_color.red() - base_color.red()) * self.animation_value)
            g = base_color.green() + int((target_color.green() - base_color.green()) * self.animation_value)
            b = base_color.blue() + int((target_color.blue() - base_color.blue()) * self.animation_value)
            return QColor(r, g, b, self.alpha)
        return QColor(base_color)
    
    def _get_current_text_color(self) -> QColor:
        """获取当前文本颜色"""
        state_colors = self._get_current_colors()
        return state_colors.text_color if state_colors else QColor(255, 255, 255)
    
    def _get_border_style(self) -> str:
        """生成边框样式字符串（根据当前状态）"""
        if self.border_width == 0:
            return ""
        
        colors = self._get_current_colors()
        if not colors:
            return ""
        
        return f"""
            border: {self.border_width}px solid {colors.border_color.name()};
            border-top: {self.border_width}px solid {colors.top_border_color.name()};
            border-bottom: {self.border_width}px solid {colors.bottom_border_color.name()};
            border-left: {self.border_width}px solid {colors.left_border_color.name()};
            border-right: {self.border_width}px solid {colors.right_border_color.name()};
        """
    
    def update_animation(self):
        # 更新悬停动画
        if self.hovered and self.animation_value < 1:
            self.animation_value += 0.1
            if self.animation_value > 1:
                self.animation_value = 1
        elif not self.hovered and self.animation_value > 0:
            self.animation_value -= 0.1
            if self.animation_value < 0:
                self.animation_value = 0

        # 更新按下动画
        if self.pressed_state and self.pressed_animation_value < 1:
            self.pressed_animation_value += 0.1
            if self.pressed_animation_value > 1:
                self.pressed_animation_value = 1
        elif not self.pressed_state and self.pressed_animation_value > 0:
            self.pressed_animation_value -= 0.1
            if self.pressed_animation_value < 0:
                self.pressed_animation_value = 0

        # 获取当前颜色
        current_color = self._get_current_bg_color()
        text_color = self._get_current_text_color()
        border_style = self._get_border_style()

        style = f"""
        QLineEdit {{
            background-color: rgba({current_color.red()}, {current_color.green()}, {current_color.blue()}, {self.alpha/255});
            {border_style}
            border-style: solid;
            outline: none;
            border-radius: {self.border_radius}px;
            padding: 5px;
            color: {text_color.name()};
        }}
        QLineEdit::placeholder {{
            color: rgba({text_color.red()}, {text_color.green()}, {text_color.blue()}, 128);
        }}
        """
        
        self.setStyleSheet(style)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressed_state = True
            self.pressed.emit(True)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.Release.emit(False)
        if event.button() == Qt.LeftButton:
            self.pressed_state = False
        super().mouseReleaseEvent(event)