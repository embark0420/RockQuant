from pack.libs.gui.QtPack import *


class CodeEdit(QPlainTextEdit):
    """老式终端风格代码编辑器。

    光标采用经典 CRT/DOS 终端的「块状反色光标」，并在失去焦点或
    光标到达文本末尾时显示为闪烁的下划线/半透明块，模拟老式终端
    的硬件光标质感。
    """

    # 闪烁周期（毫秒），老式终端大约在 0.5s 左右
    BLINK_INTERVAL = 500

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        # 终端配色：纯黑背景 + 纯白文字
        terminal_palette = self.palette()
        terminal_palette.setColor(QPalette.Base, QColor(0, 0, 0))          # 编辑区背景 -> 纯黑
        terminal_palette.setColor(QPalette.Text, QColor(255, 255, 255))    # 文字 -> 纯白
        terminal_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(terminal_palette)

        # 去掉控件边框（QPlainTextEdit 继承自 QFrame）
        self.setFrameShape(QFrame.NoFrame)

        # 隐藏 Qt 默认的细条光标，改由 paintEvent 自绘老式块状光标
        self.setCursorWidth(0)

        # 光标是否处于"亮"状态（闪烁开关）
        self._cursor_on = True
        # 是否与普通光标一样，仅仅在文本末尾附近显示为下划线
        self._cursor_at_end = False

        # 闪烁定时器
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(self.BLINK_INTERVAL)
        self._blink_timer.timeout.connect(self._toggle_cursor)

        # 光标位置变化、文本内容变化时刷新光标状态
        self.cursorPositionChanged.connect(self._refresh_cursor)
        self.textChanged.connect(self._refresh_cursor)

        self._set_blink_state(self.hasFocus())

    # ------------------------------------------------------------------
    # 光标状态控制
    # ------------------------------------------------------------------
    def _set_blink_state(self, active: bool):
        """打开/关闭闪烁，并重置为可见状态。"""
        self._cursor_on = True
        if active:
            if not self._blink_timer.isActive():
                self._blink_timer.start()
        else:
            self._blink_timer.stop()
        # 通知 paintEvent 立刻重绘光标
        self._update_viewport()

    def _toggle_cursor(self):
        self._cursor_on = not self._cursor_on
        self._update_viewport()

    def _refresh_cursor(self):
        self._set_blink_state(self.hasFocus())

    def _update_viewport(self):
        self.viewport().update()

    # ------------------------------------------------------------------
    # 焦点相关
    # ------------------------------------------------------------------
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._set_blink_state(True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._set_blink_state(False)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.hasFocus() or not self._cursor_on:
            return

        painter = QPainter(self.viewport())
        cursor = self.textCursor()
        rect = self.cursorRect(cursor)

        line_height = rect.height()
        char_width = self._char_width()

        block_height = max(1, int(line_height * 0.7))
        block_y = rect.y() + (line_height - block_height) // 2
        block_width = max(char_width, rect.width())

        self._cursor_at_end = cursor.atBlockEnd()
        painter.setCompositionMode(QPainter.CompositionMode_Difference)

        if self._cursor_at_end:
            # 行末：半宽反色块
            painter.fillRect(
                rect.x(), block_y, int(block_width * 0.6), block_height,
                QColor(255, 255, 255),
            )
        else:
            # 正常：半高反色块（垂直居中）
            painter.fillRect(rect.x(), block_y, block_width, block_height, QColor(255, 255, 255))

        # 恢复普通绘制模式，避免影响后续绘制
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    def _char_width(self) -> int:
        """估算当前文档中一个字符的宽度。"""
        metrics = QFontMetrics(self.font())
        return metrics.width("M")


if __name__ == "__main__":
    app = QApplication([])

    window = QMainWindow()
    window.resize(400, 400)
    editor = CodeEdit(window)
    editor.setGeometry(80, 80, 250, 250)
    editor.setFont(QFont("Consolas", 12))
    window.show()

    app.exec()