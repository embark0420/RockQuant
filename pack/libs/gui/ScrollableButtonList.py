from pack.libs.gui.button import *
from pack.libs.gui.InvertedImageButton import *
from pack.libs.gui.widget import *
from pack.libs.gui.QtPack import *
from pack.libs.gui.frame import *
from pack.libs.gui.Separator import *
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtWidgets import QScroller      # 不再使用，但保留导入不报错即可


class SmoothScrollArea(QScrollArea):
    """支持缓动曲线滚动的滚动区域
    - 使用 QTimer 驱动帧动画而非 QPropertyAnimation，避免 setEndValue 造成的跳变
    - 每帧按指数衰减逼近目标，天然支持方向切换和连续滚动无卡顿
    - 支持触摸板高精度 pixelDelta 滚动
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_value = 0
        self._smooth_factor = 0.35       # 每帧逼近比例（越高越快）
        self._dead_zone = 0.5            # 停止阈值（像素）
        self._min_step = 1.0             # 最小步长
        self._max_step = 80.0            # 最大步长（防止一次滚轮飞太远）

        self._anim_timer = QTimer(self)
        self._anim_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._anim_timer.timeout.connect(self._tick)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # ---- 帧动画 ----

    def _tick(self):
        """每帧向目标值逼近一步"""
        bar = self.verticalScrollBar()
        current = bar.value()
        diff = self._target_value - current

        if abs(diff) < self._dead_zone:
            bar.setValue(self._target_value)
            self._anim_timer.stop()
            return

        # 指数衰减：step = diff * factor，越靠近越慢（天然缓动）
        step = diff * self._smooth_factor
        # 限制步长范围
        if abs(step) < self._min_step:
            step = self._min_step if diff > 0 else -self._min_step
        elif abs(step) > self._max_step:
            step = self._max_step if diff > 0 else -self._max_step

        bar.setValue(int(current + step))

    def _clamp_target(self, value: int) -> int:
        return max(0, min(value, self.verticalScrollBar().maximum()))

    def _kick(self):
        """启动 tick 定时器（若未运行）"""
        if not self._anim_timer.isActive():
            self._anim_timer.start(16)  # ~60fps

    # ---- 公共 API ----

    def smooth_scroll_to(self, value: int, duration: int = 800, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
        """平滑滚动到绝对位置（duration 和 easing 保留兼容，实际由 smooth_factor 控制速率）"""
        self._target_value = self._clamp_target(value)
        self._kick()

    def scroll_by(self, delta: int, duration: int = 400, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
        """相对滚动 delta 像素，累加到当前目标"""
        self._target_value = self._clamp_target(self._target_value + delta)
        self._kick()

    def wheelEvent(self, event):
        """滚轮/触摸板事件：增量累加到目标，方向切换零延迟"""
        pd = event.pixelDelta()
        if pd.y() != 0:
            self.scroll_by(-pd.y())
            event.accept()
            return

        ad = event.angleDelta().y()
        if ad == 0:
            event.ignore()
            return

        steps = ad / 120.0
        single = self.verticalScrollBar().singleStep()
        if single <= 0:
            single = 20
        pixel_delta = int(-steps * single * 3)  # *3 而非 *8，避免一次滚动太远

        if pixel_delta != 0:
            self.scroll_by(pixel_delta)

        event.accept()

    def scroll_to_top(self, duration: int = 400, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
        self.smooth_scroll_to(0, duration, easing)

    def scroll_to_bottom(self, duration: int = 400, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
        self.smooth_scroll_to(self.verticalScrollBar().maximum(), duration, easing)


class ScrollableButtonList(Frame):
    buttonClicked = pyqtSignal(object)

    def __init__(self, parent=None, border_radius: int = 0, border_width: int = 0,transparent = 255):
        super().__init__(parent,transparent=transparent)
        self.border_radius = border_radius
        self.border_width = border_width
        self.initUI()
        # 移除 QScroller 相关设置，避免拖动冲突和属性错误

    def initUI(self):
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建支持平滑滚动的区域
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent;
            }
            QScrollBar:vertical {
                width: 6px;
                background: rgba(0, 0, 0, 0);
                border-radius: 3px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 100, 100, 100);
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(120, 120, 120, 150);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)

        # 创建包含按钮的容器
        self.button_container = QWidget()
        self.button_container.setStyleSheet("background: transparent;")
        self.button_layout = QVBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(2)
        self.button_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.button_container)
        self.main_layout.addWidget(self.scroll_area)

    def addButton(self, text, onClick=None, button_height: int = 25):
        """动态添加按钮"""
        button = TaskButton(border_width=0, text_alignment="left",border_radius = 0)
        button.setText(f"{text}")
        button.setObjectName(str(text))
        button.setFixedHeight(button_height)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if onClick is not None:
            def wrapped_click():
                onClick()
                self.buttonClicked.emit(text)
            button.clicked.connect(wrapped_click)

        self.button_layout.addWidget(button)
    
    def addRippleButton(self, text, onClick=None, button_height: int = 25):
        """动态添加按钮"""
        button = RippleButton(border_width=0, text_align=Qt.AlignmentFlag.AlignVCenter,corner_radius = 0)
        button.setText(f"{text}")
        button.setObjectName(str(text))
        button.setFixedHeight(button_height)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if onClick is not None:
            def wrapped_click():
                onClick()
                self.buttonClicked.emit(text)
            button.clicked.connect(wrapped_click)

        self.button_layout.addWidget(button)

    def addTaskButton(self, text, onClick=None, button_height: int = 25):
        """动态添加任务按钮"""
        button = TaskButtonWithIcon()
        button.setText(f"   {text}")
        button.setObjectName(str(text))
        button.setFixedHeight(button_height)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if onClick is not None:
            def wrapped_click():
                onClick()
                self.buttonClicked.emit(text)
            button.clicked.connect(wrapped_click)

        self.button_layout.addWidget(button)

    def addWidget(self, widget):
        self.button_layout.addWidget(widget)

    def addSeparator(self):
        from pack.libs.gui.Separator import Separator
        self.button_layout.addWidget(Separator(None))

    def clearButtons(self):
        """清除所有按钮"""
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def scroll_to_top(self, duration: int = 300, easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic):
        """滚动到顶部"""
        self.scroll_area.scroll_to_top(duration, easing)

    def scroll_to_bottom(self, duration: int = 300, easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic):
        """滚动到底部"""
        self.scroll_area.scroll_to_bottom(duration, easing)

    def smooth_scroll_to(self, index: int, duration: int = 300,
                         easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic):
        """平滑滚动到指定索引的按钮"""
        if index < 0 or index >= self.button_layout.count():
            return

        target_button = self.button_layout.itemAt(index).widget()
        if target_button:
            target_y = target_button.pos().y()
            self.scroll_area.smooth_scroll_to(target_y, duration, easing)