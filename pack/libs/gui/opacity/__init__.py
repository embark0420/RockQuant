from pack.libs.gui.QtPack import *
from pack.libs.gui.PropertyAnimation import *
class Opacity:
        class GraphicsOpacityEffect(QGraphicsOpacityEffect):

            def __init__(self, parent : QWidget,Opacity : float = 0.5):
                super().__init__(parent)
                self.setOpacity(Opacity)
                parent.setGraphicsEffect(self)
                parent.setAutoFillBackground(True)

        class GraphicsOpacityEffect_Anim(QGraphicsOpacityEffect):
            def __init__(self, parent : QWidget = None, StartValue : int = 1,EndValue : int = 0.1 ,EasingCurve : QEasingCurve.Type = QEasingCurve.Type.InBack,Duration : int = 500):
                super().__init__(parent)
                self.setOpacity(0.5)
                parent.setGraphicsEffect(self)
                parent.setAutoFillBackground(True)

                self.Animation = PropertyAnimation(parent,self,b'opacity',StartValue,EndValue,EasingCurve,Duration)
                self.Animation.start()
                

            def Animation_team_add(self,animTeam: QSequentialAnimationGroup):
                animTeam.addAnimation(self.A)