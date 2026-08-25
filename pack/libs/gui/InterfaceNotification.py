
from pack.libs.gui.frame import *
from pack.libs.gui.QtPack import *
from pack.libs.gui.shadow import *
from pack.libs.gui.label import *
from pack.libs.gui.widget import *
from pack.libs.gui.Separator import *
from pack.libs.gui.button import *

from pack.libs.fonts.SegoeAssets import *

import time

class InterfaceNotification(AnimatedWidget):
    def __init__ (self,title : str = "none", text : str = "None", parent : QWidget = None, showTime : int = 0):
        super().__init__(parent)
        self.title = title
        self.text  = text 
        self._show_time = showTime
        self._start_time = time.time()
        self._is_closing = False
        Shadow.Show(self,r=15,color = None, dy = 3)

        self.__initgui__()

        if self._show_time > 0:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._check_timeout)
            self._timer.start(1000)

    def __initgui__(self):
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20,15,20,15)
        layout.setSpacing(5)

        title = Label(self.title,None,15)
        self.copy_button = Button("\uE8C8",self,border_width = 0)
        self.copy_button.setFont(SegoeMDL2Assets.font)

        layout.addWidget(title)
        layout.addWidget(Separator())
        layout.addWidget(QLabel(self.text))
        
    def paintEvent(self, arg__1):
        self.copy_button.setGeometry(self.width()-35,5,30,30)

        return super().paintEvent(arg__1)

    def _check_timeout(self):
        if self._is_closing:
            return
        elapsed = time.time() - self._start_time
        if elapsed >= self._show_time:
            self.closeE()

    def closeE(self):
        if self._is_closing:
            return
        self._is_closing = True
        if hasattr(self, '_timer'):
            self._timer.stop()
        
        self.set_scale_animation(1, 0, 300)
        self.set_opacity_animation(1, 0, 300, finished=self.deleteLater)