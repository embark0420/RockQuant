from pack.libs.gui.QtPack import *
from pack.libs.gui.ReadConfigFile import *
import re

class ThemeColors:
    """存储主题颜色配置"""
    def __init__(self, theme_data: dict):
        self.default_color = QColor(theme_data.get('button_color', '#232323'))
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
    
    normal_data = parse_theme_config(section, 'button_theme_color')
    hover_data = parse_theme_config(section, 'button_theme_hover_color')
    pressed_data = parse_theme_config(section, 'button_theme_pressed_color')
    
    return {
        'normal': ThemeColors(normal_data),
        'hover': ThemeColors(hover_data),
        'pressed': ThemeColors(pressed_data)
    }

# 预加载主题（也可以延迟加载）
_dark_theme = load_theme_colors('dark')
_light_theme = load_theme_colors('light')

class Button(QPushButton):
    PressEvent = pyqtSignal(bool)
    ReleaseEvent = pyqtSignal(bool)
    
    def __init__(self, text="", parent=None, border_radius: int = 3, border_width: int = 1, 
                 text_alignment: str = "center", shadow: bool = False, transparent: int = 255,padding: int = 5,font_size : int = 12):
        super().__init__(text, parent)
        self.border_width = border_width
        self.border_radius = border_radius
        self.text_alignment = text_alignment
        self.shadow = shadow
        self.font_size = font_size
        self.padding = padding
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
        QPushButton {{
            background-color: {bg_color_str};
            {border_style}
            color: {text_color};
            border-radius: {self.border_radius}px;
            text-align: {self.text_alignment};
            padding: {self.padding}px;
            font-size : {self.font_size}px;
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
        hover_color = self._apply_transparency(self._theme_colors['hover'].default_color)
        self._animate_color(hover_color)
        self._state = 'hover'
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        normal_color = self._apply_transparency(self._theme_colors['normal'].default_color)
        self._animate_color(normal_color)
        self._state = 'normal'
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pressed_color = self._apply_transparency(self._theme_colors['pressed'].default_color)
            self._animate_color(pressed_color)
            self._state = 'pressed'
            self.PressEvent.emit(True)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
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