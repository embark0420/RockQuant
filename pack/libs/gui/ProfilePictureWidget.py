import os

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import (QPainter, QColor, QPixmap, QPainterPath, QBrush, QPen)


class ProfilePictureWidget(QLabel):
    """圆形头像控件（QPainter 绘制：圆形背景 + 居中图片，支持透明背景）"""

    def __init__(
        self,
        parent=None,
        background_color: str = "#2d2d44",
        border_width : int = 1,
        image_path: str = "",
        size: int = 80
    ):
        super().__init__(parent)

        self.setFixedSize(size, size)

        # 背景色：支持 "#rrggbb" 或 "transparent"
        self._bg_color = QColor(background_color) if background_color else QColor(Qt.transparent)
        if not self._bg_color.isValid():
            # QColor("xx") 失败时（如乱写的字符串）回退为透明，避免崩溃
            self._bg_color = QColor(Qt.transparent)

        # 边框宽度（半透明 #a2a2a2 圆环边框，宽度为 0 时表示不画边框）
        self._border_width = max(0, int(border_width or 0))

        self._image_path = image_path or ""
        self._pixmap = QPixmap()
        self._load_image()

        self.setAlignment(Qt.AlignCenter)

    # ------------------------------------------------------------------
    # 图片加载
    # ------------------------------------------------------------------
    def _load_image(self):
        """按 image_path 加载图片；路径无效或为空时清空。"""
        self._pixmap = QPixmap()
        if self._image_path and os.path.isfile(self._image_path):
            pm = QPixmap(self._image_path)
            if not pm.isNull():
                self._pixmap = pm
        self.update()

    def set_image(self, image_path: str):
        """更新头像图像"""
        self._image_path = image_path or ""
        self._load_image()

    def set_background_color(self, color: str):
        """更新背景色（支持 transparent）"""
        c = QColor(color) if color else QColor(Qt.transparent)
        if c.isValid():
            self._bg_color = c
        self.update()

    def set_size(self, size: int):
        """动态调整尺寸"""
        self.setFixedSize(size, size)
        self.update()

    def set_border_width(self, width: int):
        """更新边框宽度（0 = 无边框）"""
        self._border_width = max(0, int(width or 0))
        self.update()

    # ------------------------------------------------------------------
    # 绘制：圆形裁剪，保证透明背景 + 图片都能正确显示
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addEllipse(rect)

        # 填充背景（transparent 时不会产生可见背景，仅起兜底作用）
        p.fillPath(path, QBrush(self._bg_color))

        # 绘制居中图片（仅在圆形区域内显示，达到圆形头像效果）
        if not self._pixmap.isNull():
            p.save()
            p.setClipPath(path)
            scaled = self._pixmap.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
            p.restore()

        # 绘制半透明 #a2a2a2 圆环边框（宽度由 border_width 控制）
        if self._border_width > 0:
            bw = self._border_width
            # 边框线画在椭圆的半径方向上居中（向内缩半宽，保证不超出控件）
            border_rect = QRectF(rect).adjusted(bw / 2, bw / 2, -bw / 2, -bw / 2)
            border_path = QPainterPath()
            border_path.addEllipse(border_rect)
            p.setPen(QPen(QColor(162, 162, 162, 180), bw))
            p.setBrush(Qt.NoBrush)
            p.drawPath(border_path)
