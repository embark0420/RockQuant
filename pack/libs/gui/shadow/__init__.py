from pack.libs.gui.QtPack import *

class Shadow:
    """
    # 阴影效果
    - Shadow_Show   显示阴影
    - Shadow_Back   隐藏阴影
    - Shadow_Number  数字阴影(在固定值上来回切换)
    - Effect        效果
    - Show          显示阴影动画
    - Back          隐藏阴影动画
    - Number        数字阴影动画(在固定值上来回切换)
    - Static        静态阴影
    """
    class Shadow_Show(QGraphicsDropShadowEffect):
        """
        # 显示阴影
        - parent : 父控件
        - color  : 阴影颜色
        - dx     : x轴偏移量
        - dy     : y轴偏移量
        - r      : 阴影半径
        """
        
        def __init__(self, parent : QWidget = None ,color = None,dx = 0, dy = 0, r = 20,Duration : int = 500) -> None:
            super(Shadow.Shadow_Show, self).__init__(parent)
            self.r = r
            self.Duration = Duration
            self.setBlurRadius(self.r)
            self.setOffset(dx,dy)
            #set color
            if color == None:
                self.update_colors()
                QApplication.instance().paletteChanged.connect(self.update_colors)
            else:
                self.setColor(color)
                    
                    
            self._radius = 0
                    
            self.animation = QPropertyAnimation(self)
            self.animation.setTargetObject(self)
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.r)
            self.animation.setDuration(self.Duration)
            self.animation.setEasingCurve(QEasingCurve.OutBack)
            self.animation.setPropertyName(b'radius')
        def update_colors(self):
            palette = QApplication.palette()
            is_dark = palette.window().color().lightness() < 128
            
            if is_dark:  
                self.setColor(QColor(0,0,0))
            else:
                self.setColor(QColor("#616161"))


        def start(self):
            self.animation.start()

        @pyqtProperty(int)
        def radius(self):
            return self._radius

        @radius.setter
        def radius(self, r):
            self._radius = r
            self.setBlurRadius(r)
    class Shadow_Back(QGraphicsDropShadowEffect):
        """
        # 隐藏阴影
        - parent : 父控件
        - color  : 阴影颜色
        - dx     : x轴偏移量
        - dy     : y轴偏移量
        - r      : 阴影半径
        """
        def __init__(self, parent : QWidget = None ,color : QColor = None,dx = 0, dy = 0,r = 20,Duration : int = 500) -> None:
            super(Shadow.Shadow_Back, self).__init__(parent)
            self.r = r
            self.Duration = Duration
            self.setBlurRadius(self.r)
            self.setOffset(dx,dy)
            #set color
            if color == None:
                self.update_colors()
                QApplication.instance().paletteChanged.connect(self.update_colors)
            else:
                self.setColor(Qt.black)
            self._radius = 0
                    
            self.animation = QPropertyAnimation(self)
            self.animation.setTargetObject(self)
            self.animation.setStartValue(self.r)  # 一次循环时间
            self.animation.setEndValue(0)
            self.animation.setEasingCurve(QEasingCurve.OutExpo)
            self.animation.setDuration(self.Duration)
            self.animation.setPropertyName(b'radius')
        def update_colors(self):
            palette = QApplication.palette()
            is_dark = palette.window().color().lightness() < 128
            
            if is_dark:  
                self.setColor(QColor(0,0,0))
            else:
                self.setColor(QColor(134,134,134))
        def start(self):
            self.animation.start()

        @pyqtProperty(int)
        def radius(self):
            return self._radius

        @radius.setter
        def radius(self, r):
            self._radius = r
            self.setBlurRadius(r)

    class Shadow_Number(QGraphicsDropShadowEffect):
        """
        # 数字阴影(在固定值上来回切换)
        - parent : 父控件
        - color  : 阴影颜色
        - dx     : x轴偏移量
        - dy     : y轴偏移量
        - r_Initial : 初始值
        - r_End : 结束值

        """
        def __init__(self, parent : QWidget = None ,color : QColor = Qt.black,dx = 0, dy = 3,r_Initial = 20, r_End = 0,Duration : int = 500) -> None:
            super(Shadow.Shadow_Number, self).__init__(parent)
            self.r = r_Initial
            self.r_off = r_End
            self.Duration = Duration
            self.setBlurRadius(self.r)
            self.setOffset(dx,dy)
            #set color
            if color == None:
                self.update_colors()
                QApplication.instance().paletteChanged.connect(self.update_colors)
            else:
                self.setColor(Qt.black)
                    
            self._radius = 0
                    
            self.animation = QPropertyAnimation(self)
            self.animation.setTargetObject(self)
            self.animation.setStartValue(self.r)  # 一次循环时间
            self.animation.setEndValue(self.r_off)
            self.animation.setEasingCurve(QEasingCurve.OutExpo)
            self.animation.setDuration(self.Duration)
            self.animation.setPropertyName(b'radius')
        def update_colors(self):
            palette = QApplication.palette()
            is_dark = palette.window().color().lightness() < 128
            
            if is_dark:  
                self.setColor(QColor(0,0,0))
            else:
                self.setColor(QColor(134,134,134))
        def setValue(self, Value : tuple) -> tuple:
            """
            # 设置值
            * Value : tuple
            * Value[0] : 初始值
            * Value[1] : 结束值 
            """
            self.r = Value[0]
            self.r_off = Value[1]

        def start(self):
            self.animation.start()

        @pyqtProperty(int)
        def radius(self):
            return self._radius

        @radius.setter
        def radius(self, r):
            self._radius = r
            self.setBlurRadius(r)
    class Effect(QGraphicsDropShadowEffect):
        def __init__(self, parent : QWidget = None ,color : QColor = Qt.black,dx = 0, dy = 0,r = 20) -> None:
            super(Shadow.Effect, self).__init__(parent)
            self.r = r
            self.setBlurRadius(self.r)
            self.setOffset(dx,dy)
            #set color
            self.setColor(color)
            parent.setGraphicsEffect(self)
    class EffectC(QGraphicsDropShadowEffect):
        def __init__(self, parent : QWidget = None ,dx = 0, dy = 0,r = 20) -> None:
            super(Shadow.EffectC, self).__init__(parent)
            self.r = r
            self.setBlurRadius(self.r)
            self.setOffset(dx,dy)
            #set color
            parent.setGraphicsEffect(self)

            self.update_colors()
            QApplication.instance().paletteChanged.connect(self.update_colors)
        def update_colors(self):
            palette = QApplication.palette()
            is_dark = palette.window().color().lightness() < 128

            if is_dark:
                self.setColor(QColor(0, 0, 0, 255))
            else:
                self.setColor(Qt.gray)

    class Show(Shadow_Show):
        def __init__(self, parent: QWidget = None, color=Qt.black,dx = 0,dy = 0 ,r : int = 20,Duration : int = 500) -> None:
            super().__init__(parent, color,dx,dy ,r,Duration)
            parent.setGraphicsEffect(self)
            self.start()

    class Back(Shadow_Back):
        def __init__(self, parent: QWidget = None, color: QColor = Qt.red,dx = 0,dy = 0, r : int = 20,Duration : int = 500) -> None:
            super().__init__(parent, color,dx,dy, r,Duration)
            parent.setGraphicsEffect(self)
            self.start()

    class Number(Shadow_Number):
        def __init__(self, parent: QWidget = None, color: QColor = Qt.black,dx = 0,dy = 0, r_on : int = 20, r_off : int = 0,Duration : int = 500) -> None:
            super().__init__(parent, color,dx,dy, r_on, r_off,Duration)
            parent.setGraphicsEffect(self)
            self.start()


    class Static(QGraphicsDropShadowEffect):
        def __init__(self,parent : QWidget = None, r : int = 30,color = Qt.gray) -> None:
            super().__init__(parent)

            self.setOffset(0,0)
            self.setBlurRadius(r) # 阴影半径
            self.setColor(color) # 阴影颜色
                        
        def show(self, parent:QWidget = None):
            parent.setGraphicsEffect(self) # 将设置套用到button窗口中 