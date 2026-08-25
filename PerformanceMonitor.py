from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import psutil
import collections
import platform
import time

from pack.libs.gui.Control import EMdiSubWindow


# ============================================================
#  实时滚动曲线图（参考 Untitled.py 的 CurveChart，PyQt5 重写）
# ============================================================
class CurveChart(QWidget):
    """实时滚动 0-100 百分比曲线图。

    - MODE_TOTAL：单条总体利用率曲线，颜色随数值渐变（绿→黄→橙→红）
    - MODE_PER_CORE：每个逻辑核心一条曲线（固定色相区分）
    - 右键菜单切换显示模式
    """

    MODE_TOTAL = "total"
    MODE_PER_CORE = "per_core"

    def __init__(self, parent=None, max_points=60, title="", base_color=None,
                 mode=MODE_PER_CORE, context_menu=True):
        super().__init__(parent)
        self._max_points = max_points
        self._title = title
        self._mode = mode
        self._base_color = QColor(base_color) if base_color else QColor(34, 197, 94)

        self._total_data = collections.deque([0.0] * max_points, maxlen=max_points)
        self._series = []            # 每核心 deque
        self._series_colors = []     # 每核心固定颜色

        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        if context_menu:
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_context_menu)

    @property
    def mode(self):
        return self._mode

    def set_mode(self, mode):
        if mode not in (self.MODE_TOTAL, self.MODE_PER_CORE):
            return
        self._mode = mode
        self.update()

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        act_total = menu.addAction("总体利用率（汇总）")
        act_total.setCheckable(True)
        act_total.setChecked(self._mode == self.MODE_TOTAL)
        act_per = menu.addAction("逻辑处理器（每核心）")
        act_per.setCheckable(True)
        act_per.setChecked(self._mode == self.MODE_PER_CORE)
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == act_total:
            self.set_mode(self.MODE_TOTAL)
        elif chosen == act_per:
            self.set_mode(self.MODE_PER_CORE)

    # ---------- 数据输入 ----------
    def push(self, value):
        """追加数据：标量 → 总体；列表 → 每核心"""
        if isinstance(value, (list, tuple)):
            self._push_per_core(value)
        else:
            self._total_data.append(float(value))
        self.update()

    def _push_per_core(self, values):
        n = len(values)
        if n != len(self._series):
            self._series = [
                collections.deque([0.0] * self._max_points, maxlen=self._max_points)
                for _ in range(n)
            ]
            self._series_colors = self._generate_core_colors(n)
        for i, v in enumerate(values):
            self._series[i].append(min(max(float(v), 0.0), 100.0))

    @staticmethod
    def _generate_core_colors(n):
        colors = []
        for i in range(n):
            hue = int(360.0 * i / n) if n > 1 else 160
            colors.append(QColor.fromHsv(hue, 200, 230))
        return colors

    # ---------- 颜色映射 ----------
    def _target_color(self, pct):
        pct = min(max(pct, 0.0), 100.0)
        GREEN = (34, 197, 94)
        YELLOW = (234, 179, 8)
        ORANGE = (245, 158, 11)
        RED = (239, 68, 68)

        def _lerp(c1, c2, t):
            return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))

        if pct < 60:
            return QColor(*_lerp(GREEN, YELLOW, pct / 60.0))
        elif pct < 80:
            return QColor(*_lerp(YELLOW, ORANGE, (pct - 60) / 20.0))
        elif pct < 90:
            return QColor(*_lerp(ORANGE, RED, (pct - 80) / 10.0))
        else:
            return QColor(*_lerp(RED, (255, 0, 0), (pct - 90) / 10.0))

    # ---------- 绘制 ----------
    def _grid_colors(self):
        dark = QApplication.palette().window().color().lightness() < 128
        if not dark:
            return QColor("#E3E7F0"), QColor("#C7CFDE"), QColor("#98A0B3")
        return QColor("#282840"), QColor("#35355a"), QColor("#606080")

    def _geometry(self):
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 42, 12, 8, 22
        return w, h, ml, mr, mt, mb, w - ml - mr, h - mt - mb

    def _point_at(self, i, val, ml, mt, cw, ch):
        x = ml + i * cw / (self._max_points - 1)
        y = mt + ch * (1.0 - min(max(val, 0.0), 100.0) / 100.0)
        return QPointF(x, y)

    def _draw_grid(self, painter, ml, mr, mt, mb, cw, ch, h):
        grid_c, mid_c, txt_c = self._grid_colors()
        painter.setPen(QPen(grid_c, 0.5))
        for pct in (25, 50, 75):
            y = mt + ch * (1.0 - pct / 100.0)
            painter.drawLine(QPointF(ml, y), QPointF(ml + cw, y))
        painter.setPen(QPen(mid_c, 0.5))
        painter.drawLine(QPointF(ml, mt + ch * 0.5), QPointF(ml + cw, mt + ch * 0.5))

        painter.setPen(txt_c)
        painter.setFont(QFont("Segoe UI", 8))
        for pct in (0, 100):
            y = mt + ch * (1.0 - pct / 100.0)
            painter.drawText(QRectF(0, y - 7, ml - 6, 14), Qt.AlignRight | Qt.AlignVCenter, f"{pct}%")
        painter.drawText(QRectF(ml, h - mb + 4, 40, 14), Qt.AlignLeft, "60s")
        painter.drawText(QRectF(ml + cw - 24, h - mb + 4, 24, 14), Qt.AlignRight, "0")

    def _draw_total(self, painter, ml, mt, mb, cw, ch):
        data = list(self._total_data)
        if len(data) < 2:
            return
        pts = [self._point_at(i, v, ml, mt, cw, ch) for i, v in enumerate(data)]
        line_color = self._target_color(data[-1])

        fill = QPainterPath()
        fill.moveTo(pts[0].x(), mt + ch)
        for pt in pts:
            fill.lineTo(pt)
        fill.lineTo(pts[-1].x(), mt + ch)
        fill.closeSubpath()
        grad = QLinearGradient(0, mt, 0, mt + ch)
        grad.setColorAt(0.0, QColor(line_color.red(), line_color.green(), line_color.blue(), 70))
        grad.setColorAt(1.0, QColor(line_color.red(), line_color.green(), line_color.blue(), 5))
        painter.fillPath(fill, grad)

        pen = QPen(line_color, 1.5)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        for i in range(len(pts) - 1):
            painter.drawLine(pts[i], pts[i + 1])
        painter.drawEllipse(pts[-1], 3, 3)

    def _draw_per_core(self, painter, ml, mt, mb, cw, ch):
        for idx, ser in enumerate(self._series):
            data = list(ser)
            if len(data) < 2:
                continue
            color = self._series_colors[idx] if idx < len(self._series_colors) else QColor("#60A5FA")
            pen = QPen(color, 1.0)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            prev = None
            for i, v in enumerate(data):
                pt = self._point_at(i, v, ml, mt, cw, ch)
                if prev:
                    painter.drawLine(prev, pt)
                prev = pt

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QApplication.palette().window().color())

        w, h, ml, mr, mt, mb, cw, ch = self._geometry()
        self._draw_grid(painter, ml, mr, mt, mb, cw, ch, h)
        if self._mode == self.MODE_PER_CORE:
            self._draw_per_core(painter, ml, mt, mb, cw, ch)
        else:
            self._draw_total(painter, ml, mt, mb, cw, ch)

        _, _, txt_c = self._grid_colors()
        painter.setPen(txt_c)
        painter.setFont(QFont("Segoe UI", 8))
        label = "逻辑处理器" if self._mode == self.MODE_PER_CORE else "总体利用率"
        painter.drawText(QRectF(ml, mt - 4, cw, 14), Qt.AlignRight, label)


# ============================================================
#  性能监视面板（本机监控：CPU / 内存 / 磁盘）
# ============================================================
class PerformancePanel(QWidget):
    """性能监视器面板：CPU 型号 + 指标 + CPU/内存曲线 + 磁盘用量。

    数据源为 psutil 本机采样；UI 通过 QTimer 每 1 秒刷新，不阻塞主线程。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

        # 预热 psutil（首次 cpu_percent 会返回占位值）
        self._cpu_model = self._get_cpu_model()
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1000)

        self._refresh()
        self._apply_style()

    def _get_cpu_model(self):
        try:
            m = platform.processor()
            if m and m.strip():
                return m.strip()
        except Exception:
            pass
        try:
            # Linux 回退
            import subprocess
            out = subprocess.check_output(
                "cat /proc/cpuinfo 2>/dev/null | grep -m1 'model name' | cut -d: -f2",
                shell=True,
            ).decode("utf-8", "ignore").strip()
            if out:
                return out
        except Exception:
            pass
        return "未知 CPU"

    def _fmt_mem(self, mb):
        try:
            mb = int(mb)
            if mb >= 1024:
                return f"{mb/1024:.1f} GB"
            return f"{mb} MB"
        except Exception:
            return "获取中..."

    def _fmt_bytes(self, b):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(b) < 1024.0:
                return f"{b:.1f} {unit}" if unit != "B" else f"{int(b)} B"
            b /= 1024.0
        return f"{b:.1f} PB"

    def _init_ui(self):
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(20, 16, 20, 16)
        vlay.setSpacing(12)

        # 标题
        title = QLabel("性能")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#000000; background:transparent;")
        vlay.addWidget(title)

        # CPU 型号
        self._cpu_model_label = QLabel(self._get_cpu_model())
        self._cpu_model_label.setWordWrap(True)
        self._cpu_model_label.setStyleSheet("font-size:14px; color:#333; background:transparent;")
        vlay.addWidget(self._cpu_model_label)

        # 四列指标
        metrics = QWidget()
        mh = QHBoxLayout(metrics)
        mh.setContentsMargins(0, 4, 0, 0)
        mh.setSpacing(20)

        def _metric(title_text, value_ref):
            col = QWidget()
            c = QVBoxLayout(col)
            c.setContentsMargins(0, 0, 0, 0)
            c.setSpacing(2)
            t = QLabel(title_text)
            t.setStyleSheet("font-size:11px; color:#888; background:transparent;")
            c.addWidget(t)
            val = QLabel("--")
            val.setStyleSheet("font-size:22px; font-weight:bold; color:#000; background:transparent;")
            setattr(self, value_ref, val)
            c.addWidget(val)
            mh.addWidget(col)

        _metric("利用率", "_cpu_pct_label")
        _metric("速度", "_cpu_freq_label")
        _metric("进程", "_proc_count_label")
        _metric("运行时间", "_uptime_label")
        mh.addStretch()
        vlay.addWidget(metrics)

        # CPU 曲线图
        self._cpu_chart = CurveChart(max_points=60)
        self._cpu_chart.setMinimumHeight(150)
        vlay.addWidget(self._cpu_chart, 1)

        # 底部：内存曲线 + 磁盘
        bottom = QWidget()
        bh = QHBoxLayout(bottom)
        bh.setContentsMargins(0, 0, 0, 0)
        bh.setSpacing(12)

        # 内存卡
        mem_card = QWidget()
        mv = QVBoxLayout(mem_card)
        mv.setContentsMargins(0, 0, 0, 0)
        mv.setSpacing(4)
        mt = QLabel("内存")
        mt.setStyleSheet("font-size:13px; font-weight:bold; color:#333; background:transparent;")
        mv.addWidget(mt)
        self._mem_label = QLabel("-- / --")
        self._mem_label.setStyleSheet("font-size:13px; color:#000; background:transparent;")
        mv.addWidget(self._mem_label)
        self._mem_chart = CurveChart(max_points=60, base_color=QColor(245, 158, 11),
                                     mode=CurveChart.MODE_TOTAL, context_menu=False)
        self._mem_chart.setMinimumHeight(110)
        mv.addWidget(self._mem_chart, 1)
        bh.addWidget(mem_card, 1)

        # 磁盘卡
        disk_card = QWidget()
        dv = QVBoxLayout(disk_card)
        dv.setContentsMargins(0, 0, 0, 0)
        dv.setSpacing(4)
        dt = QLabel("磁盘")
        dt.setStyleSheet("font-size:13px; font-weight:bold; color:#333; background:transparent;")
        dv.addWidget(dt)
        self._disk_label = QLabel("-- / --")
        self._disk_label.setStyleSheet("font-size:13px; color:#000; background:transparent;")
        dv.addWidget(self._disk_label)
        self._disk_bar = QProgressBar()
        self._disk_bar.setRange(0, 100)
        self._disk_bar.setFixedHeight(14)
        self._disk_bar.setTextVisible(False)
        dv.addWidget(self._disk_bar)
        dv.addStretch()
        bh.addWidget(disk_card, 1)

        vlay.addWidget(bottom, 1)

    def _refresh(self):
        try:
            # CPU
            cpu = psutil.cpu_percent(interval=None)
            per = psutil.cpu_percent(interval=None, percpu=True)
            self._cpu_pct_label.setText(f"{cpu:.0f}%")
            self._cpu_chart.push(cpu)
            if per:
                self._cpu_chart.push(per)

            # 频率
            freq = psutil.cpu_freq()
            if freq:
                self._cpu_freq_label.setText(f"{freq.current/1000:.2f} GHz")
            else:
                self._cpu_freq_label.setText("--")

            # 进程数
            self._proc_count_label.setText(str(len(psutil.pids())))

            # 运行时间
            uptime = time.time() - psutil.boot_time()
            h = int(uptime // 3600)
            m = int((uptime % 3600) // 60)
            self._uptime_label.setText(f"{h}h{m}m")

            # 内存
            mem = psutil.virtual_memory()
            self._mem_label.setText(
                f"{self._fmt_mem(mem.used)} / {self._fmt_mem(mem.total)}"
            )
            self._mem_chart.push(mem.percent)

            # 磁盘
            disk = psutil.disk_usage("/")
            self._disk_label.setText(
                f"{self._fmt_bytes(disk.used)} / {self._fmt_bytes(disk.total)}"
            )
            self._disk_bar.setValue(int(disk.percent))
        except Exception:
            pass

    def _apply_style(self):
        dark = QApplication.palette().window().color().lightness() < 128
        bg = "#1f1f1f" if dark else "#fafafa"
        self.setStyleSheet(f"PerformancePanel {{ background: {bg}; }}")
        self._disk_bar.setStyleSheet(
            "QProgressBar { background:#e0e0e0; border:none; border-radius:3px; }"
            "QProgressBar::chunk { background:#10B981; border-radius:3px; }"
        )

    def stop(self):
        """停止采样定时器（窗口关闭时调用）"""
        if self._timer:
            self._timer.stop()


def create_task_manager_window(parent=None):
    """用 EMdiSubWindow 创建「任务管理器」窗口（返回后需调用 show()）。"""
    win = EMdiSubWindow(parent, "任务管理器",
                        allow_maxmin_buttons=True, allow_resize=True)
    win.resize(760, 520)
    panel = PerformancePanel()
    win.addWidget(panel)
    # 窗口关闭时停止采样
    win.destroyed.connect(panel.stop)
    return win


if __name__ == "__main__":
    app = QApplication([])
    w = create_task_manager_window()
    w.show()
    app.exec()
