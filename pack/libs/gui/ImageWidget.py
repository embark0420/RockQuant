"""
ImageWidget — 聊天面板中的图片显示控件
自动缩放图片以适应最大宽度，保持宽高比，支持点击放大预览
"""
from pack.libs.gui.QtPack import *
from pack.libs.gui.TaskButton import TaskButton
import os


class ImageWidget(TaskButton):
    """图片显示控件，最大宽度 400px，保持宽高比，可点击放大"""

    MAX_WIDTH = 400
    MAX_HEIGHT = 300
    MIN_WIDTH = 100

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self._image_path = image_path
        self._original_pixmap = QPixmap(image_path)

        self.setFixedHeight(56)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("点击放大查看")

        self._init_ui()

        # 点击放大
        self.clicked.connect(self._show_enlarged)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 缩略图
        self._image_label = QLabel()
        self._image_label.setFixedSize(48, 48)
        self._image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._image_label)

        # 文件名
        fname = os.path.basename(self._image_path)
        self._text_label = QLabel(f"🖼️ {fname}")
        self._text_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._text_label, 1)

        # 大小信息
        size_kb = os.path.getsize(self._image_path) / 1024
        self._size_label = QLabel(f"{size_kb:.0f} KB")
        self._size_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self._size_label)

        # 加载缩略图
        if not self._original_pixmap.isNull():
            thumb = self._original_pixmap.scaled(
                48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._image_label.setPixmap(thumb)

        self._apply_theme()
        QApplication.instance().paletteChanged.connect(self._apply_theme)

    def _apply_theme(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128
        if is_dark:
            bg = "#1e2a1e"
            border = "#2d4a2d"
        else:
            bg = "#e8f5e9"
            border = "#c8e6c9"
        self.setStyleSheet(
            f"ImageWidget {{ background-color: {bg}; border: 1px solid {border}; "
            f"border-radius: 6px; }}"
            f"ImageWidget:hover {{ border-color: #4a9eff; }}"
        )

    def _show_enlarged(self):
        """点击放大显示原图"""
        if self._original_pixmap.isNull():
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(os.path.basename(self._image_path))
        dialog.setAttribute(Qt.WA_DeleteOnClose)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 缩放后的图片
        screen = QApplication.primaryScreen()
        screen_size = screen.availableSize() if screen else QSize(1000, 700)
        max_w = screen_size.width() - 80
        max_h = screen_size.height() - 120

        pix = self._original_pixmap
        scaled = pix.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        label = QLabel()
        label.setPixmap(scaled)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label, 1)

        # 关闭按钮
        btn = TaskButton("关闭")
        btn.setFixedSize(70, 28)
        btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        dialog.resize(scaled.width() + 40, scaled.height() + 60)
        dialog.exec()

    @property
    def image_path(self) -> str:
        return self._image_path
