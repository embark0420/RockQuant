import os
import sys

# ---- QtWebEngine 媒体播放配置（必须在创建 QApplication / QWebEngineView 之前生效）----
# 解锁自动播放、启用 GPU 视频解码、允许 WebRTC，改善网页视频播放。
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--autoplay-policy=no-user-gesture-required "
    "--ignore-gpu-blocklist "
    "--enable-gpu-rasterization "
    "--enable-zero-copy "
    "--disable-features=UseSkiaRenderer "
    "--use-gl=desktop "
    "--enable-accelerated-video-decode "
    "--disable-gpu-driver-bug-workarounds "
)
# 允许 QtWebEngine 读取其自带的 resources（必要时定位 Qt5 安装目录）
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

# ---- Linux 沙箱修复 ----
# Chromium（QtWebEngine）作为 root 运行时："Running as root without --no-sandbox
# is not supported"。嵌入式/单板机常以 root 运行，因此 Linux 下追加 --no-sandbox。
# （也可避免某些环境缺 user-namespace 导致沙箱启动失败）
if sys.platform.startswith("linux"):
    _flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "").strip()
    if "--no-sandbox" not in _flags:
        _flags = (_flags + " --no-sandbox").strip()
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = _flags

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineSettings

from pack.libs.gui.Control import EMdiSubWindow


class BrowserWidget(QWidget):
    """内置网页浏览器：地址栏 + 前进/后退/刷新 + 主页 + 加载进度。"""

    HOME_URL = "http://www.baidu.com"

    def __init__(self, parent=None, start_url=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._init_ui()
        self._apply_style()
        self.load(start_url or self.HOME_URL)

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ---------- 顶部导航工具条 ----------
        bar = QHBoxLayout()
        bar.setSpacing(6)

        self.btn_back = QToolButton(); self.btn_back.setText("←")
        self.btn_back.setToolTip("后退")
        self.btn_back.clicked.connect(lambda: self.view.back())
        bar.addWidget(self.btn_back)

        self.btn_forward = QToolButton(); self.btn_forward.setText("→")
        self.btn_forward.setToolTip("前进")
        self.btn_forward.clicked.connect(lambda: self.view.forward())
        bar.addWidget(self.btn_forward)

        self.btn_reload = QToolButton(); self.btn_reload.setText("⟳")
        self.btn_reload.setToolTip("刷新")
        self.btn_reload.clicked.connect(lambda: self.view.reload())
        bar.addWidget(self.btn_reload)

        self.btn_home = QToolButton(); self.btn_home.setText("⌂")
        self.btn_home.setToolTip("主页")
        self.btn_home.clicked.connect(lambda: self.load(self.HOME_URL))
        bar.addWidget(self.btn_home)

        self.address = QLineEdit()
        self.address.setPlaceholderText("输入网址，如 http://example.com")
        self.address.returnPressed.connect(self._go)
        bar.addWidget(self.address, 1)

        go = QToolButton(); go.setText("前往")
        go.clicked.connect(self._go)
        bar.addWidget(go)

        root.addLayout(bar)

        # ---------- 网页视图 ----------
        self.view = QWebEngineView()
        self._configure_engine_settings()
        self.view.urlChanged.connect(self._on_url_changed)
        self.view.loadProgress.connect(self._on_progress)
        self.view.titleChanged.connect(self._on_title_changed)
        root.addWidget(self.view, 1)

        # ---------- 状态栏 ----------
        self.status = QLabel("就绪")
        self.status.setObjectName("BrowserStatus")
        self.status.setFixedHeight(22)
        root.addWidget(self.status)

    def _configure_engine_settings(self):
        """配置 QtWebEngine 设置，尽量解锁媒体/视频播放能力。"""
        try:
            s = self.view.settings()
            # 媒体与交互
            s.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
            s.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
            s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            s.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
            s.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
            s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            s.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            s.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
            s.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
            s.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, True)
            try:
                # 子进程/媒体权限
                settings_attrs = [
                    "AllowRunningInsecureContent", "AllowGeolocationOnInsecureOrigins",
                ]
                for name in settings_attrs:
                    if hasattr(QWebEngineSettings, name):
                        s.setAttribute(getattr(QWebEngineSettings, name), True)
            except Exception:
                pass
            # 固定一个现代浏览器 UA，避免站点拒绝播放
            self.view.page().profile().setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
            )
        except Exception as e:
            print(f"[Browser] 引擎设置配置失败: {e}")

    def load(self, url: str):
        """加载 URL（自动补全协议）"""
        url = url.strip()
        if not url:
            return
        if not ("://" in url):
            url = "http://" + url
        self.view.setUrl(QUrl(url))

    def _go(self):
        self.load(self.address.text())

    def _on_url_changed(self, url: QUrl):
        self.address.setText(url.toString())

    def _on_title_changed(self, title):
        if title:
            self.setWindowTitle(title)

    def _on_progress(self, progress: int):
        if progress < 100:
            self.status.setText(f"加载中… {progress}%")
        else:
            self.status.setText("完成")

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget { background: #1e212d; color: #e8eaf0; font-size: 13px; }
            QToolButton {
                background: rgba(255,255,255,0.05);
                border: none; border-radius: 6px;
                color: #e8eaf0; font-size: 15px; padding: 4px 8px;
            }
            QToolButton:hover { background: rgba(255,255,255,0.12); }
            QToolButton:pressed { background: rgba(91,124,250,0.5); }
            QLineEdit {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 6px; padding: 4px 8px; color: #e8eaf0;
            }
            QLineEdit:focus { border: 1px solid #5b7cfa; }
            QLabel#BrowserStatus { color: #9aa3b2; padding-left: 4px; }
        """)


def create_browser_window(parent=None):
    """用 EMdiSubWindow 生成浏览器窗口（返回后需调用 show()）。"""
    win = EMdiSubWindow(parent, "浏览器",
                        allow_maxmin_buttons=True, allow_resize=True)
    win.resize(860, 560)
    content = BrowserWidget()
    win.addWidget(content)
    return win


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = create_browser_window()
    win.show()
    app.exec()
