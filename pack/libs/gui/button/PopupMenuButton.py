from pack.libs.gui.PopupMenuPanel import PopupMenuPanel
from pack.libs.gui.button import *
from pack.libs.gui.RippleButton import *
from pack.libs.gui.TaskButton import *
from pack.libs.gui.QtPack import *


class RipplePopupButton(RippleButton):
    """带内联菜单的按钮 - 宽松版"""
    def __init__(
        self, 
        text: str = "", 
        parent: QWidget = None,
        border_width : int = 0,
        border_radius : int = 3,
        direction: str = "bottom",
        text_alignment = Qt.AlignmentFlag.AlignCenter,
        width : int = 190
    ):
        super().__init__(text, parent,border_radius,border_width,text_align=text_alignment)

        self.widthc = width
        self._direction = direction
        
        self._menu_panel = PopupMenuPanel(self.window() if parent else self,self.widthc)
        self._menu_panel.hide()

        # 点击按钮切换菜单
        self.clicked.connect(self._toggle_menu)

        # 全局事件过滤器 - 点击外部关闭
        QApplication.instance().installEventFilter(self)

    def addButton(self, text: str, onClick=None, alignment=Qt.AlignLeft):
        """添加菜单项"""
        self._menu_panel.addButton(text, onClick, alignment=alignment)

    def addSeparator(self):
        """添加分隔线"""
        self._menu_panel.addSeparator()
    
    def clear_menu(self):
        """清空菜单"""
        self._menu_panel.clear()
    
    def _toggle_menu(self):
        if self._menu_panel.isVisible():
            self._menu_panel.hide()
        else:
            self._show_menu()
    
    def _show_menu(self):
        """显示菜单，根据 direction 从相反方向滑入"""
        btn_global = self.mapToGlobal(QPoint(0, 0))
        # 用 sizeHint 而非 height()，因为面板隐藏时 height() 可能未更新
        menu_width = self._menu_panel.sizeHint().width()
        menu_height = self._menu_panel.sizeHint().height()

        # direction → 定位位置 & 滑入方向（从相反方向滑入）
        if self._direction == "bottom":
            x = btn_global.x() - 13
            y = btn_global.y() + self.height() - 10
            slide_from = "top"
        elif self._direction == "top":
            x = btn_global.x() - 13
            y = btn_global.y() - menu_height + 10
            slide_from = "bottom"
        elif self._direction == "right":
            x = btn_global.x() + self.width()
            y = btn_global.y()
            slide_from = "left"
        elif self._direction == "left":
            x = btn_global.x() - menu_width + 10
            y = btn_global.y() - 10
            slide_from = "right"
        else:
            x = btn_global.x()
            y = btn_global.y() + self.height()
            slide_from = "top"

        self._menu_panel.show_at(QPoint(x, y), slide_from)
    
    def _on_action(self, text: str):
        self._menu_panel.hide()
    
    def _on_exit(self, text: str):
        self._menu_panel.hide()
    
    def eventFilter(self, obj, event):
        """点击其他地方关闭菜单"""
        if event.type() == QEvent.MouseButtonPress:
            if self._menu_panel.isVisible():
                pos = event.globalPos()
                # 检查点击是否在菜单面板或按钮上
                in_menu = self._menu_panel.geometry().contains(pos)
                in_btn = self.geometry().contains(self.mapFromGlobal(pos))
                if not in_menu and not in_btn:
                    self._menu_panel.hide()
        return super().eventFilter(obj, event)
    
    def set_direction(self, direction: str):
        """设置菜单弹出方向 - 忽略无效值"""
        valid = ["bottom", "top", "left", "right"]
        if direction in valid:
            self._direction = direction
class PopupButton(Button):
    """带内联菜单的按钮 - 宽松版"""
    def __init__(
        self, 
        text: str = "", 
        parent: QWidget = None,
        border_width : int = 1,
        border_radius : int = 3,
        direction: str = "bottom",
        text_alignment:str = "center",
        width : int = 190,
        transparent : int = 255
    ):
        super().__init__(text, parent,border_radius,border_width,text_alignment=text_alignment,transparent = transparent)

        self.widthc = width
        self._direction = direction
        
        self._menu_panel = PopupMenuPanel(self.window() if parent else self,self.widthc)
        self._menu_panel.hide()

        # 点击按钮切换菜单
        self.clicked.connect(self._toggle_menu)

        # 全局事件过滤器 - 点击外部关闭
        QApplication.instance().installEventFilter(self)

    def addButton(self, text: str, onClick=None, alignment=Qt.AlignLeft):
        """添加菜单项"""
        self._menu_panel.addButton(text, onClick, alignment=alignment)

    def addSeparator(self):
        """添加分隔线"""
        self._menu_panel.addSeparator()
    
    def clear_menu(self):
        """清空菜单"""
        self._menu_panel.clear()
    
    def _toggle_menu(self):
        if self._menu_panel.isVisible():
            self._menu_panel.hide()
        else:
            self._show_menu()
    
    def _show_menu(self):
        """显示菜单，根据 direction 从相反方向滑入"""
        btn_global = self.mapToGlobal(QPoint(0, 0))
        # 用 sizeHint 而非 height()，因为面板隐藏时 height() 可能未更新
        menu_width = self._menu_panel.sizeHint().width()
        menu_height = self._menu_panel.sizeHint().height()

        # direction → 定位位置 & 滑入方向（从相反方向滑入）
        if self._direction == "bottom":
            x = btn_global.x() - 13
            y = btn_global.y() + self.height() - 10
            slide_from = "top"
        elif self._direction == "top":
            x = btn_global.x() - 13
            y = btn_global.y() - menu_height + 10
            slide_from = "bottom"
        elif self._direction == "right":
            x = btn_global.x() + self.width()
            y = btn_global.y()
            slide_from = "left"
        elif self._direction == "left":
            x = btn_global.x() - menu_width + 10
            y = btn_global.y() - 10
            slide_from = "right"
        else:
            x = btn_global.x()
            y = btn_global.y() + self.height()
            slide_from = "top"

        self._menu_panel.show_at(QPoint(x, y), slide_from)
    
    def _on_action(self, text: str):
        self._menu_panel.hide()
    
    def _on_exit(self, text: str):
        self._menu_panel.hide()
    
    def eventFilter(self, obj, event):
        """点击其他地方关闭菜单"""
        if event.type() == QEvent.MouseButtonPress:
            if self._menu_panel.isVisible():
                pos = event.globalPos()
                # 检查点击是否在菜单面板或按钮上
                in_menu = self._menu_panel.geometry().contains(pos)
                in_btn = self.geometry().contains(self.mapFromGlobal(pos))
                if not in_menu and not in_btn:
                    self._menu_panel.hide()
        return super().eventFilter(obj, event)
    
    def set_direction(self, direction: str):
        """设置菜单弹出方向 - 忽略无效值"""
        valid = ["bottom", "top", "left", "right"]
        if direction in valid:
            self._direction = direction
class TaskPopupButton(TaskButton):
    """带内联菜单的按钮 - 宽松版"""
    def __init__(
        self, 
        text: str = "", 
        parent: QWidget = None,
        border_width : int = 1,
        border_radius : int = 3,
        direction: str = "bottom",
        text_alignment:str = "center",
        width : int = 190
    ):
        super().__init__(text, parent,border_radius,border_width,text_alignment=text_alignment)

        self.widthc = width
        self._direction = direction
        
        self._menu_panel = PopupMenuPanel(self.window() if parent else self,self.widthc)
        self._menu_panel.hide()

        # 点击按钮切换菜单
        self.clicked.connect(self._toggle_menu)

        # 全局事件过滤器 - 点击外部关闭
        QApplication.instance().installEventFilter(self)

    def addButton(self, text: str, onClick=None, alignment=Qt.AlignLeft):
        """添加菜单项"""
        self._menu_panel.addButton(text, onClick, alignment=alignment)

    def addSeparator(self):
        """添加分隔线"""
        self._menu_panel.addSeparator()
    
    def clear_menu(self):
        """清空菜单"""
        self._menu_panel.clear()
    
    def _toggle_menu(self):
        if self._menu_panel.isVisible():
            self._menu_panel.hide()
        else:
            self._show_menu()
    
    def _show_menu(self):
        """显示菜单，根据 direction 从相反方向滑入"""
        btn_global = self.mapToGlobal(QPoint(0, 0))
        # 用 sizeHint 而非 height()，因为面板隐藏时 height() 可能未更新
        menu_width = self._menu_panel.sizeHint().width()
        menu_height = self._menu_panel.sizeHint().height()

        # direction → 定位位置 & 滑入方向（从相反方向滑入）
        if self._direction == "bottom":
            x = btn_global.x() - 13
            y = btn_global.y() + self.height() - 10
            slide_from = "top"
        elif self._direction == "top":
            x = btn_global.x() - 13
            y = btn_global.y() - menu_height + 10
            slide_from = "bottom"
        elif self._direction == "right":
            x = btn_global.x() + self.width()
            y = btn_global.y()
            slide_from = "left"
        elif self._direction == "left":
            x = btn_global.x() - menu_width + 10
            y = btn_global.y() - 10
            slide_from = "right"
        else:
            x = btn_global.x()
            y = btn_global.y() + self.height()
            slide_from = "top"

        self._menu_panel.show_at(QPoint(x, y), slide_from)
    
    def _on_action(self, text: str):
        self._menu_panel.hide()
    
    def _on_exit(self, text: str):
        self._menu_panel.hide()
    
    def eventFilter(self, obj, event):
        """点击其他地方关闭菜单"""
        if event.type() == QEvent.MouseButtonPress:
            if self._menu_panel.isVisible():
                pos = event.globalPos()
                # 检查点击是否在菜单面板或按钮上
                in_menu = self._menu_panel.geometry().contains(pos)
                in_btn = self.geometry().contains(self.mapFromGlobal(pos))
                if not in_menu and not in_btn:
                    self._menu_panel.hide()
        return super().eventFilter(obj, event)
    
    def set_direction(self, direction: str):
        """设置菜单弹出方向 - 忽略无效值"""
        valid = ["bottom", "top", "left", "right"]
        if direction in valid:
            self._direction = direction
