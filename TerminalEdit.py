import os

from pack.libs.gui.QtPack import *


class TerminalEdit(QPlainTextEdit):
    """基于 QPlainTextEdit 的交互式系统 shell 终端控件。

    通过 QProcess 在后台运行系统 shell（Windows 默认 PowerShell），把 shell 的
    stdout/stderr 实时追加到控件中，同时把用户在控件里输入的命令逐行发送给
    shell 执行。具备提示符、输入保护、命令历史等基础终端能力。
    外观为老式终端风格：纯黑背景、纯白文字、块状反色闪烁光标。
    """

    # ------------------------------------------------------------------
    # 可配置项
    # ------------------------------------------------------------------
    SHELL_ENV = "powershell"          # 系统终端命令（Windows 默认 PowerShell）
    # 启动参数：关闭横幅、结束后保持，并把提示符固定为简短的 "PS> "。
    # 固定提示符便于：【透传】shell 输出（含 python 等子程序的 >>> 提示符），
    # 同时让控件能精确定位可编辑输入区起点。
    SHELL_ARGS = [
        "-NoLogo", "-NoExit",
        "-Command", "function global:prompt { 'PS> ' }",
    ]
    BLINK_INTERVAL = 500              # 光标闪烁周期（毫秒）

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self._shell = None            # QProcess 句柄
        self._history = []            # 命令历史
        self._hist_index = 0          # 历史浏览指针
        self._readonly_pos = 0        # 只读区与提示符的分界（提示符起始位置），<= 该位置的内容不可修改
        self._input_start = 0         # 可编辑区起点（提示符末尾），< 该位置（含提示符）一律不可编辑

        # ---- 终端配色：纯黑背景 + 纯白文字 ----
        pal = self.palette()
        pal.setColor(QPalette.Base, QColor(0, 0, 0))
        pal.setColor(QPalette.Text, QColor(255, 255, 255))
        pal.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(pal)

        # 去掉边框、隐藏原生光标（改为自绘块状反色光标）
        self.setFrameShape(QFrame.NoFrame)
        self.setCursorWidth(0)

        # ---- 光标闪烁控制 ----
        self._cursor_on = True
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(self.BLINK_INTERVAL)
        self._blink_timer.timeout.connect(self._toggle_cursor)
        self._set_blink_state(self.hasFocus())

        # ---- 事件连接 ----
        self.textChanged.connect(self._auto_scroll)
        self.cursorPositionChanged.connect(self._guard_cursor)

        # 应用退出前优雅终止 shell，避免子进程残留
        QApplication.instance().aboutToQuit.connect(self._cleanup_shell)

        # 兜底守卫：周期强制把光标锁在输入区，确保任何途径都无法停留在只读区
        self._guard_timer = QTimer(self)
        self._guard_timer.setInterval(60)
        self._guard_timer.timeout.connect(self._guard_cursor)
        self._guard_timer.start()

        # 启动系统 shell
        self._start_shell()

    def closeEvent(self, event):
        """关闭控件时优雅地终止 shell 子进程，避免残留。"""
        self._cleanup_shell()
        super().closeEvent(event)

    def _cleanup_shell(self):
        """终止正在运行的 shell 子进程。"""
        if self._shell and self._shell.state() == QProcess.Running:
            self._shell.terminate()
            if not self._shell.waitForFinished(1000):
                self._shell.kill()

    # ==================================================================
    # 终端核心：shell 进程管理
    # ==================================================================
    def _start_shell(self):
        """启动系统 shell 进程并连接输出信号。"""
        self._shell = QProcess(self)
        # 合并 stdout 与 stderr，保证输出顺序一致
        self._shell.setProcessChannelMode(QProcess.MergedChannels)

        env = QProcessEnvironment.systemEnvironment()
        self._shell.setProcessEnvironment(env)

        self._shell.readyReadStandardOutput.connect(self._on_shell_output)
        self._shell.finished.connect(self._on_shell_finished)

        self._shell.start(self.SHELL_ENV, self.SHELL_ARGS)

        # 启动横幅
        self._append_output(
            "TerminalEdit - interactive shell\n"
            f"shell: {self.SHELL_ENV}\n"
            "type 'exit' to quit, use Up/Down for history.\n\n"
        )
        # 输入区起点推到当前文本末尾（等 shell 的提示符输出到达后会自动推进）
        self._advance_input_area()

    def _on_shell_output(self):
        """shell 有输出时，追加到控件。"""
        data = bytes(self._shell.readAllStandardOutput())
        text = data.decode("utf-8", errors="replace")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if text:
            # 若末尾是提示符则先清掉，再附加新输出，最后重新给提示符
            self._append_output(text)

    def _on_shell_finished(self, exit_code: int, status):
        """shell 退出（用户执行 exit）时收尾并重启一个新 shell。"""
        self._append_output(f"\n[shell exited with code {exit_code}]")
        self._shell.deleteLater()
        self._shell = None
        self._start_shell()

    # ==================================================================
    # 输出与输入区：透传模型
    # shell/子程序的输出（含提示符，如 "PS> " 或 python 的 ">>> "）原样
    # 追加显示；每当有新输出到达，就把可编辑输入区起点推进到最新输出的末尾。
    # ==================================================================
    def _append_output(self, text: str):
        """把 shell 输出原样追加到末尾，并把输入区起点推进到新输出的末尾。"""
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)
        # 新输入从本次输出的末尾开始
        self._input_start = self.textCursor().position()
        self._readonly_pos = self._input_start
        self.moveCursor(QTextCursor.End)
        self._auto_scroll()

    def _advance_input_area(self):
        """在没有任何新输出的情况下重置输入区（例如 shell 刚启动时），
        将其起点放在当前文本末尾。"""
        self.moveCursor(QTextCursor.End)
        self._input_start = self.textCursor().position()
        self._readonly_pos = self._input_start
        self._auto_scroll()

    def _current_line_command(self) -> str:
        """提取可编辑输入区中的命令文本（输入区起点之后直到当前行尾）。"""
        text = self.document().toPlainText()
        cur = self.textCursor()
        cur.movePosition(QTextCursor.End)
        return text[self._input_start:cur.position()]

    def _replace_current_command(self, cmd: str):
        """用新的命令文本替换可编辑输入区的内容（只动输入区，不动历史输出）。"""
        cur = self.textCursor()
        cur.setPosition(self._input_start)
        cur.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cur.removeSelectedText()
        cur.insertText(cmd)
        cur.movePosition(QTextCursor.End)
        self.setTextCursor(cur)
        self._auto_scroll()

    def _auto_scroll(self):
        """滚动到底部。"""
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ==================================================================
    # 输入保护：历史输出区只读，光标强制锁定在输入区
    # ==================================================================
    def _cursor_in_input_area(self) -> bool:
        """判断光标是否位于可编辑区（当前提示符末尾之后）。"""
        cur = self.textCursor()
        return cur.position() >= self._input_start

    def _guard_cursor(self):
        """光标一旦跑到不可编辑区（提示符及其之前），立即弹回可编辑区起点。"""
        # 初始化未完成时跳过（提示符还没写入、边界未就绪）
        if self._input_start <= 0:
            return
        doc = self.document()
        doc_len = doc.characterCount() - 1  # 最后一个有效位置
        cur = self.textCursor()
        if cur.selectionStart() < self._input_start or cur.position() < self._input_start:
            cur.clearSelection()
            # 目标位置：可编辑区起点，且不得超出文档末尾
            target = min(self._input_start, doc_len)
            target = max(0, target)
            cur.setPosition(target)
            self.setTextCursor(cur)

    def _edit_point(self) -> int:
        """可编辑光标位置：夹紧在 [可编辑区起点, 文档末尾] 之间。"""
        doc_len = max(0, self.document().characterCount() - 1)
        return min(max(self._input_start, doc_len), doc_len) if self._input_start >= 0 else doc_len

    def mousePressEvent(self, event):
        """点击任何位置后，立即把光标强制守卫回可编辑区。"""
        super().mousePressEvent(event)
        self._guard_cursor()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        self._guard_cursor()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._guard_cursor()

    def _touches_readonly(self) -> bool:
        """判断当前选区（或光标）是否触碰到提示符及其之前的不可编辑区。"""
        cur = self.textCursor()
        return cur.selectionStart() < self._input_start or cur.position() < self._input_start

    def _force_cursor_to_edit_start(self):
        """把光标/选区强制归位到可编辑区起点（用于删除前的守卫）。"""
        cur = self.textCursor()
        cur.clearSelection()
        # 夹紧到合法范围
        doc_len = max(0, self.document().characterCount() - 1)
        cur.setPosition(max(0, min(self._input_start, doc_len)))
        self.setTextCursor(cur)

    def insertFromMimeData(self, source):
        """拦截粘贴：只允许粘贴进可编辑区。"""
        if self._touches_readonly():
            self._force_cursor_to_edit_start()
        super().insertFromMimeData(source)

    # ==================================================================
    # 键盘事件：命令提交 / 历史浏览 / 输入保护
    # ==================================================================
    def keyPressEvent(self, event):
        key = event.key()

        # 上/下：命令历史
        if key == Qt.Key_Up:
            self._browse_history(-1)
            event.accept()
            return
        if key == Qt.Key_Down:
            self._browse_history(1)
            event.accept()
            return

        # 回车：提交当前行的命令
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.moveCursor(QTextCursor.End)
            self._submit_command()
            event.accept()
            return

        # ---- 只读保护核心 ----
        # 退格：会删除 position()-1 处的字符。若光标在可编辑区起点（提示符末尾），
        # 退格会删掉提示符的最后一个字符，必须拦截。仅当 position() > _input_start 才放行。
        if key == Qt.Key_Backspace:
            cur = self.textCursor()
            if self._touches_readonly() or cur.position() <= self._input_start:
                # 已无输入字符可删，直接拦截，保护提示符不被删除
                event.accept()
                return
            super().keyPressEvent(event)
            event.accept()
            self._guard_cursor()
            return

        # Delete：删除 position() 处的字符。光标必须在可编辑区内。
        if key == Qt.Key_Delete:
            if self._touches_readonly():
                self._force_cursor_to_edit_start()
                event.accept()
                return
            super().keyPressEvent(event)
            event.accept()
            self._guard_cursor()
            return

        # 光标移动类按键：只允许在可编辑区内移动，不允许回退到提示符/历史区
        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End,
                   Qt.Key_PageUp, Qt.Key_PageDown):
            if not self._cursor_in_input_area():
                self._force_cursor_to_edit_start()
                event.accept()
                return
            super().keyPressEvent(event)
            event.accept()
            self._guard_cursor()
            return

        # 其余可打印字符 / 粘贴：若不在可编辑区，先强制回可编辑区
        if not self._cursor_in_input_area():
            self._force_cursor_to_edit_start()
            event.accept()
            self._guard_cursor()
            return

        super().keyPressEvent(event)
        self._guard_cursor()

    def _submit_command(self):
        """把当前输入行的命令发送给系统 shell。"""
        cmd = self._current_line_command()

        # 换行结束输入行
        self.moveCursor(QTextCursor.End)
        self.insertPlainText("\n")
        self._auto_scroll()

        cmd = cmd.strip()

        # 空命令：发送空行给 shell，让其输出新提示符
        if not cmd:
            if self._shell and self._shell.state() == QProcess.Running:
                self._shell.write(b"\n")
            return

        # 记录历史
        if not self._history or self._history[-1] != cmd:
            self._history.append(cmd)
        self._hist_index = len(self._history)

        # 内置命令：exit 关闭 shell
        if cmd.lower() in ("exit", "quit"):
            if self._shell and self._shell.state() == QProcess.Running:
                self._shell.write(b"exit\n")
                self._shell.waitForFinished(2000)
                self._shell.kill()
            return

        # 发送给系统 shell
        if self._shell and self._shell.state() == QProcess.Running:
            self._shell.write((cmd + "\n").encode("utf-8"))

    def _browse_history(self, direction: int):
        """上/下键浏览历史，替换当前输入行内容。"""
        if not self._history:
            return
        idx = self._hist_index + direction
        if idx < 0:
            idx = 0
        if idx > len(self._history):
            idx = len(self._history)
        self._hist_index = idx

        if idx == len(self._history):
            cmd = ""
        else:
            cmd = self._history[idx]
        self._replace_current_command(cmd)

    # ==================================================================
    # 光标闪烁（老式终端块状反色光标）
    # ==================================================================
    def _set_blink_state(self, active: bool):
        self._cursor_on = True
        if active:
            if not self._blink_timer.isActive():
                self._blink_timer.start()
        else:
            self._blink_timer.stop()
        self.viewport().update()

    def _toggle_cursor(self):
        self._cursor_on = not self._cursor_on
        self.viewport().update()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._set_blink_state(True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._set_blink_state(False)

    # ------------------------------------------------------------------
    # 绘制：自绘老式终端光标 + 强制黑底白字
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

        at_end = cursor.atBlockEnd()
        painter.setCompositionMode(QPainter.CompositionMode_Difference)

        if at_end:
            painter.fillRect(
                rect.x(), block_y, int(block_width * 0.6), block_height,
                QColor(255, 255, 255),
            )
        else:
            painter.fillRect(rect.x(), block_y, block_width, block_height, QColor(255, 255, 255))

        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    def _char_width(self) -> int:
        """估算当前文档中一个字符的宽度。"""
        metrics = QFontMetrics(self.font())
        return metrics.width("M")


if __name__ == "__main__":
    app = QApplication([])

    window = QMainWindow()
    window.resize(700, 400)
    terminal = TerminalEdit(window)
    terminal.setGeometry(10, 10, 680, 380)
    terminal.setFont(QFont("Consolas", 12))
    window.show()

    app.exec()