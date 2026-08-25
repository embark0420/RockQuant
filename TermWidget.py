import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from pack.libs.gui.Control import EMdiSubWindow

IS_LINUX = sys.platform.startswith("linux")

# 尝试导入 py3qterm（Rock S0 Linux 已安装；Windows 上不可用会自动降级）
try:
    from pyqtermwidget import TerminalWidget as _PyQTerm
    HAS_PY3QTERM = True
except Exception:
    HAS_PY3QTERM = False


# ----------------------------------------------------------------------
#  py3qterm 终端（真实 PTY，Linux）
# ----------------------------------------------------------------------
def _build_py3qterm_terminal(parent):
    """用 py3qterm + QProcess 启动 /bin/bash，返回终端控件。"""
    term = _PyQTerm(parent)
    # 去掉 Window 标志，强制其为普通子控件，内嵌到 EMdiSubWindow 里
    term.setWindowFlag(Qt.Window, False)
    # 用 palette + autoFillBackground 填充深色背景。
    # ⚠️ 这里不能用 styleSheet，也不能设 WA_OpaquePaintEvent ——
    # 否则会覆盖/干扰 pyqtermwidget 内部的自绘渲染，
    # 导致终端内容不显示（只有标题栏、下方透明）。
    term.setAutoFillBackground(True)
    pal = term.palette()
    bg = QColor(18, 18, 24)
    pal.setColor(QPalette.Window, bg)
    pal.setColor(QPalette.Base, bg)
    pal.setColor(QPalette.Text, QColor(230, 230, 230))
    term.setPalette(pal)
    term.setFocusPolicy(Qt.StrongFocus)
    term.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    proc = QProcess(term)
    proc.setProcessChannelMode(QProcess.MergedChannels)
    proc.start("/bin/bash", [])
    term._proc = proc

    def _feed(data):
        """用户按键 → shell 的 stdin"""
        try:
            raw = data.encode("utf-8") if isinstance(data, str) else data
            proc.write(raw)
        except Exception:
            pass

    # py3qterm 的输入信号（兼容多种命名）
    for _sig in ("input", "termKeyPressed", "keyPressed"):
        if hasattr(term, _sig):
            try:
                getattr(term, _sig).connect(_feed)
                break
            except Exception:
                pass

    def _read_out():
        try:
            term.putData(proc.readAllStandardOutput())
        except Exception:
            pass

    def _read_err():
        try:
            term.putData(proc.readAllStandardError())
        except Exception:
            pass

    proc.readyReadStandardOutput.connect(_read_out)
    proc.readyReadStandardError.connect(_read_err)
    return term


# ----------------------------------------------------------------------
#  降级终端（Windows 开发环境模拟）
# ----------------------------------------------------------------------
def _build_fallback_terminal(parent):
    """Windows 上无 py3qterm：用 TerminalEdit（QProcess + PowerShell 模拟终端）。"""
    from TerminalEdit import TerminalEdit
    return TerminalEdit(parent)


def build_term_widget(parent=None) -> QWidget:
    """返回一个终端控件：Linux 优先用 py3qterm，否则降级 TerminalEdit 模拟。"""
    if HAS_PY3QTERM:
        try:
            return _build_py3qterm_terminal(parent)
        except Exception as e:
            print("py3qterm 初始化失败，降级到 TerminalEdit:", e)
    return _build_fallback_terminal(parent)


def create_terminal_window(parent=None):
    """用 EMdiSubWindow 生成终端窗口（返回后需调用 show()）。"""
    win = EMdiSubWindow(parent, "终端",
                        allow_maxmin_buttons=True, allow_resize=True)
    win.resize(720, 500)
    term = build_term_widget(win)
    win.addWidget(term)
    return win


if __name__ == "__main__":
    app = QApplication([])
    w = create_terminal_window()
    w.show()
    app.exec()
