from pack.libs.gui.QtPack import *
from pack.libs.gui.frame import *
from pack.libs.gui.button import *
from pack.libs.gui.Separator import *
import pathlib
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import re


def _parse_theme_value(value: str) -> dict:
    """解析 'key1:val1;key2:val2;' 格式的配置字符串"""
    if not value:
        return {}
    pattern = r'([^:;]+):([^;]+);'
    return {k.strip(): v.strip() for k, v in re.findall(pattern, value)}


def _load_menu_colors():
    """从 config.toml 读取菜单相关颜色，返回深色/浅色两套"""
    config_path = pathlib.Path(__file__).resolve().parents[4] / "config.toml"
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
    except Exception:
        return _fallback_colors()

    result = {}
    for theme in ("Dark", "Light"):
        section = f"Theme_{theme}"
        sec = config.get(section, {})
        hover_raw = sec.get("button_theme_hover_color", "")
        hover = _parse_theme_value(hover_raw)
        normal_raw = sec.get("button_theme_color", "")
        normal = _parse_theme_value(normal_raw)

        result[theme.lower()] = {
            "bg_color": normal.get("button_color", "#2b2b2b" if theme == "Dark" else "#ffffff"),
            "hover_bg": hover.get("button_color", "#3c3c3c" if theme == "Dark" else "#e9e9e9"),
            "text_color": normal.get("text_color", "#ffffff" if theme == "Dark" else "#000000"),
            "accent_color": "#60A5FA",  # 左侧高亮条颜色
        }
    return result


def _fallback_colors():
    return {
        "dark": {"bg_color": "#2b2b2b", "hover_bg": "#3c3c3c", "text_color": "#ffffff", "accent_color": "#60A5FA"},
        "light": {"bg_color": "#ffffff", "hover_bg": "#e9e9e9", "text_color": "#000000", "accent_color": "#2563EB"},
    }


# 模块加载时读取一次
_MENU_COLORS = _load_menu_colors()


class MenuItem(QWidget):
    """菜单项控件 - 支持悬停高亮，颜色从 config.toml 读取"""

    def __init__(self, text: str, onClick=None, parent=None, icon: str = "", alignment=Qt.AlignLeft):
        super().__init__(parent)
        self._text = text
        self._callback = onClick
        self._icon = icon
        self._alignment = alignment
        self._hovered = False

        self.setFixedHeight(25)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMouseTracking(True)

        # 当前颜色
        self._bg = QColor(0,0,0,0)
        self._hover_bg = QColor("#3c3c3c")
        self._text_color = QColor("#ffffff")
        self._accent = QColor("#60A5FA")

        self.update_colors()
        QApplication.instance().paletteChanged.connect(self.update_colors)

    def _is_dark_mode(self) -> bool:
        palette = QApplication.palette()
        return palette.window().color().lightness() < 128

    def update_colors(self):
        """从 config.toml 重新读取并应用当前主题颜色"""
        global _MENU_COLORS
        _MENU_COLORS = _load_menu_colors()  # 每次刷新，支持热更新

        theme = "dark" if self._is_dark_mode() else "light"
        c = _MENU_COLORS.get(theme, _MENU_COLORS["dark"])

        self._bg = QColor(c["bg_color"])
        self._hover_bg = QColor(c["hover_bg"])
        self._text_color = QColor(c["text_color"])
        self._accent = QColor(c["accent_color"])

        # self.setStyleSheet(f"background: {self._bg.name()};")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._hovered:
            hover_alpha = QColor(self._hover_bg)
            hover_alpha.setAlpha(30)
            painter.fillRect(self.rect(), hover_alpha)
            painter.fillRect(0, 4, 3, self.height() - 8, self._accent)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        painter.setPen(self._text_color)
        text_rect = self.rect().adjusted(16, 0, -12, 0)
        painter.drawText(text_rect, self._alignment | Qt.AlignVCenter, self._text)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mouseReleaseEvent(self, event):
        if self._callback and event.button() == Qt.LeftButton:
            try:
                self._callback(self._text)
            except TypeError:
                self._callback()


class PopupMenuPanel(Frame):
    """弹出菜单面板 - 带淡入+从上滑入动画。
    使用 Qt.Tool 替代 Qt.Popup，避免 Windows 系统强制定位，
    使 self.move() 和动画正常工作。
    """

    # 窗口失焦时发出的信号
    focusOut = pyqtSignal()

    def __init__(self, parent=None,width : int = 190):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.NoDropShadowWindowHint
        )
        self.widthc = width
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.setFocusPolicy(Qt.StrongFocus)

        # ---- 淡入动画 ----
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(280)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCurve)

        # ---- 滑入动画 ----
        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setDuration(450)
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutExpo)

        # ---- 并行动画组 ----
        self._show_anim_group = QParallelAnimationGroup()
        self._show_anim_group.addAnimation(self._fade_anim)
        self._show_anim_group.addAnimation(self._slide_anim)

        self._target_pos = QPoint(0, 0)

        # ---- 主布局 ----
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(0)

        # ---- 内容容器 ----
        self.content = Frame(self)
        self.content.setObjectName("PopupMenuContent")

        # 内容布局
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(6, 6, 6, 6)
        self.content_layout.setSpacing(4)

        self._items = []
        self._callbacks = {}

        outer_layout.addWidget(self.content)

        self.setFixedWidth(self.widthc)
        self.setMinimumHeight(80)

    # ---- 添加项 ----

    def addButton(self, text: str, onClick=None, alignment=Qt.AlignLeft):
        """添加文本菜单项"""
        if not text or text.strip() == "":
            return
        item = MenuItem(text, onClick, self.content, alignment=alignment)
        self.content_layout.addWidget(item)
        self._items.append(item)
        self._callbacks[text] = onClick
        return item

    def addWidget(self, widget: QWidget):
        """添加任意控件到菜单"""
        self.content_layout.addWidget(widget)
        self._items.append(widget)
        return widget

    def addSeparator(self):
        """添加分隔线"""
        sep = Separator(self.content)
        sep.setFixedHeight(1)
        self.content_layout.addWidget(sep)

    def clear(self):
        """清空所有项"""
        for item in self._items:
            item.deleteLater()
        self._items.clear()
        self._callbacks.clear()

    def setWidth(self, width: int):
        """设置面板宽度"""
        self.setFixedWidth(width)

    def setContentStyle(self, stylesheet: str):
        """设置内容容器样式"""
        self.content.setStyleSheet(stylesheet)

    # ---- 显示/隐藏 ----

    def show_at(self, pos: QPoint, slide_from: str = "top"):
        """在指定位置以淡入+方向滑入动画显示。
        slide_from: "top"从上滑入 / "bottom"从下滑入 / "left"从左滑入 / "right"从右滑入
        """
        # ---- 先确定最终位置（不做屏幕边界修正，交由调用方处理）----
        self._target_pos = QPoint(pos)

        # 根据方向计算滑入起点（从相反方向偏移30px）
        offset = 30
        if slide_from == "top":
            start_pos = QPoint(pos.x(), pos.y() - offset)
        elif slide_from == "bottom":
            start_pos = QPoint(pos.x(), pos.y() + offset)
        elif slide_from == "left":
            start_pos = QPoint(pos.x() - offset, pos.y())
        elif slide_from == "right":
            start_pos = QPoint(pos.x() + offset, pos.y())
        else:
            start_pos = QPoint(pos.x(), pos.y() - offset)

        self.move(start_pos)

        self.show()
        self.raise_()
        self.setFocus()

        self._show_anim_group.stop()
        self._slide_anim.setStartValue(start_pos)
        self._slide_anim.setEndValue(self._target_pos)
        self._show_anim_group.start()

    def hide(self):
        self._show_anim_group.stop()
        self.setWindowOpacity(0.0)
        super().hide()

    def focusOutEvent(self, event):
        """焦点离开时自动关闭"""
        self.focusOut.emit()
        self.hide()
        super().focusOutEvent(event)

    def sizeHint(self):
        return QSize(self.width(), self.content.sizeHint().height() + 24)
