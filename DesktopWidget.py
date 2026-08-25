from PyQt5.QtWidgets import*
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# QtWebEngine 必须在创建 QApplication 之前导入，并开启共享 OpenGL 上下文
# （否则浏览器初始化为插件时，要求先设置 AA_ShareOpenGLContexts）
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage  # noqa: F401
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    _HAS_WEBENGINE = True
except ImportError:
    _HAS_WEBENGINE = False

# 必须先创建 QApplication，再导入任何会用到 QFontDatabase 的模块
# （否则触发 "QFontDatabase: Must construct a QGuiApplication"）
app = QApplication([])
from pack.libs.fonts.SegoeAssets import *
from pack.libs.gui.Control import *
from pack.libs.gui.button import *
from pack.libs.gui.button.PopupMenuButton import *
from pack.libs.gui.lineedit import *
from pack.libs.gui.frame import *
from pack.libs.gui.label import *
from pack.libs.gui.shadow import *
from pack.libs.gui.widget import *

import pathlib
import subprocess
import re
import threading
import sys
import os

from SettingWidget import create_settings_window
from PerformanceMonitor import create_task_manager_window
from FileManager import create_file_manager_window
from Browser import create_browser_window
from TextEditor import create_editor_window
from TermWidget import create_terminal_window


# ----------------------------------------------------------------
#  桌面图标相关
# ----------------------------------------------------------------
def parse_app_config(text: str) -> dict:
    """解析 config.txt 的 `Key: value;` 格式"""
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        key, val = line.split(':', 1)
        result[key.strip()] = val.strip().rstrip(';').strip()
    return result


def find_app_icon(folder, icon_spec: str) -> str:
    """根据 ApplicationIcon 规格（如 /.ico）查找文件夹内的图标文件"""
    ext = None
    m = re.search(r'\.([A-Za-z0-9]+)', icon_spec or "")
    if m:
        ext = m.group(1).lower()
    if ext:
        for f in sorted(folder.iterdir()):
            if f.is_file() and f.suffix.lower() == "." + ext:
                return str(f)
    # 回退：找任意常见图片格式
    for f in sorted(folder.iterdir()):
        if f.is_file() and f.suffix.lower() in ('.ico', '.png', '.jpg', '.jpeg', '.bmp', '.svg'):
            return str(f)
    return ""


# ----------------------------------------------------------------
#  全局右键菜单（QMenu）现代样式
# ----------------------------------------------------------------
MENU_QSS = """
QMenu {
    background-color: #ffffff;
    border: 1px solid #f0f0f0;
    border-radius: 0px;
    padding: 4px;
}
QMenu::item {
    background-color: transparent;
    color: #000000;
    font-size: 11px;
    padding: 7px 22px 7px 12px;
    border-radius: 3px;
    margin: 1px 2px;
}
QMenu::item:selected {
    background-color: #eaeaea;
    color: #000000;
}
QMenu::item:disabled {
    color: #d4d4d4;
}
QMenu::separator {
    height: 1px;
    background: rgba(138, 138, 138, 1);
    margin: 5px 8px;
}
"""


def style_menu(menu: QMenu) -> QMenu:
    """为菜单应用统一现代化样式"""
    menu.setStyleSheet(MENU_QSS)
    menu.setAttribute(Qt.WA_TranslucentBackground, True)
    return menu


# -------------------------------------------------------------------
#  自定义 MsgBox 提示框（基于 Control.EMdiSubWindow，图标取自 pack/libs/gui/Theme/）
# -------------------------------------------------------------------
# Theme 图标目录：pack/libs/gui/Theme/（info.png / wran.png / error.png / node.png / logo.png）
THEME_DIR = pathlib.Path(__file__).resolve().parent / "pack" / "libs" / "gui" / "Theme"

# 各提示等级对应的主题图标
MSG_ICONS = {
    "info":    THEME_DIR / "info.png",
    "warning": THEME_DIR / "wran.png",   # 主题目录命名 wran.png
    "error":   THEME_DIR / "error.png",
    "question":THEME_DIR / "logo.png",   # 确认框用 logo 图标
    "node":    THEME_DIR / "node.png",
}

# 各提示等级的整体强调色（用于按钮/左侧色条）
MSG_COLORS = {
    "info":     "#5b7cfa",
    "warning":  "#e6c73f",
    "error":    "#e64343",
    "question": "#8a6cf0",
    "node":     "#8b95a8",
}


class MsgBox(EMdiSubWindow):
    """基于 Control.EMdiSubWindow 的 MDI 提示框（会注册到任务栏，带标题栏+图标）。

    用法：
        MsgBox.info(win, "标题", "正文")            # 提示
        MsgBox.warning(win, "标题", "正文")          # 警告
        MsgBox.error(win, "标题", "正文")            # 错误
        MsgBox.question(win, "标题", "正文", cb)     # 确认 → cb(bool)
        MsgBox.okcancel(win, "标题", "正文", cb)     # 确定/取消 → cb(bool)
    """

    def __init__(self, parent=None, title: str = "提示", text: str = "",
                 mode: str = "info", buttons: str = "ok", callback=None):
        icon_path = str(MSG_ICONS.get(mode, THEME_DIR / "info.png"))
        # 提示框固定大小，不可缩放/最大化，仅保留关闭按钮
        super().__init__(parent, title=title,
                         allow_resize=True, allow_maxmin_buttons=True,
                         icon_path=icon_path)

        self._mode = mode
        self._callback = callback

        self.resize(380, 200)
        self.setMinimumSize(380, 200)
        self.setMaximumSize(440, 320)

        # 标题栏强制白色文字（深色底）
        try:
            self.title_label.setStyleSheet("color:#ffffff; background:transparent;")
        except Exception:
            pass

        color = MSG_COLORS.get(mode, "#5b7cfa")
        icon = MSG_ICONS.get(mode, THEME_DIR / "info.png")

        # ---- 内容区 ----
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 10, 16, 12)
        lay.setSpacing(10)

        # 图标 + 正文
        body = QHBoxLayout()
        body.setSpacing(14)
        icon_label = QLabel()
        pix = QPixmap(str(icon)) if icon.exists() else QPixmap()
        if pix.isNull():
            pix = QPixmap(40, 40)
            pix.fill(Qt.transparent)
            p = QPainter(pix)
            p.setRenderHint(QPainter.Antialiasing)
            p.setBrush(QColor(color))
            p.setPen(Qt.NoPen)
            p.drawEllipse(2, 2, 36, 36)
            txt = (title or "!")[:1].upper()
            p.setPen(QColor("white"))
            p.setFont(QFont("Segoe UI", 18, QFont.Bold))
            p.drawText(pix.rect(), Qt.AlignCenter, txt)
            p.end()
        else:
            pix = pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(pix)
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignCenter)
        body.addWidget(icon_label, 0, Qt.AlignTop)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setObjectName("MsgText")
        text_label.setStyleSheet("color:#e6e8ee; font-size:13px; background:transparent;")
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.addWidget(text_label, 1)
        lay.addLayout(body)
        lay.addStretch()

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.accept_btn = QPushButton("确定")
        self.accept_btn.setStyleSheet(self._btn_qss(color))
        self.accept_btn.setCursor(Qt.PointingHandCursor)
        self.accept_btn.setFixedWidth(72)
        self.accept_btn.clicked.connect(lambda: self._finish(True))
        btn_row.addWidget(self.accept_btn)

        if buttons in ("okcancel", "yesno"):
            self.cancel_btn = QPushButton("取消" if buttons == "okcancel" else "否")
            self.cancel_btn.setStyleSheet(self._btn_qss("#55586a"))
            self.cancel_btn.setCursor(Qt.PointingHandCursor)
            self.cancel_btn.setFixedWidth(72)
            self.cancel_btn.clicked.connect(lambda: self._finish(False))
            btn_row.addWidget(self.cancel_btn)

            if buttons == "yesno":
                self.accept_btn.setText("是")

        lay.addLayout(btn_row)

        self.addWidget(content)

        # 提示框关闭即回收，避免残留（含确认框，回调在 _finish 里先执行）
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # 力保深色底 + 白色文字（覆盖系统浅色主题导致的白底白字）
        self.update_colors()

        # 居中到宿主窗口
        self._center_on_parent()

        # EMdiSubWindow 构造后是 hidden，必须显式 show；再做一次淡入动画
        QTimer.singleShot(0, self._register_and_show)
        self.show()

    def update_colors(self):
        """覆写：提示框始终深色背景（浅色系统主题下 Background 为白，会使白字不可见）。"""
        bg = QColor(30, 33, 45)
        self.normal_bg_color = bg
        self.hover_bg_color = bg
        self.pressed_bg_color = bg
        self.disabled_bg_color = bg
        # 内容区背景也强制深色
        if hasattr(self, 'main_Frame') and self.main_Frame is not None:
            self.main_Frame.setStyleSheet("background: transparent;")

    def _center_on_parent(self):
        """把提示框居中显示在宿主窗口中。"""
        parent = self.parent()
        if parent is None:
            return
        pw, ph = parent.width(), parent.height()
        w, h = self.width(), self.height()
        x = max(0, (pw - w) // 2)
        y = max(0, (ph - h) // 2)
        self.move(x, y)

    def _register_and_show(self):
        """覆写：提示框不注册到任务栏（瞬态小窗），仅做淡入显示。

        跳过 register_window 也就不会连接 destroyed->unregister_window，
        从根本上避免应用退出时访问已删除任务栏布局的崩溃。
        """
        self.play_show_animation()
        self._taskbar_registered = False

    @staticmethod
    def _btn_qss(base: str) -> str:
        """按钮样式：主色底 + hover/pressed 反馈"""
        return f"""
            QPushButton {{
                background: {base};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {base}; opacity: 0.85; }}
            QPushButton:pressed {{ background: {base}; }}
        """

    def _finish(self, ok: bool):
        """按钮确定：回调后关闭提示框。"""
        if self._callback is not None:
            try:
                self._callback(ok)
            except Exception as e:
                print("MsgBox 回调异常:", e)
        self.close_with_callback()

    # 便捷类方法
    @classmethod
    def info(cls, parent=None, title="提示", text=""):
        return cls(parent, title=title, text=text, mode="info", buttons="ok")

    @classmethod
    def warning(cls, parent=None, title="警告", text=""):
        return cls(parent, title=title, text=text, mode="warning", buttons="ok")

    @classmethod
    def error(cls, parent=None, title="错误", text=""):
        return cls(parent, title=title, text=text, mode="error", buttons="ok")

    @classmethod
    def question(cls, parent=None, title="确认", text="", callback=None,
                 ok_text="是", cancel_text="否"):
        """确认框：yes/no，结果通过 callback(bool) 返回。"""
        box = cls(parent, title=title, text=text, mode="question",
                  buttons="yesno", callback=callback)
        if ok_text:
            box.accept_btn.setText(ok_text)
        if cancel_text:
            box.cancel_btn.setText(cancel_text)
        return box

    @classmethod
    def okcancel(cls, parent=None, title="确认", text="", callback=None):
        """确定/取消：结果通过 callback(bool) 返回。"""
        return cls(parent, title=title, text=text, mode="node",
                   buttons="okcancel", callback=callback)



class DesktopButton(QWidget):
    """桌面图标：上方图标图片 + 下方文字，支持拖动、右键菜单、双击启动、选中"""

    # 网格参数：图标按网格吸附排列
    GRID_CELL_W = 84
    GRID_CELL_H = 94
    GRID_ORIGIN_X = 20
    GRID_ORIGIN_Y = 20

    selectedSignal = pyqtSignal(object, bool)   # (self, toggle)：点击时发出，toggle=Ctrl 多选
    rightClicked = pyqtSignal(object, QPoint)   # (self, global_pos)：右键时发出

    def __init__(self, parent, icon_path, name, process_name, folder=""):
        super().__init__(parent)
        self.process_name = process_name
        self.folder = folder
        self._selected = False
        self.setFixedSize(76, 88)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(2)

        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(48, 48)
        layout.addWidget(self.icon_label, 0, Qt.AlignHCenter)

        self.name_label = QLabel(name, self)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        self._set_icon(icon_path)
        self._drag_offset = None
        self.set_selected(False)

    def set_selected(self, selected):
        """设置选中态：选中时图标/文字加蓝色高亮"""
        self._selected = selected
        if selected:
            self.icon_label.setStyleSheet(
                "background: rgba(0,120,215,0.4);"
                "border:1px solid rgba(255,255,255,0.7); border-radius:2px;"
            )
            self.name_label.setStyleSheet(
                "background: rgba(0,120,215,0.8); color:#ffffff;"
                "font-size:11px; border-radius:2px;"
            )
        else:
            self.icon_label.setStyleSheet("background: transparent;")
            self.name_label.setStyleSheet(
                "color:#ffffff; font-size:11px; background:transparent;"
            )

    def _set_icon(self, icon_path):
        pix = QPixmap(icon_path) if (icon_path and pathlib.Path(icon_path).exists()) else QPixmap()
        if pix.isNull():
            pix = self._default_icon()
        self.icon_label.setPixmap(pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    @staticmethod
    def _default_icon():
        pix = QPixmap(48, 48)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(70, 130, 200))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(4, 4, 40, 40, 6, 6)
        p.setPen(QColor("white"))
        p.setFont(QFont("Segoe UI", 16, QFont.Bold))
        p.drawText(pix.rect(), Qt.AlignCenter, "A")
        p.end()
        return pix

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_offset = e.globalPos() - self.parent().mapToGlobal(self.pos())
            self.raise_()
            ctrl = bool(e.modifiers() & Qt.ControlModifier)
            self.selectedSignal.emit(self, ctrl)
        elif e.button() == Qt.RightButton:
            self.rightClicked.emit(self, e.globalPos())
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_offset is not None and (e.buttons() & Qt.LeftButton):
            new_global = e.globalPos() - self._drag_offset
            self.move(self.parent().mapFromGlobal(new_global))
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_offset = None
        self._snap_to_grid()   # 松开后吸附到网格
        super().mouseReleaseEvent(e)

    def _snap_to_grid(self):
        """把图标吸附到最近的空闲网格格点（不与其它图标重叠）"""
        p = self.pos()

        def cell_of(pos):
            col = round((pos.x() - self.GRID_ORIGIN_X) / self.GRID_CELL_W)
            row = round((pos.y() - self.GRID_ORIGIN_Y) / self.GRID_CELL_H)
            return max(0, col), max(0, row)

        # 收集其它可见图标已占用的格点
        parent = self.parent()
        occupied = set()
        if parent is not None:
            for child in parent.children():
                if (isinstance(child, DesktopButton) and child is not self
                        and not child.isHidden()):
                    occupied.add(cell_of(child.pos()))

        col, row = cell_of(p)
        target = (col, row)

        # 目标格点被占用时，螺旋向外搜索最近的空闲格点
        if target in occupied:
            radius = 1
            while radius <= 100:
                best = None
                best_dist = None
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if max(abs(dx), abs(dy)) != radius:
                            continue
                        c = (col + dx, row + dy)
                        if c[0] < 0 or c[1] < 0:
                            continue
                        if c in occupied:
                            continue
                        d = abs(dx) + abs(dy)
                        if best is None or d < best_dist:
                            best, best_dist = c, d
                if best is not None:
                    target = best
                    break
                radius += 1

        x = self.GRID_ORIGIN_X + target[0] * self.GRID_CELL_W
        y = self.GRID_ORIGIN_Y + target[1] * self.GRID_CELL_H
        self.move(x, y)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._launch()
        super().mouseDoubleClickEvent(e)

    # ---------- 右键菜单 / 启动 ----------
    def _launch(self):
        """双击启动：独立线程中检测入口；含 MainWidget 时用 EMdiSubWindow 显示，否则独立进程"""
        folder = pathlib.Path(self.folder)
        main_py = folder / "main.py"
        if not main_py.exists():
            MsgBox.error(self.window(), "启动失败",
                         f"未找到入口文件:\n{main_py}")
            return

        def run():
            try:
                if self._has_main_widget(main_py):
                    # 有 MainWidget：回主线程用 EMdiSubWindow 显示（QWidget 必须主线程）
                    QMetaObject.invokeMethod(
                        self, "_show_mdi_widget", Qt.QueuedConnection,
                        Q_ARG(str, str(main_py)),
                    )
                else:
                    # 无 MainWidget：独立进程启动，并监控其退出状态
                    proc = subprocess.Popen(
                        [sys.executable, str(main_py)],
                        cwd=str(folder),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True,
                    )
                    stdout, stderr = proc.communicate()
                    code = proc.returncode
                    # 仅当进程「因错误退出」（正整数退出码）才弹窗；
                    # 正常结束(0) 或 被用户终止(负数信号) 不弹窗。
                    if code is not None and code > 0:
                        raw = (stderr or stdout or b"")
                        log = raw.decode("utf-8", errors="replace").strip()
                        msg = (f"进程异常退出（退出码 {code}）:\n\n{log}"
                               if log else
                               f"进程异常退出（退出码 {code}）。")
                        QMetaObject.invokeMethod(
                            self, "_show_error_msgbox", Qt.QueuedConnection,
                            Q_ARG(str, msg),
                        )
            except Exception:
                # 线程内不能直接创建 QWidget，回主线程弹 MsgBox 显示错误日志
                import traceback
                QMetaObject.invokeMethod(
                    self, "_show_error_msgbox", Qt.QueuedConnection,
                    Q_ARG(str, traceback.format_exc()),
                )

        threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(str)
    def _show_error_msgbox(self, msg):
        """主线程：弹出 MsgBox 显示运行错误日志"""
        MsgBox.error(self.window(), "启动失败", msg)

    @staticmethod
    def _has_main_widget(main_py) -> bool:
        """静态检测 main.py 源文件内是否定义 MainWidget 类"""
        try:
            import ast
            src = pathlib.Path(main_py).read_text(encoding="utf-8")
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "MainWidget":
                    return True
            return False
        except Exception:
            return False

    @pyqtSlot(str)
    def _show_mdi_widget(self, main_py):
        """主线程：动态导入 main.py 的 MainWidget 并用 EMdiSubWindow 显示，内容自适应窗口大小"""
        import importlib.util

        # 把 main.py 所在目录及其父目录临时加入 sys.path，
        # 支持 main.py 内部两种导入：
        #   1) 相对导入：from pack.libs import ...            （需要 main.py 所在目录）
        #   2) 包导入：  from HelloWorld.pack.libs import ...  （需要父目录，使 HelloWorld 成为包）
        main_path = pathlib.Path(main_py)
        for _d in (str(main_path.parent), str(main_path.parent.parent)):
            if _d not in sys.path:
                sys.path.insert(0, _d)

        try:
            spec = importlib.util.spec_from_file_location("_app_main", main_py)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception:
            import traceback
            MsgBox.error(self.window(), "启动失败",
                         f"导入模块失败:\n{traceback.format_exc()}")
            return

        MainWidget = getattr(module, "MainWidget", None)
        if MainWidget is None:
            MsgBox.error(self.window(), "启动失败",
                         "未在入口文件中找到 MainWidget 类。")
            return

        try:
            widget = MainWidget()
        except Exception:
            import traceback
            MsgBox.error(self.window(), "启动失败",
                         f"实例化 MainWidget 失败:\n{traceback.format_exc()}")
            return

        top = self.window()

        # 从 MainWidget 读取窗口配置（类属性优先，缺失用默认值）
        title = getattr(widget, "WINDOW_TITLE", None) or self.name_label.text()
        size = getattr(widget, "WINDOW_SIZE", None)
        resizable = getattr(widget, "WINDOW_RESIZABLE", True)
        maxmin = getattr(widget, "WINDOW_MAXMIN", True)

        win = EMdiSubWindow(top, title, allow_maxmin_buttons=maxmin, allow_resize=resizable)

        # 窗口尺寸：优先 WINDOW_SIZE，否则用 MainWidget 的 sizeHint，最后默认 640x480
        if size and len(size) == 2:
            win.resize(int(size[0]), int(size[1]))
        else:
            sx = widget.sizeHint()
            if sx.isValid() and sx.width() > 0:
                win.resize(max(sx.width(), 320), max(sx.height() + 30, 200))
            else:
                win.resize(640, 480)

        win.addWidget(widget)   # addWidget 使其自适应窗口大小
        win.show()
        win.raise_()

    def _open_folder(self):
        """右键「打开所在目录」：用内置文件管理器（FileManagerWidget）打开该目录"""
        from FileManager import create_file_manager_window
        top = self.window()
        win = create_file_manager_window(top, start_dir=str(pathlib.Path(self.folder)))
        ww, hh = 760, 520
        x = max(0, (top.width() - ww) // 2)
        y = max(0, (top.height() - hh) // 2)
        win.setGeometry(x, y, ww, hh)
        win.show()
        win.raise_()


class DesktopWidget(QMainWindow):
    _iconReady = pyqtSignal(str, str, str, str)   # (icon_path, icon_name, process_name, folder)

    # 桌面图标根目录：程序当前目录下的 /Desktop（Linux / Windows 通用）
    DESKTOP_DIR = pathlib.Path(__file__).resolve().parent / "Desktop"

    def __init__ (self, parent : QWidget = None):
        super().__init__(parent)
        self._iconReady.connect(self._on_icon_ready)

        screen = QDesktopWidget().screenGeometry()
        width = screen.width()
        height = screen.height()
        
        # 设置窗口铺满屏幕
        self.move(0,0)
        self.setWindowTitle("RockQuant System")
        self.resize(width, height)

        self._initgui()

        # 桌面图标网格
        self._desktop_buttons = []
        self._selected_icons = []
        self._grid_rows = max(1, (self.height() - DesktopButton.GRID_ORIGIN_Y * 2) // DesktopButton.GRID_CELL_H)
        self._load_desktop_icons()
    def _initgui(self):
        # 壁纸控件：整屏背景图
        self.main_widget = ImageWidget(
            image = str(pathlib.Path(__file__).resolve().parent / "background.jpg"),
            parent = self,
        )
        self.setCentralWidget(self.main_widget)

        # 任务栏：使用 Control.ETaskBar（内部自带 TaskBarWindowManager 单例）
        self.TaskBar = ETaskBar(self)
        self.TaskBar.setFixedHeight(40)
        self._build_taskbar()
        self._build_start_menu()

        # 壁纸右键菜单
        self._build_context_menu()

    def _build_context_menu(self):
        """使用 Qt 自带的 QMenu 作为壁纸右键菜单（轻量，节省单板机资源）"""
        # 使用 CustomContextMenu 策略：Qt 会自动把右键转换为 customContextMenuRequested 信号
        self.main_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.main_widget.customContextMenuRequested.connect(self._show_context_menu)

        # Qt 原生菜单（轻量）+ 现代化样式
        self.context_menu = style_menu(QMenu(self))
        action = self.context_menu.addAction("打开终端")
        action.triggered.connect(lambda: self._launch_app("terminal"))
        self.context_menu.addAction("刷新壁纸")
        refresh_icons_act = self.context_menu.addAction("刷新")
        refresh_icons_act.triggered.connect(self._refresh_desktop_icons)
        self.context_menu.addSeparator()
        reboot_act = self.context_menu.addAction("重启")
        reboot_act.triggered.connect(self._reboot)
        power_act = self.context_menu.addAction("关机")
        power_act.triggered.connect(self._power_off)

    def _show_context_menu(self, pos):
        """在右键点击处弹出原生菜单"""
        self.context_menu.exec_(self.main_widget.mapToGlobal(pos))

    # ----------------------------------------------------------------
    # 任务栏（全部使用 QPushButton + 样式表，轻量、节省单板机资源）
    # ----------------------------------------------------------------

    def _build_taskbar(self):
        """构建任务栏：开始按钮 + 任务按钮（从左侧开始排列）；时钟独立定位在右下角"""
        self.TaskBar.addButton("开始", 72, lambda: self._toggle_start_menu())

        # 任务栏右键菜单（收纳任务管理器等操作）
        self._build_taskbar_context_menu()

        # 时钟直接创建在窗口上，右下角实时定位（见 resizeEvent）
        self._build_taskbar_clock()

    def _build_taskbar_clock(self):
        """在窗口右下角创建实时时钟（独立于任务栏布局）"""
        self.clock_label = QLabel(self)
        self.clock_label.setAlignment(Qt.AlignCenter)
        self.clock_label.setStyleSheet(
            "color:#ffffff;"  # 深色主题：白字
            "font-size:12px; background:transparent; padding:0 10px;"
        )
        self.clock_label.adjustSize()
        self._update_clock()
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._place_clock()

    def _update_clock(self):
        now = QDateTime.currentDateTime()
        time_str = now.toString("HH:mm")
        date_str = now.toString("M月d日")
        self.clock_label.setText(f"{date_str}  {time_str}")
        self.clock_label.adjustSize()

    def _place_clock(self):
        """把时钟定位到窗口右下角（任务栏右端之上）"""
        if not getattr(self, 'clock_label', None):
            return
        cw = self.clock_label.width()
        ch = self.clock_label.height()
        tb_h = 40  # 任务栏高度
        x = self.width() - cw - 10
        y = self.height() - tb_h + (tb_h - ch) // 2
        self.clock_label.move(x, y)
        self.clock_label.raise_()

    def _build_taskbar_context_menu(self):
        """任务栏右键菜单"""
        self.TaskBar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.TaskBar.customContextMenuRequested.connect(self._show_taskbar_menu)

        self.taskbar_menu = style_menu(QMenu(self))
        task_mgr_act = self.taskbar_menu.addAction("任务管理器")
        task_mgr_act.triggered.connect(self.open_task_manager_window)

    def _show_taskbar_menu(self, pos):
        self.taskbar_menu.exec_(self.TaskBar.mapToGlobal(pos))

    def new_window(self, title: str = "新窗口"):
        """创建并显示一个 MDI 子窗口（自动注册到任务栏，按钮文字 = 窗口标题）
        使用级联偏移定位，避免多个窗口堆叠在同一个位置。"""
        win = EMdiSubWindow(self, title,
                            allow_maxmin_buttons=True, allow_resize=True)
        w, h = 680, 480

        # 级联偏移：每次向右下错开 40px，超出边界后回到左上附近
        cascade = getattr(self, '_window_cascade', 0)
        step = 40
        x = 60 + (cascade * step) % max(1, self.width() - w - 60)
        y = 60 + (cascade * step) % max(1, self.height() - h - 60 - 40)
        self._window_cascade = cascade + 1

        win.setGeometry(x, y, w, h)
        win.show()
        win.raise_()
        self._last_window = win
        return win

    # ----------------------------------------------------------------
    # 开始菜单面板（普通 QFrame 浮层，轻量）
    # ----------------------------------------------------------------

    def _build_start_menu(self):
        """构建开始菜单面板：应用列表 + 底部电源操作"""
        self.start_menu = QFrame(self)
        self.start_menu.setObjectName("StartMenu")
        self.start_menu.setAttribute(Qt.WA_StyledBackground, True)

        # 深色主题：固定深色底 + 白字
        bg  = "rgba(28,31,44,0.96)"
        col = "#ffffff"

        self.start_menu.setStyleSheet(f"""
            QFrame#StartMenu {{
                background-color: {bg};
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 10px;
            }}
            QLabel {{ color: {col}; font-size: 13px; }}
            QPushButton {{
                background: transparent;
                color: {col};
                border: none;
                border-radius: 6px;
                font-size: 13px;
                text-align: left;
                padding: 8px 12px;
            }}
            QPushButton:hover   {{ background: rgba(91,124,250,0.35); }}
            QPushButton:pressed {{ background: rgba(91,124,250,0.5); }}
        """)
        self.start_menu.setFixedSize(260, 320)

        layout = QVBoxLayout(self.start_menu)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(4)

        # 标题
        title = QLabel("应用", self.start_menu)
        title.setStyleSheet("font-size:14px; font-weight:bold;")
        layout.addWidget(title)

        # 应用按钮列表
        apps = [("终端", "terminal"), ("文件管理器", "files"),
                ("浏览器", "browser"), ("设置", "settings"),
                ("文本编辑器", "editor")]
        for text, key in apps:
            b = QPushButton(text, self.start_menu)
            b.clicked.connect(lambda checked, k=key: self._launch_app(k))
            layout.addWidget(b)

        layout.addStretch(1)

        # 分隔线（用 1px QFrame）
        line = QFrame(self.start_menu)
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: rgba(128,128,128,0.4);")
        layout.addWidget(line)

        # 底部电源操作
        power_row = QHBoxLayout()
        reboot_btn = QPushButton("重启", self.start_menu)
        reboot_btn.clicked.connect(self._reboot)
        power_btn  = QPushButton("关机", self.start_menu)
        power_btn.clicked.connect(self._power_off)
        power_row.addWidget(reboot_btn)
        power_row.addWidget(power_btn)
        layout.addLayout(power_row)

        self.start_menu.hide()

        # 点击面板外部自动关闭
        QApplication.instance().installEventFilter(self)

    def _toggle_start_menu(self):
        if self.start_menu.isVisible():
            self.start_menu.hide()
        else:
            self._show_start_menu()

    def _show_start_menu(self):
        """在任务栏左端上方弹出开始菜单"""
        p = self.mapFromGlobal(self.TaskBar.mapToGlobal(QPoint(0, 0)))
        x = p.x()
        y = p.y() - self.start_menu.height()
        self.start_menu.move(x, y)
        self.start_menu.show()
        self.start_menu.raise_()

    def eventFilter(self, obj, event):
        """点击开始菜单外部时关闭菜单"""
        if (self.start_menu.isVisible()
                and event.type() == QEvent.MouseButtonPress):
            global_pos = event.globalPos()
            in_menu = self.start_menu.rect().contains(
                self.start_menu.mapFromGlobal(global_pos))
            if not in_menu:
                self.start_menu.hide()
        return super().eventFilter(obj, event)

    # ----------------------------------------------------------------
    # 功能处理（纯 Qt / 系统命令，避免额外依赖）
    # ----------------------------------------------------------------

    def _launch_app(self, key: str):
        """根据 key 启动对应应用"""
        # 内置应用：打开内部窗口，而非外部命令
        builtin = {
            "settings":  self.open_settings_window,
            "files":     self.open_file_manager_window,
            "browser":   self.open_browser_window,
            "editor":    self.open_editor_window,
            "terminal":  self.open_terminal_window,
        }
        if key in builtin:
            builtin[key]()
            self.start_menu.hide()
            return

        self._launch_external(key)
        self.start_menu.hide()

    def _launch_external(self, key: str):
        """按平台启动外部应用（Linux 用 xterm/xdg-open，Windows 用对应原生命令）"""
        if key == "terminal":
            cmd = ["xterm", "-e", "/bin/bash"] if not sys.platform.startswith("win") \
                else ["cmd", "/k"]
        else:
            return

        try:
            subprocess.Popen(cmd, start_new_session=True)
        except Exception as e:
            print("启动应用失败:", e)

    def _open_with_default(self, path_or_url: str):
        """用系统默认方式打开文件/URL（跨平台）"""
        try:
            if sys.platform.startswith("win"):
                os.startfile(path_or_url)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path_or_url], start_new_session=True)
        except Exception as e:
            print("打开失败:", e)

    def open_settings_window(self):
        """打开内部设置窗口（Windows 风格，已在任务栏注册）"""
        w = getattr(self, '_settings_window', None)
        if w is not None and w.isVisible():
            w.raise_()
            return w

        win = create_settings_window(self)
        ww, hh = 720, 480
        x = max(0, (self.width() - ww) // 2)
        y = max(0, (self.height() - hh) // 2)
        win.setGeometry(x, y, ww, hh)
        win.show()
        win.raise_()
        self._settings_window = win

        # 连接设置面板的个性化信号：把壁纸/强调色作用到本桌面（而非系统桌面）
        content = getattr(win, "_settings_content", None)
        if content is not None:
            content.wallpaperApplyRequested.connect(self._apply_setting_wallpaper)
            content.accentApplyRequested.connect(self._apply_setting_accent)
        return win

    # ----------------------------------------------------------------
    # 个性化应用（来自设置面板）
    # ----------------------------------------------------------------
    def _apply_setting_wallpaper(self, path: str):
        """把壁纸应用到内置桌面 main_widget。"""
        if hasattr(self, "main_widget") and path:
            try:
                self.main_widget.load_image(path)
            except Exception as e:
                print("应用壁纸失败:", e)

    def _apply_setting_accent(self, color: QColor):
        """把强调色应用到任务栏（背景 + 文字）。"""
        if not hasattr(self, "TaskBar") or not color.isValid():
            return
        bg = color.name()
        # 计算可读文字颜色：色彩亮度较高时用深色文字，否则用白色
        text = "#101010" if color.lightness() > 150 else "#ffffff"
        self.TaskBar.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                color: {text};
            }}
        """)

    def open_task_manager_window(self):
        """打开任务管理器窗口（性能监视，本机监控）"""
        w = getattr(self, '_task_manager_window', None)
        if w is not None and w.isVisible():
            w.raise_()
            return w

        win = create_task_manager_window(self)
        ww, hh = 760, 520
        x = max(0, (self.width() - ww) // 2)
        y = max(0, (self.height() - hh) // 2)
        win.setGeometry(x, y, ww, hh)
        win.show()
        win.raise_()
        self._task_manager_window = win
        return win

    def open_file_manager_window(self):
        """打开文件管理器窗口（仿 Linux，已在任务栏注册）"""
        w = getattr(self, '_file_manager_window', None)
        if w is not None and w.isVisible():
            w.raise_()
            return w

        win = create_file_manager_window(self)
        ww, hh = 760, 520
        x = max(0, (self.width() - ww) // 2)
        y = max(0, (self.height() - hh) // 2)
        win.setGeometry(x, y, ww, hh)
        win.show()
        win.raise_()
        self._file_manager_window = win
        return win

    def open_browser_window(self):
        """打开浏览器窗口（内置，已在任务栏注册）"""
        w = getattr(self, '_browser_window', None)
        if w is not None and w.isVisible():
            w.raise_()
            return w

        win = create_browser_window(self)
        ww, hh = 860, 560
        x = max(0, (self.width() - ww) // 2)
        y = max(0, (self.height() - hh) // 2)
        win.setGeometry(x, y, ww, hh)
        win.show()
        win.raise_()
        self._browser_window = win
        return win

    def open_editor_window(self):
        """打开文本编辑器窗口（内置，已在任务栏注册）"""
        w = getattr(self, '_editor_window', None)
        if w is not None and w.isVisible():
            w.raise_()
            return w

        win = create_editor_window(self)
        ww, hh = 720, 500
        x = max(0, (self.width() - ww) // 2)
        y = max(0, (self.height() - hh) // 2)
        win.setGeometry(x, y, ww, hh)
        win.show()
        win.raise_()
        self._editor_window = win
        return win

    def open_terminal_window(self):
        """打开终端窗口（Linux 用 py3qterm，Windows 模拟）"""
        w = getattr(self, '_terminal_window', None)
        if w is not None and w.isVisible():
            w.raise_()
            return w

        win = create_terminal_window(self)
        ww, hh = 720, 500
        x = max(0, (self.width() - ww) // 2)
        y = max(0, (self.height() - hh) // 2)
        win.setGeometry(x, y, ww, hh)
        win.show()
        win.raise_()
        self._terminal_window = win
        return win

    # ----------------------------------------------------------------
    # 桌面图标（多线程扫描 Desktop/ 下的 config.txt）
    # ----------------------------------------------------------------
    def _refresh_desktop_icons(self):
        """刷新桌面图标：先清空当前图标，再重新扫描 Desktop/。"""
        # 清除当前已有图标
        for btn in list(self._desktop_buttons):
            if btn in self._selected_icons:
                self._selected_icons.remove(btn)
            btn.setParent(None)
            btn.deleteLater()
        self._desktop_buttons = []
        self._selected_icons = []
        # 重新扫描加载
        self._load_desktop_icons()

    def _load_desktop_icons(self):
        """后台线程扫描 Desktop/ 下每个子文件夹的 config.txt，解析出桌面图标"""
        def worker():
            desktop_dir = self.DESKTOP_DIR
            if not desktop_dir.exists():
                return
            for folder in sorted(desktop_dir.iterdir()):
                if not folder.is_dir():
                    continue
                cfg = folder / "config.txt"
                if not cfg.exists():
                    continue
                try:
                    text = cfg.read_text(encoding="utf-8")
                except Exception:
                    continue
                data = parse_app_config(text)
                # ApplicationName: "进程名" | "桌面图标名";
                name_raw = data.get("ApplicationName", "")
                parts = [p.strip().strip('"').strip() for p in name_raw.split('|')]
                process_name = parts[0] if parts else folder.name
                icon_name = parts[1] if len(parts) > 1 else process_name
                icon_path = find_app_icon(folder, data.get("ApplicationIcon", ""))
                self._iconReady.emit(icon_path, icon_name, process_name, str(folder))

        threading.Thread(target=worker, daemon=True).start()

    def _on_icon_ready(self, icon_path, icon_name, process_name, folder):
        """主线程：在桌面网格中添加一个图标"""
        btn = DesktopButton(self.main_widget, icon_path, icon_name, process_name, folder)
        btn.selectedSignal.connect(self._on_icon_selected)
        btn.rightClicked.connect(self._on_icon_right_click)
        n = len(self._desktop_buttons)
        col = n // self._grid_rows
        row = n % self._grid_rows
        x = DesktopButton.GRID_ORIGIN_X + col * DesktopButton.GRID_CELL_W
        y = DesktopButton.GRID_ORIGIN_Y + row * DesktopButton.GRID_CELL_H
        btn.move(x, y)
        btn.show()
        self._desktop_buttons.append(btn)

    def _on_icon_selected(self, btn, toggle=False):
        """选中处理：toggle=True（Ctrl+点击）切换单个，否则单选"""
        if toggle:
            if btn in self._selected_icons:
                self._selected_icons.remove(btn)
                btn.set_selected(False)
            else:
                self._selected_icons.append(btn)
                btn.set_selected(True)
        else:
            for b in self._desktop_buttons:
                b.set_selected(b is btn)
            self._selected_icons = [btn] if btn is not None else []

    def _on_icon_right_click(self, btn, global_pos):
        """右键图标：根据选中数量弹出菜单"""
        # 右键未选中的图标时，先单选它
        if btn not in self._selected_icons:
            self._on_icon_selected(btn, toggle=False)

        menu = style_menu(QMenu(self))
        if len(self._selected_icons) > 1:
            batch_open = menu.addAction("批量打开")
            batch_open.triggered.connect(self._batch_open)
            menu.addSeparator()
            delete_act = menu.addAction("删除")
            delete_act.triggered.connect(self._delete_selected)
        else:
            open_act = menu.addAction("打开")
            open_act.triggered.connect(btn._launch)
            locate_act = menu.addAction("打开所在目录")
            locate_act.triggered.connect(btn._open_folder)
            menu.addSeparator()
            delete_act = menu.addAction("删除")
            delete_act.triggered.connect(self._delete_selected)
        menu.exec(global_pos)

    def _batch_open(self):
        """批量打开所有选中的图标"""
        for btn in list(self._selected_icons):
            btn._launch()

    def _delete_selected(self):
        """删除选中的桌面图标（从桌面移除，不删除磁盘文件）"""
        if not self._selected_icons:
            return
        # 用 MDI 提示框确认（callback 形式返回是否继续）
        MsgBox.question(
            self, "删除",
            f"确定删除选中的 {len(self._selected_icons)} 个图标吗？",
            callback=self._do_delete_selected,
        )

    def _do_delete_selected(self, ok: bool):
        """确认后的实际删除动作（由 MsgBox 回调触发）。"""
        if not ok:
            return
        for btn in list(self._selected_icons):
            if btn in self._desktop_buttons:
                self._desktop_buttons.remove(btn)
            btn.setParent(None)
            btn.deleteLater()
        self._selected_icons = []

    def _power_off(self):
        self.start_menu.hide()
        if sys.platform.startswith("win"):
            cmd = ["shutdown", "/s", "/t", "0"]
        else:
            cmd = ["systemctl", "poweroff"]
        try:
            subprocess.Popen(cmd, start_new_session=True)
        except Exception as e:
            print("关机失败:", e)

    def _reboot(self):
        self.start_menu.hide()
        if sys.platform.startswith("win"):
            cmd = ["shutdown", "/r", "/t", "0"]
        else:
            cmd = ["systemctl", "reboot"]
        try:
            subprocess.Popen(cmd, start_new_session=True)
        except Exception as e:
            print("重启失败:", e)

    def resizeEvent(self,event):

        self.TaskBar.setFixedSize(self.width(),40)
        self.TaskBar.move(0,self.height()-40)
        self.TaskBar.raise_()   # 置顶显示于壁纸之上

        # 时钟跟随窗口大小实时定位到右下角
        self._place_clock()

        # 窗口变化时重新定位开始菜单
        if getattr(self, 'start_menu', None) and self.start_menu.isVisible():
            self._show_start_menu()

        super().resizeEvent(event)

if __name__ == "__main__":

    win = DesktopWidget()
    win.show()
    app.exec()
        