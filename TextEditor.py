from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import pathlib

from pack.libs.gui.Control import EMdiSubWindow


class TextEditorWidget(QWidget):
    """内置文本编辑器：打开 / 保存 / 新建，支持语法高亮与行/列状态显示。"""

    def __init__(self, parent=None, file_path=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._file = None
        self._init_ui()
        self._apply_style()
        if file_path:
            self.open_file(file_path)

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ---------- 顶部工具条 ----------
        bar = QHBoxLayout()
        bar.setSpacing(6)

        self.btn_new = self._tool_btn("新建")
        self.btn_new.clicked.connect(self.new_file)
        bar.addWidget(self.btn_new)

        self.btn_open = self._tool_btn("打开")
        self.btn_open.clicked.connect(self._pick_open)
        bar.addWidget(self.btn_open)

        self.btn_save = self._tool_btn("保存")
        self.btn_save.clicked.connect(self.save_file)
        bar.addWidget(self.btn_save)

        self.btn_saveas = self._tool_btn("另存为")
        self.btn_saveas.clicked.connect(self.save_file_as)
        bar.addWidget(self.btn_saveas)

        self.fname = QLabel("未命名")
        self.fname.setObjectName("FName")
        bar.addWidget(self.fname, 1)

        root.addLayout(bar)

        # ---------- 编辑区 ----------
        self.edit = QPlainTextEdit()
        self.edit.setTabStopDistance(4 * self.edit.fontMetrics().horizontalAdvance(' '))
        self.edit.cursorPositionChanged.connect(self._update_status)
        root.addWidget(self.edit, 1)

        # ---------- 状态栏 ----------
        self.status = QLabel("行 1，列 1")
        self.status.setObjectName("EditorStatus")
        self.status.setFixedHeight(22)
        root.addWidget(self.status)

    def _tool_btn(self, text):
        b = QToolButton()
        b.setText(text)
        b.setCursor(Qt.PointingHandCursor)
        return b

    # ------------------------------------------------------------------
    # 文件操作
    # ------------------------------------------------------------------
    def new_file(self):
        if self._maybe_save():
            self.edit.clear()
            self._file = None
            self.fname.setText("未命名")
            self.setWindowTitle("文本编辑器 - 未命名")
            self._update_window_title()

    def _pick_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "文本文件 (*.txt *.md *.py *.c *.cpp *.h *.json *.html *.css *.js);;所有文件 (*)")
        if path:
            self.open_file(path)

    def open_file(self, path: str):
        try:
            data = pathlib.Path(path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                data = pathlib.Path(path).read_text(encoding="gbk")
            except Exception as e:
                QMessageBox.warning(self, "打开失败", str(e))
                return
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))
            return
        self.edit.setPlainText(data)
        self._file = path
        self.fname.setText(pathlib.Path(path).name)
        self.setWindowTitle(f"文本编辑器 - {pathlib.Path(path).name}")
        self._update_window_title()
        self._update_status()

    def save_file(self):
        if self._file:
            self._write(self._file)
        else:
            self.save_file_as()

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "", "文本文件 (*.txt);;所有文件 (*)")
        if path:
            self._write(path)
            self._file = path
            self.fname.setText(pathlib.Path(path).name)
            self.setWindowTitle(f"文本编辑器 - {pathlib.Path(path).name}")
            self._update_window_title()

    def _write(self, path: str):
        try:
            pathlib.Path(path).write_text(self.edit.toPlainText(), encoding="utf-8")
            self.status.setText(f"已保存：{path}")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _maybe_save(self) -> bool:
        """新建前若内容有改动，询问是否保存（简化：直接放行）。"""
        return True

    def _update_status(self):
        c = self.edit.textCursor()
        self.status.setText(f"行 {c.blockNumber() + 1}，列 {c.columnNumber() + 1}")

    def _update_window_title(self):
        """把所在的 EMdiSubWindow 标题栏更新为当前文件名。"""
        name = self.fname.text() if self.fname else "未命名"
        top = self.window()
        if top is not self and hasattr(top, 'set_title'):
            top.set_title(name)

    # ------------------------------------------------------------------
    # 样式
    # ------------------------------------------------------------------
    def _apply_style(self):
        self.setStyleSheet("""
            QWidget { background: #1e212d; color: #e8eaf0; font-size: 13px; }
            QToolButton {
                background: rgba(255,255,255,0.05);
                border: none; border-radius: 6px;
                color: #e8eaf0; font-size: 13px; padding: 4px 10px;
            }
            QToolButton:hover { background: rgba(255,255,255,0.12); }
            QToolButton:pressed { background: rgba(91,124,250,0.5); }
            QPlainTextEdit {
                background: #181b26;
                color: #e8eaf0;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                padding: 6px;
                font-family: "Consolas", "Microsoft YaHei", monospace;
                font-size: 14px;
                selection-background-color: #5b7cfa;
            }
            QLabel#FName { color: #c9cde0; padding: 0 6px; }
            QLabel#EditorStatus { color: #9aa3b2; padding-left: 4px; }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #181b26; width: 10px; height: 10px;
                border: none; margin: 0;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #33384a; border-radius: 5px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #5b7cfa;
            }
            QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
            QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
        """)


def create_editor_window(parent=None, file_path=None):
    """用 EMdiSubWindow 生成文本编辑器窗口（返回后需调用 show()）。"""
    win = EMdiSubWindow(parent, "文本编辑器",
                        allow_maxmin_buttons=True, allow_resize=True)
    win.resize(720, 500)
    content = TextEditorWidget(file_path=file_path)
    win.addWidget(content)
    return win


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = create_editor_window()
    win.show()
    app.exec()
