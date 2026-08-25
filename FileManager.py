from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import sys
import shutil
import pathlib
from datetime import datetime

from pack.libs.gui.Control import EMdiSubWindow
from pack.libs.gui.RippleButton import *



ICON_QSS = """
QListWidget {
    background: #transparent;          /* 显式深色，避免 viewport 显示系统浅色 */
    border: none;
    outline: none;
    icon-size: 20px;
}
QListWidget::item {
    border-radius: 3px;
    padding: 3px 6px;
    color: #ffffff;
    min-height: 28px;
}
QListWidget::item:hover      { background: rgba(255,255,255,0.06); }
QListWidget::item:selected   { background: #6b6b6b; }
QListWidget::item:selected:hover { background: #505050; }
QScrollBar:vertical, QScrollBar:horizontal {
    background: #2a2a2a; width: 10px; height: 10px;
    border: none; margin: 0;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #414141; border-radius: 5px; min-height: 30px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #565656;
}
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""

# 文件管理器右键菜单样式
MENU_QSS = """
QMenu {
    background-color: #1F1F1F;
    border: 1px solid #2c2c2c;
    border-radius: 0px;
    padding: 6px;
}
QMenu::item {
    background-color: transparent;
    color: #f2f3f7;
    font-size: 13px;
    padding: 7px 22px 7px 12px;
    border-radius: 3px;
    margin: 1px 2px;
}
QMenu::item:selected { background-color: #494949; color: #ffffff; }
QMenu::item:disabled { color: #6b7280; }
QMenu::separator {
    height: 1px;
    background: rgba(95, 95, 95, 0.12);
    margin: 5px 8px;
}
"""


class FileManagerWidget(QWidget):
    """仿 Linux 文件资源管理器：左侧位置栏 + 路径导航 + 右侧文件列表 + 状态栏。"""

    def __init__(self, parent=None, start_dir=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)  # 让 QWidget 背景 QSS 生效
        self._history = []          # 已访问路径栈
        self._history_index = -1
        self._open_apps = {}        # 已打开的应用窗口缓存
        self._clipboard = {"paths": [], "cut": False}  # 复制/剪切剪贴板
 
        self._init_ui()
        self._apply_style()

        home = start_dir or self._home_dir()
        self._navigate(home)

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------
    @staticmethod
    def _home_dir() -> str:
        return str(pathlib.Path.home())

    @staticmethod
    def _is_dir(path: str) -> bool:
        try:
            return os.path.isdir(path)
        except OSError:
            return False

    def _standard_dirs(self) -> list:
        """常用位置：[显示名, 绝对路径]"""
        home = pathlib.Path.home()
        items = [
            ("主目录", str(home)),
            ("桌面", str(home / "Desktop")),
            ("文档", str(home / "Documents")),
            ("下载", str(home / "Downloads")),
            ("图片", str(home / "Pictures")),
            ("音乐", str(home / "Music")),
            ("视频", str(home / "Videos")),
        ]
        return [(n, p) for n, p in items if self._is_dir(p) or n == "主目录"]

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ---------- 顶部：导航工具条 + 路径栏 ----------
        top = QHBoxLayout()
        top.setSpacing(0)

        class SegoeMDL2Assets:
            font_db = QFontDatabase()
            font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "segmdl2.ttf")
            if os.path.exists(font_path):
                font_id = font_db.addApplicationFont(font_path)
                if font_id != -1:
                    families = font_db.applicationFontFamilies(font_id)
                    if families:
                        font = QFont(families[0], 11)
                    else:
                        font = QFont("Segoe MDL2 Assets", 11)
                else:
                    font = QFont("Segoe MDL2 Assets", 11)
            else:
                font = QFont("Segoe MDL2 Assets", 11)

        self.btn_back = RippleButton()
        self.btn_back.setFixedWidth(30)
        self.btn_back.setText("\ue09a")
        self.btn_back.setFont(SegoeMDL2Assets.font)
        self.btn_back.setToolTip("后退")
        self.btn_back.clicked.connect(self._go_back)
        top.addWidget(self.btn_back)

        self.btn_forward = RippleButton()
        self.btn_forward.setFixedWidth(30)
        self.btn_forward.setText("\ue09b")
        self.btn_forward.setFont(SegoeMDL2Assets.font)
        self.btn_forward.setToolTip("前进")
        self.btn_forward.clicked.connect(self._go_forward)
        top.addWidget(self.btn_forward)

        self.btn_up = RippleButton()
        self.btn_up.setFixedWidth(30)
        self.btn_up.setText("\ue110")
        self.btn_up.setFont(SegoeMDL2Assets.font)
        self.btn_up.setToolTip("上级目录")
        self.btn_up.clicked.connect(self._go_up)
        top.addWidget(self.btn_up)

        self.btn_home = RippleButton()
        self.btn_home.setFixedWidth(30)
        self.btn_home.setText("\ue80f")
        self.btn_home.setFont(SegoeMDL2Assets.font)
        self.btn_home.setToolTip("主目录")
        self.btn_home.clicked.connect(self._go_home)
        top.addWidget(self.btn_home)

        self.btn_refresh = RippleButton()
        self.btn_refresh.setFixedWidth(30)
        self.btn_refresh.setText("\ue149")
        self.btn_refresh.setFont(SegoeMDL2Assets.font)
        self.btn_refresh.setToolTip("刷新")
        self.btn_refresh.clicked.connect(self._reload)
        top.addWidget(self.btn_refresh)

        # 路径栏（面包屑按钮）
        self.path_bar = QFrame()
        self.path_bar.setObjectName("PathBar")
        self.path_layout = QHBoxLayout(self.path_bar)
        self.path_layout.setContentsMargins(8, 0, 8, 0)
        self.path_layout.setSpacing(2)
        top.addWidget(self.path_bar, 1)

        root.addLayout(top)

        # ---------- 中部分隔：左侧位置栏 + 右侧文件列表 ----------
        middle = QHBoxLayout()
        middle.setSpacing(6)

        # 左侧「位置」栏
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(150)
        side_lay = QVBoxLayout(self.sidebar)
        side_lay.setContentsMargins(6, 8, 6, 8)
        side_lay.setSpacing(2)

        side_title = QLabel("位置")
        side_title.setStyleSheet("color:#9aa3b2; font-size:11px; ")
        side_lay.addWidget(side_title)

        self.side_list = QListWidget()
        self.side_list.setObjectName("SideList")
        self.side_list.setIconSize(QSize(18, 18))
        self.side_list.itemClicked.connect(self._on_side_clicked)
        for name, path in self._standard_dirs():
            it = QListWidgetItem("  " + name)
            it.setData(Qt.UserRole, path)
            self.side_list.addItem(it)
        side_lay.addWidget(self.side_list, 1)

        middle.addWidget(self.sidebar)

        # 右侧文件列表（列表视图：每行一个文件，图标 + 名称）
        self.file_list = QListWidget()
        self.file_list.setViewMode(QListView.ListMode)
        self.file_list.setResizeMode(QListView.Adjust)
        self.file_list.setMovement(QListView.Static)
        self.file_list.setWordWrap(False)
        self.file_list.itemDoubleClicked.connect(self._on_item_activated)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_file_menu)
        self.file_list.setIconSize(QSize(20, 20))
        self.file_list.setStyleSheet(ICON_QSS)
        middle.addWidget(self.file_list, 1)

        root.addLayout(middle, 1)

        # ---------- 底部状态栏 ----------
        self.status = QLabel("")
        self.status.setObjectName("StatusBar")
        self.status.setFixedHeight(22)
        root.addWidget(self.status)

    # ------------------------------------------------------------------
    # 样式
    # ------------------------------------------------------------------
    def _apply_style(self):
        self.setStyleSheet("""
            QWidget, QFrame, QListWidget, QListView, QAbstractItemView {
                background: #1f1f1f;
                color: #e8eaf0;
                font-size: 13px;
            }
            QToolButton {
                background: rgba(255,255,255,0.05);
                border: none; border-radius: 2px;
                color: #e8eaf0; font-size: 15px;
                padding: 4px 8px;
            }
            QToolButton:hover  { background: rgba(255,255,255,0.12); }
            QToolButton:pressed{ background: #1f1f1f; }
            QFrame#PathBar, QFrame#Sidebar {
                background: #1f1f1f;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
            }
            QPushButton#Crumb {
                background: transparent; border: none; border-radius: 4px;
                color: #cccccc; padding: 3px 6px;
            }
            QPushButton#Crumb:hover { background: rgba(255,255,255,0.10); color: #ffffff; }
            QListWidget#SideList {
                background: transparent; border: none; outline: none;
            }
            QListWidget#SideList::item {
                border-radius: 0px; padding: 5px; color: #cccccc;
            }
            QListWidget#SideList::item:hover    { background: rgba(255,255,255,0.07); }
            QListWidget#SideList::item:selected { background: #272727;border-left : 1px solid #0091ff;}
            QLabel#StatusBar { color: #9aa3b2; padding-left: 4px; }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #434343; width: 10px; height: 10px;
                border: none; margin: 0;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #434343; border-radius: 5px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #434343;
            }
            QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
            QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
        """)

    # ------------------------------------------------------------------
    # 导航
    # ------------------------------------------------------------------
    def _navigate(self, path: str):
        """进入指定目录，并刷新列表与路径栏。"""
        if not self._is_dir(path):
            return
        real = os.path.realpath(path)

        # 记录历史
        self._history = self._history[: self._history_index + 1]
        self._history.append(real)
        self._history_index = len(self._history) - 1

        self._reload()

    def _reload(self):
        """重新加载当前目录内容（不改变历史）。"""
        cur = self._current_path()
        if not cur:
            return

        self.file_list.clear()
        try:
            entries = sorted(os.scandir(cur), key=lambda e: (not e.is_dir(), e.name.lower()))
        except OSError as e:
            self.status.setText(f"无法读取目录：{e}")
            return

        for entry in entries:
            try:
                is_dir = entry.is_dir()
            except OSError:
                is_dir = False
            icon = self._make_icon(is_dir)
            item = QListWidgetItem(icon, entry.name)
            item.setData(Qt.UserRole, entry.path)
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.file_list.addItem(item)

        self._update_path_bar()
        self._update_buttons()
        try:
            n_dirs = sum(1 for e in os.scandir(cur) if e.is_dir())
        except OSError:
            n_dirs = 0
        self.status.setText(f"{cur}   ·   {self.file_list.count()} 项")

    def _current_path(self) -> str:
        if self._history_index >= 0 and self._history_index < len(self._history):
            return self._history[self._history_index]
        return ""

    def _make_icon(self, is_dir: bool):
        """生成简易的文件夹 / 文件图标（纯 Qt 绘制，避免外部依赖）。"""
        pix = QPixmap(20, 20)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        if is_dir:
            p.setBrush(QColor(240, 194, 90))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(2, 5, 16, 12, 2, 2)
            p.drawRoundedRect(5, 2, 9, 4, 2, 2)
        else:
            p.setBrush(QColor(120, 136, 165))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(4, 2, 9, 16, 2, 2)
            p.drawRect(5, 9, 4, 3)
        p.end()
        return QIcon(pix)

    def _update_path_bar(self):
        """把当前路径渲染为可点击的面包屑。"""
        # 清除旧按钮
        while self.path_layout.count():
            it = self.path_layout.takeAt(0)
            w = it.widget()
            if w and not w.isHidden():
                w.deleteLater()

        cur = self._current_path()
        if not cur:
            return

        drive = pathlib.Path(cur).anchor or "/"
        parts = [p for p in cur.split(os.sep) if p]

        def add_crumb(text: str, path: str, last: bool = False):
            btn = RippleButton(text)
            btn.setObjectName("Crumb")
            if last:
                btn.setStyleSheet(
                    "RippleButton#Crumb{color:#ffffff;font-weight:600;}")
            else:
                btn.clicked.connect(lambda: self._navigate(path))
            self.path_layout.addWidget(btn)

        # 根
        if drive:
            root_path = str(pathlib.Path(drive).resolve())
            add_crumb(" / " if drive == "/" else drive, root_path,
                      len(parts) == 0)
            if parts:
                sep = QLabel("›")
                sep.setStyleSheet("color:#9aa3b2;")
                self.path_layout.addWidget(sep)

        acc = str(pathlib.Path(drive).resolve()) if drive else ""
        for i, part in enumerate(parts):
            acc = os.path.join(acc, part) if acc else part
            last = (i == len(parts) - 1)
            add_crumb(part, acc, last)
            if not last:
                sep = QLabel("›")
                sep.setStyleSheet("color:#9aa3b2;")
                self.path_layout.addWidget(sep)

        self.path_layout.addStretch(1)

    def _update_buttons(self):
        self.btn_back.setEnabled(self._history_index > 0)
        self.btn_forward.setEnabled(
            self._history_index < len(self._history) - 1)
        cur = self._current_path()
        self.btn_up.setEnabled(bool(cur) and self._is_dir(
            os.path.dirname(cur)) and os.path.dirname(cur) != cur)

    # ------------------------------------------------------------------
    # 槽
    # ------------------------------------------------------------------
    def _go_back(self):
        if self._history_index > 0:
            self._history_index -= 1
            self._reload()

    def _go_forward(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._reload()

    def _go_up(self):
        cur = self._current_path()
        parent = os.path.dirname(cur)
        if parent and self._is_dir(parent):
            self._navigate(parent)

    def _go_home(self):
        self._navigate(self._home_dir())

    def _on_side_clicked(self, item):
        path = item.data(Qt.UserRole)
        if path and self._is_dir(path):
            self._navigate(path)

    def _on_item_activated(self, item):
        path = item.data(Qt.UserRole)
        if not path:
            return
        if self._is_dir(path):
            self._navigate(path)
        else:
            self._open_file(path)

    def _open_file(self, path: str):
        """双击文件：用内置文本编辑器打开（文本类文件）。"""
        try:
            from TextEditor import create_editor_window
        except ImportError:
            self._open_in_system(path)
            return
        top = self.window()
        win = create_editor_window(top, file_path=path)
        ww, hh = 760, 520
        x = max(0, (self.width() - ww) // 2)
        y = max(0, (self.height() - hh) // 2)
        win.setGeometry(x, y, ww, hh)
        win.show()
        win.raise_()
        self._open_apps[path] = win

    def _open_in_system(self, path: str):
        """用系统默认方式打开（Windows: startfile；Linux: xdg-open）。"""
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                import subprocess
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print("打开文件失败:", e)

    # ------------------------------------------------------------------
    # 右键菜单：打开 / 复制 / 剪切 / 粘贴 / 重命名 / 属性
    # ------------------------------------------------------------------
    def _show_file_menu(self, pos):
        """在文件列表上弹出右键菜单（含空白区与选中项两种上下文）。"""
        item = self.file_list.itemAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)

        if item is not None:
            path = item.data(Qt.UserRole)
            self.file_list.setCurrentItem(item)
            self._file_menu_for_item(menu, path)
            menu.addSeparator()
        else:
            # 空白区域：新建文件夹 / 粘贴
            self._file_menu_for_blank(menu)

        menu.exec_(self.file_list.viewport().mapToGlobal(pos))

    def _file_menu_for_item(self, menu: QMenu, path: str):
        """选中文件/文件夹的右键菜单项"""
        act_open = menu.addAction("打开")
        act_open.triggered.connect(lambda: self._activate_path(path))
        act_copy = menu.addAction("复制")
        act_copy.triggered.connect(lambda: self._copy_paths([path]))
        act_cut = menu.addAction("剪切")
        act_cut.triggered.connect(lambda: self._cut_paths([path]))
        act_paste = menu.addAction("粘贴")
        act_paste.setEnabled(bool(self._clipboard["paths"]))
        act_paste.triggered.connect(self._paste)
        act_rename = menu.addAction("重命名")
        act_rename.triggered.connect(lambda: self._rename(path))
        act_prop = menu.addAction("属性")
        act_prop.triggered.connect(lambda: self._show_properties(path))

    def _file_menu_for_blank(self, menu: QMenu):
        """空白区域的右键菜单项：新建文件夹 / 粘贴"""
        act_new = menu.addAction("新建文件夹")
        act_new.triggered.connect(self._new_folder)
        act_paste = menu.addAction("粘贴")
        act_paste.setEnabled(bool(self._clipboard["paths"]))
        act_paste.triggered.connect(self._paste)

    def _activate_path(self, path: str):
        if self._is_dir(path):
            self._navigate(path)
        else:
            self._open_file(path)

    def _copy_paths(self, paths):
        self._clipboard = {"paths": list(paths), "cut": False}
        self.status.setText(f"已复制 {len(paths)} 项")

    def _cut_paths(self, paths):
        self._clipboard = {"paths": list(paths), "cut": True}
        self.status.setText(f"已剪切 {len(paths)} 项")

    def _paste(self):
        src_paths = self._clipboard.get("paths", [])
        if not src_paths:
            return
        dest = self._current_path()
        cut = self._clipboard.get("cut", False)
        ok, err = 0, ""
        for src in src_paths:
            name = os.path.basename(src)
            dst = os.path.join(dest, name)
            dst = self._unique_path(dst)
            try:
                if cut:
                    shutil.move(src, dst)
                else:
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                ok += 1
            except Exception as e:
                err = str(e)
        if cut:
            self._clipboard = {"paths": [], "cut": False}
        self._reload()
        self.status.setText(f"粘贴完成 {ok} 项" + (f"（{err}）" if err else ""))

    def _unique_path(self, dst: str) -> str:
        """若目标已存在，生成不冲突的名字。"""
        if not os.path.exists(dst):
            return dst
        base, ext = os.path.splitext(dst)
        i = 1
        while os.path.exists(f"{base} ({i}){ext}"):
            i += 1
        return f"{base} ({i}){ext}"

    def _rename(self, path: str):
        name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称：", text=name)
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        new_path = os.path.join(os.path.dirname(path), new_name)
        if new_path == path:
            return
        try:
            os.rename(path, new_path)
            self._reload()
            self.status.setText(f"已重命名为：{new_name}")
        except Exception as e:
            QMessageBox.warning(self, "重命名失败", str(e))

    def _new_folder(self):
        base = os.path.join(self._current_path(), "新建文件夹")
        new = self._unique_path(base)
        try:
            os.mkdir(new)
            self._reload()
            self.status.setText("已新建文件夹")
        except Exception as e:
            QMessageBox.warning(self, "新建文件夹失败", str(e))

    def _show_properties(self, path: str):
        name = os.path.basename(path) or path
        try:
            st = os.stat(path)
            size = self._fmt_size(st.st_size)
            mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            QMessageBox.warning(self, "属性", str(e))
            return
        kind = "文件夹" if self._is_dir(path) else "文件"
        info = (f"名称：{name}\n"
                f"类型：{kind}\n"
                f"位置：{path}\n"
                f"大小：{size}\n"
                f"修改时间：{mtime}")
        QMessageBox.information(self, "属性", info)

    @staticmethod
    def _fmt_size(num: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if num < 1024 or unit == "TB":
                return f"{num:.1f} {unit}" if unit != "B" else f"{num} B"
            num /= 1024
        return f"{num} B"


def create_file_manager_window(parent=None, start_dir=None):
    """用 EMdiSubWindow 生成文件资源管理器窗口（返回后需调用 show()）。"""
    win = EMdiSubWindow(parent, "文件管理器",
                        allow_maxmin_buttons=True, allow_resize=True)
    win.resize(760, 520)
    content = FileManagerWidget(start_dir=start_dir)
    win.addWidget(content)
    return win

if __name__ == "__main__":
    app = QApplication([])
    w = create_file_manager_window()
    w.show()
    app.exec()
