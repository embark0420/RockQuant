from pack.libs.gui.QtPack import *

class PropertyAnimation(QPropertyAnimation):
        def __init__ (self,parent, TargetObject, PropertyName : str, StartValue : int, EndValue : int , EasingCurve : QEasingCurve.Type,Duration : int):
            super().__init__(parent)
            self.setTargetObject(TargetObject)
            self.setPropertyName(PropertyName)
            self.setStartValue(StartValue)
            self.setEndValue(EndValue)
            self.setDuration(Duration)
            self.setEasingCurve(EasingCurve)
        
        def Animation_end_event(self, event):
            self.finished.connect(event)
            return True