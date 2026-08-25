from pack.libs.gui.QtPack import *
from pack.libs.gui.ReadConfigFile import *
import re


class ThemeColors:
    """存储主题颜色配置"""
    def __init__(self, theme_data: dict):
        self.default_color = QColor(theme_data.get('combobox_color', '#232323'))
        self.border_color = QColor(theme_data.get('border_color', '#2B2B2B'))
        self.top_border_color = QColor(theme_data.get('top_border_color', '#424242'))
        self.bottom_border_color = QColor(theme_data.get('bottom_border_color', '#D1D1D1'))
        self.left_border_color = QColor(theme_data.get('left_border_color', '#D1D1D1'))
        self.right_border_color = QColor(theme_data.get('right_border_color', '#D1D1D1'))
        self.text_color = QColor(theme_data.get('text_color', '#FFFFFF'))
        self.arrow_color = QColor(theme_data.get('arrow_color', '#FFFFFF'))
        self.popup_bg_color = QColor(theme_data.get('popup_bg_color', '#1F1F1F'))
        self.item_hover_color = QColor(theme_data.get('item_hover_color', '#3A3A3A'))
        self.item_selected_color = QColor(theme_data.get('item_selected_color', '#0055CC'))


def parse_theme_config(section: str, key: str) -> dict:
    """解析主题配置字符串为字典"""
    value = read_config_value(section, key)
    if not value:
        return {}

    pattern = r'([^:;]+):([^;]+);'
    matches = re.findall(pattern, value)
    return {key.strip(): value.strip() for key, value in matches}


def load_theme_colors(theme: str) -> dict:
    """加载指定主题的所有 ComboBox 颜色配置"""
    section = f'Theme_{theme.capitalize()}'

    combobox_normal = parse_theme_config(section, 'combobox_theme_color')
    combobox_hover = parse_theme_config(section, 'combobox_theme_hover_color')
    combobox_pressed = parse_theme_config(section, 'combobox_theme_pressed_color')
    combobox_focus = parse_theme_config(section, 'combobox_theme_focus_color')

    return {
        'normal': ThemeColors(combobox_normal),
        'hover': ThemeColors(combobox_hover) if combobox_hover else ThemeColors(combobox_normal),
        'pressed': ThemeColors(combobox_pressed) if combobox_pressed else ThemeColors(combobox_normal),
        'focus': ThemeColors(combobox_focus) if combobox_focus else ThemeColors(combobox_normal),
    }


_dark_theme = load_theme_colors('dark')
_light_theme = load_theme_colors('light')


class ComboBox(QComboBox):
    """自定义下拉列表，支持主题切换、颜色动画"""

    hover = pyqtSignal(bool)
    unhover = pyqtSignal(bool)
    pressed = pyqtSignal(bool)
    Release = pyqtSignal(bool)
    focus = pyqtSignal(bool)

    def __init__(self, parent=None, border_radius: int = 3, border_width: int = 1,
                 alpha: int = 255, minsize: QSize = None, maxsize: QSize = None):
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

        theme_data = _dark_theme if is_dark else _light_theme
        self._theme_colors = theme_data

        self.update_animation()

    def _apply_transparency(self, color: QColor) -> QColor:
        """应用透明度到颜色"""
        new_color = QColor(color)
        new_color.setAlpha(self.alpha)
        return new_color

    def _get_current_colors(self):
        """获取当前状态的颜色配置"""
        state_colors = self._theme_colors.get(self._state)
        if not state_colors:
            state_colors = self._theme_colors.get('normal')
        return state_colors

    def _get_current_bg_color(self) -> QColor:
        """获取当前背景颜色"""
        if self._state == 'focus':
            focus_colors = self._theme_colors.get('focus')
            if focus_colors:
                return QColor(focus_colors.default_color)

        normal_colors = self._theme_colors.get('normal')
        hover_colors = self._theme_colors.get('hover')
        pressed_colors = self._theme_colors.get('pressed')

        if not normal_colors:
            return QColor(255, 255, 255, self.alpha)

        base_color = normal_colors.default_color
        hover_color = hover_colors.default_color if hover_colors else base_color

        r = base_color.red() + int((hover_color.red() - base_color.red()) * self.animation_value)
        g = base_color.green() + int((hover_color.green() - base_color.green()) * self.animation_value)
        b = base_color.blue() + int((hover_color.blue() - base_color.blue()) * self.animation_value)
        base_color = QColor(r, g, b, self.alpha)

        pressed_color = pressed_colors.default_color if pressed_colors else base_color
        r = base_color.red() + int((pressed_color.red() - base_color.red()) * self.pressed_animation_value)
        g = base_color.green() + int((pressed_color.green() - base_color.green()) * self.pressed_animation_value)
        b = base_color.blue() + int((pressed_color.blue() - base_color.blue()) * self.pressed_animation_value)

        return QColor(r, g, b, self.alpha)

    def _get_current_text_color(self) -> QColor:
        """获取当前文本颜色"""
        state_colors = self._get_current_colors()
        return state_colors.text_color if state_colors else QColor(255, 255, 255)

    def _get_border_color(self) -> QColor:
        """获取当前边框颜色"""
        if self._state == 'focus':
            focus_colors = self._theme_colors.get('focus')
            if focus_colors:
                return focus_colors.border_color

        normal_colors = self._theme_colors.get('normal')
        if not normal_colors:
            return QColor(168, 168, 168, self.alpha)

        base_color = normal_colors.border_color
        hover_colors = self._theme_colors.get('hover')
        if hover_colors and hover_colors.border_color:
            target_color = hover_colors.border_color
            r = base_color.red() + int((target_color.red() - base_color.red()) * self.animation_value)
            g = base_color.green() + int((target_color.green() - base_color.green()) * self.animation_value)
            b = base_color.blue() + int((target_color.blue() - base_color.blue()) * self.animation_value)
            return QColor(r, g, b, self.alpha)
        return QColor(base_color)

    def _get_border_style(self) -> str:
        """生成边框样式字符串"""
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
        """更新悬停和按下动画"""
        if self.hovered and self.animation_value < 1:
            self.animation_value += 0.1
            if self.animation_value > 1:
                self.animation_value = 1
        elif not self.hovered and self.animation_value > 0:
            self.animation_value -= 0.1
            if self.animation_value < 0:
                self.animation_value = 0

        if self.pressed_state and self.pressed_animation_value < 1:
            self.pressed_animation_value += 0.1
            if self.pressed_animation_value > 1:
                self.pressed_animation_value = 1
        elif not self.pressed_state and self.pressed_animation_value > 0:
            self.pressed_animation_value -= 0.1
            if self.pressed_animation_value < 0:
                self.pressed_animation_value = 0

        self._update_stylesheet()

    def _update_stylesheet(self):
        """更新完整样式表"""
        current_color = self._get_current_bg_color()
        text_color = self._get_current_text_color()
        border_color = self._get_border_color()
        colors = self._get_current_colors()

        bg_str = f"rgba({current_color.red()}, {current_color.green()}, {current_color.blue()}, {self.alpha / 255})"
        border_str = f"{self.border_width}px solid {border_color.name()}"

        # 下拉弹出框的颜色
        popup_bg = colors.popup_bg_color.name() if colors else "#1F1F1F"
        item_hover = colors.item_hover_color.name() if colors else "#3A3A3A"
        item_selected = colors.item_selected_color.name() if colors else "#0055CC"
        text_color_str = text_color.name()

        style = f"""
        QComboBox {{
            background-color: {bg_str};
            {border_str};
            border-radius: {self.border_radius}px;
            padding: 4px 8px;
            padding-right: 24px;
            color: {text_color_str};
            min-height: 20px;
        }}
        QComboBox:hover {{
            border-color: {border_color.name()};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            border-left: none;
            border-top-right-radius: {self.border_radius}px;
            border-bottom-right-radius: {self.border_radius}px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {popup_bg};
            border: 1px solid {border_color.name()};
            border-radius: 4px;
            selection-background-color: transparent;
            color: {text_color_str};
            outline: none;
            padding: 4px;
            margin: 2px 0px;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 6px 10px;
            min-height: 26px;
            border-radius: 3px;
            margin: 1px 0px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {item_hover};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {item_selected};
            color: {text_color_str};
        }}
        QComboBox QScrollBar:vertical {{
            width: 6px;
            background: transparent;
            border-radius: 3px;
            margin: 2px 0px;
        }}
        QComboBox QScrollBar::handle:vertical {{
            background: rgba(100, 100, 100, 100);
            border-radius: 3px;
            min-height: 20px;
        }}
        QComboBox QScrollBar::handle:vertical:hover {{
            background: rgba(120, 120, 120, 150);
        }}
        QComboBox QScrollBar::add-line:vertical,
        QComboBox QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QComboBox QScrollBar::add-page:vertical,
        QComboBox QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        """

        self.setStyleSheet(style)
        self.update()

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

    def setOpacity(self, opacity_num: float):
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(opacity_num)
        self.setGraphicsEffect(effect)
