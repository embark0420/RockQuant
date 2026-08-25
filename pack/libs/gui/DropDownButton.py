from pack.libs.gui.QtPack import *
from pack.libs.gui.shadow import *
from pack.libs.gui.button import *
from pack.libs.gui.TaskButton import *
from pack.libs.gui.ScrollableButtonList import *
from pack.libs.gui.widget import *

class ComboboxButton(Button):
    def __init__ (self, text : str = "",parent : QWidget = None,width : int = 80, height : int = 80,Direction : str = "bottom",text_alignment : str = "center",font_size : int = None) -> None:
        super().__init__(text,parent,text_alignment = text_alignment,font_size = font_size)
        self.resize(80,30)
        
        self._fixed_width = width  # None means use self.width() dynamically
        self._heights = height  # None means auto-calculate from button heights
        self.Direction = Direction
        self.clicked.connect(self.__initEvent__)
        self._init_menu_()
        
    @property
    def widths(self):
        return self._fixed_width if self._fixed_width is not None else self.width()

    @property
    def heights(self):
        """如果初始化时传入None，则根据item_list中按钮高度动态计算累积值"""
        if self._heights is None:
            total = 0
            if hasattr(self, 'item_list') and self.item_list.button_layout.count() > 0:
                for i in range(self.item_list.button_layout.count()):
                    item = self.item_list.button_layout.itemAt(i)
                    if item.widget():
                        total += item.widget().height() + 10
            return total if total > 0 else 25  # 默认最小高度
        return self._heights

    @heights.setter
    def heights(self, value):
        self._heights = value

    def _init_menu_(self):
        self._menu = PopupWidget(self)
        self._menu.setAttribute(Qt.WA_TranslucentBackground)  # 启用透明背景
        self._menu.setStyleSheet("""
        PopupWidget{
            background: transparent; 
            border: none;
        }
        """)
        self._menu.resize(self.widths,self.heights)
        self.item_list =ScrollableButtonList(self._menu,border_width=0,border_radius = 4)
        

        self.item_list.setGeometry(0,0,self.widths,self.heights)
        self.item_list.show()
    def addButton(self,text: Any, onClick: Any | None = air, button_height: int = 25):
        self.item_list.addButton(text,onClick,button_height)
        # 当heights为自动计算模式时，动态更新菜单尺寸
        if self._heights is None:
            h = self.heights
            self._menu.resize(self.widths, h)
            self.item_list.setGeometry(0, 0, self.widths, h)
    def addWidget(self,widget):
        self.item_list.addWidget(widget)
        # 当heights为自动计算模式时，动态更新菜单尺寸
        if self._heights is None:
            h = self.heights
            self._menu.resize(self.widths, h)
            self.item_list.setGeometry(0, 0, self.widths, h)
    def addRippleButton(self,text: Any, onClick: Any | None = air, button_height: int = 25):
        self.item_list.addRippleButton(text,onClick,button_height)
        # 当heights为自动计算模式时，动态更新菜单尺寸
        if self._heights is None:
            h = self.heights
            self._menu.resize(self.widths, h)
            self.item_list.setGeometry(0, 0, self.widths, h)

    def animation(self):
        """显示动画效果"""
        if hasattr(self, '_menu'):
            
            if self.Direction == "bottom":    

                self.animo = QPropertyAnimation(self._menu)
                self.animo.setTargetObject(self.item_list)
                self.animo.setPropertyName(b'geometry')
                self.animo.setStartValue(QRect(0,-120,self.widths,self.heights))
                self.animo.setEndValue(QRect(0,0,self.widths,self.heights))
                self.animo.setDuration(500)
                self.animo.setEasingCurve(QEasingCurve.Type.OutExpo)
                self.animo.start()
            else:

                if self.Direction == "top":

                    self.animo = QPropertyAnimation(self._menu)
                    self.animo.setTargetObject(self.item_list)
                    self.animo.setPropertyName(b'geometry')
                    self.animo.setStartValue(QRect(0,self.heights,self.widths,self.heights))
                    self.animo.setEndValue(QRect(0,0,self.widths,self.heights))
                    self.animo.setDuration(500)
                    self.animo.setEasingCurve(QEasingCurve.Type.OutExpo)
                    self.animo.start()

    def __initEvent__(self):
        if hasattr(self, '_menu'):
            # 动态更新菜单和item_list的尺寸，确保与按钮当前宽度同步
            w = self.widths
            h = self.heights
            self._menu.resize(w, h)
            self.item_list.setGeometry(0, 0, w, h)
            if self.Direction == "top":
                pos = self.mapToGlobal(QPoint(0, -self.heights-2))
                self._menu.move(pos)
                self._menu.show()
                self.animation()
            else:
                if self.Direction == "bottom":
                    pos = self.mapToGlobal(QPoint(0, self.height()+2))
                    self._menu.move(pos)
                    self._menu.show()
                    self.animation()
class ComboboxTaskButton(TaskButton):
    def __init__ (self, text : str = "",parent : QWidget = None,width : int = 80, height : int = 80,Direction : str = "bottom",text_alignment : str = "center",font_size : int = None) -> None:
        super().__init__(text,parent,text_alignment = text_alignment,font_size = font_size)
        self.resize(80,30)
        
        self._fixed_width = width  # None means use self.width() dynamically
        self._heights = height  # None means auto-calculate from button heights
        self.Direction = Direction
        self.clicked.connect(self.__initEvent__)
        self._init_menu_()
        
    @property
    def widths(self):
        return self._fixed_width if self._fixed_width is not None else self.width()

    @property
    def heights(self):
        """如果初始化时传入None，则根据item_list中按钮高度动态计算累积值"""
        if self._heights is None:
            total = 0
            if hasattr(self, 'item_list') and self.item_list.button_layout.count() > 0:
                for i in range(self.item_list.button_layout.count()):
                    item = self.item_list.button_layout.itemAt(i)
                    if item.widget():
                        total += item.widget().height() + 10
            return total if total > 0 else 25  # 默认最小高度
        return self._heights

    @heights.setter
    def heights(self, value):
        self._heights = value

    def _init_menu_(self):
        self._menu = PopupWidget(self)
        self._menu.setAttribute(Qt.WA_TranslucentBackground)  # 启用透明背景
        self._menu.setStyleSheet("""
        PopupWidget{
            background: transparent; 
            border: none;
        }
        """)
        self._menu.resize(self.widths,self.heights)
        self.item_list =ScrollableButtonList(self._menu,border_width=0,border_radius = 4)
        

        self.item_list.setGeometry(0,0,self.widths,self.heights)
        self.item_list.show()
    def addButton(self,text: Any, onClick: Any | None = air, button_height: int = 25):
        self.item_list.addButton(text,onClick,button_height)
        # 当heights为自动计算模式时，动态更新菜单尺寸
        if self._heights is None:
            h = self.heights
            self._menu.resize(self.widths, h)
            self.item_list.setGeometry(0, 0, self.widths, h)
    def addWidget(self,widget):
        self.item_list.addWidget(widget)
        # 当heights为自动计算模式时，动态更新菜单尺寸
        if self._heights is None:
            h = self.heights
            self._menu.resize(self.widths, h)
            self.item_list.setGeometry(0, 0, self.widths, h)
    def addRippleButton(self,text: Any, onClick: Any | None = air, button_height: int = 25):
        self.item_list.addRippleButton(text,onClick,button_height)
        # 当heights为自动计算模式时，动态更新菜单尺寸
        if self._heights is None:
            h = self.heights
            self._menu.resize(self.widths, h)
            self.item_list.setGeometry(0, 0, self.widths, h)

    def animation(self):
        """显示动画效果"""
        if hasattr(self, '_menu'):
            
            if self.Direction == "bottom":    

                self.animo = QPropertyAnimation(self._menu)
                self.animo.setTargetObject(self.item_list)
                self.animo.setPropertyName(b'geometry')
                self.animo.setStartValue(QRect(0,-120,self.widths,self.heights))
                self.animo.setEndValue(QRect(0,0,self.widths,self.heights))
                self.animo.setDuration(500)
                self.animo.setEasingCurve(QEasingCurve.Type.OutExpo)
                self.animo.start()

            else:

                if self.Direction == "top":

                    self.animo = QPropertyAnimation(self._menu)
                    self.animo.setTargetObject(self.item_list)
                    self.animo.setPropertyName(b'geometry')
                    self.animo.setStartValue(QRect(0,self.heights,self.widths,self.heights))
                    self.animo.setEndValue(QRect(0,0,self.widths,self.heights))
                    self.animo.setDuration(500)
                    self.animo.setEasingCurve(QEasingCurve.Type.OutExpo)
                    self.animo.start()

    def __initEvent__(self):
        if hasattr(self, '_menu'):
            # 动态更新菜单和item_list的尺寸，确保与按钮当前宽度同步
            w = self.widths
            h = self.heights
            self._menu.resize(w, h)
            self.item_list.setGeometry(0, 0, w, h)
            if self.Direction == "top":
                pos = self.mapToGlobal(QPoint(0, -self.heights-2))
                self._menu.move(pos)
                self._menu.show()
                self.animation()
            else:
                if self.Direction == "bottom":
                    pos = self.mapToGlobal(QPoint(0, self.height()+2))
                    self._menu.move(pos)
                    self._menu.show()
                    self.animation()

class TaskDropDownButton(TaskButton):
    def __init__(self, Content='', parent=None, border_radius=4, 
                 height: int = 100, width: int = 200,
                 border_width: int = 1, button_height: int = 25, transparent: int = 255):
        super().__init__(str(Content), parent, border_width=border_width, 
                        border_radius=border_radius, transparent=transparent)
        self.clicked.connect(self._toggle_menu)
        self.button_height = button_height
        self.border_radius = border_radius
        self.menu_width = max(100, width)
        self.menu_height = height
        self._menu = None
        self._item_list = None
        self._is_animating = False
    
    def _ensure_menu(self):
        """确保菜单只创建一次"""
        if self._menu is None:
            # 找到顶层窗口作为父控件
            parent_widget = self.window()
            self._menu = ScrollableButtonList(parent_widget)
            self._menu._scale_children = True
            self._menu.border_radius = self.border_radius
            self._menu.setFixedSize(self.menu_width, self.menu_height)

            self._menu.hide()
            
            # 安装事件过滤器，监听焦点丢失
            self._menu.installEventFilter(self)
            
            # 创建按钮列表
        
    
    def paintEvent(self, event):
        super().paintEvent(event)
        # 确保菜单在按钮上方显示
        if self._menu and self._menu.isVisible():
            self._menu.raise_()


    def eventFilter(self, obj, event):
        """事件过滤器，监听菜单焦点丢失"""
        if obj == self._menu:
            # 窗口失去激活状态（点击了菜单外的地方）
            if event.type() == QEvent.Type.WindowDeactivate:
                self._hide_menu()
                return True
            # 鼠标按下事件，检查是否点击在菜单外
            elif event.type() == QEvent.Type.MouseButtonPress:
                if not self._menu.geometry().contains(event.pos()):
                    self._hide_menu()
                    return True
        return super().eventFilter(obj, event)
    
    def _toggle_menu(self):
        if self._is_animating:
            return
        
        if self._menu and self._menu.isVisible():
            self._hide_menu()
        else:
            self._show_menu()
    
    def _show_menu(self):
        self._ensure_menu()
        
        if self._is_animating or self._menu.isVisible():
            return
        
        self._is_animating = True
        
        # 更新菜单宽度（保证不小于按钮宽度）
        self.menu_width = max(self.menu_width, self.width())
        self._menu.setFixedSize(self.menu_width, self.menu_height)
        # self._item_list.setGeometry(0, 0, self.menu_width, self.menu_height)
        
        # 计算位置：按钮居中下方
        menu_x = self.mapToGlobal(QPoint(0, self.height()))
        menu_pos = self.window().mapFromGlobal(menu_x)
        self._menu.move(menu_pos)
        
        # 保存子控件位置（用于缩放动画）
        self._menu._save_children_geometries()
        
        # 重置状态
        self._menu.set_opacity(0.0)
        self._menu.set_scale_factor(0.7)
        self._menu.show()
        
        # 播放显示动画
        def on_show_finished():
            self._is_animating = False
            # 动画完成后设置焦点，并安装全局事件过滤器
            self._menu.setFocus()
            self._install_global_filter()
            Shadow.Show(self._menu,r=8,dy=2,color=None)

        self._menu.set_opacity_animation(0.0, 1.0, 300, easing=QEasingCurve.Type.OutExpo)
        self._menu.set_scale_animation(0.7, 1.0, 350, 
                                       easing=QEasingCurve.Type.OutExpo,
                                       finished=on_show_finished)
    
    def _install_global_filter(self):
        """安装全局事件过滤器，监听应用程序级别的焦点变化"""
        # 移除旧的过滤器
        try:
            QApplication.instance().removeEventFilter(self)
        except:
            pass
        # 安装新的
        QApplication.instance().installEventFilter(self)
    
    def _remove_global_filter(self):
        """移除全局事件过滤器"""
        try:
            QApplication.instance().removeEventFilter(self)
        except:
            pass
    
    def eventFilter(self, obj, event):
        """全局事件过滤器"""
        # 如果菜单不可见，不处理
        if not self._menu or not self._menu.isVisible():
            return super().eventFilter(obj, event)
        
        # 检查是否是菜单本身的事件
        if obj == self._menu:
            # 窗口失去激活状态
            if event.type() == QEvent.Type.WindowDeactivate:
                self._hide_menu()
                return True
        
        # 检查是否是菜单的子控件
        if self._menu and obj is not self._menu:
            # 检查 obj 是否是菜单的子控件
            parent = obj
            is_child = False
            while parent:
                if parent == self._menu:
                    is_child = True
                    break
                parent = parent.parent() if hasattr(parent, 'parent') else None
            
            # 如果不是子控件，且发生了鼠标按下事件，则隐藏菜单
            if not is_child and event.type() == QEvent.Type.MouseButtonPress:
                self._hide_menu()
                return True
        
        # 检查是否是应用程序焦点变化
        if event.type() == QEvent.Type.ApplicationActivate:
            pass
        elif event.type() == QEvent.Type.ApplicationDeactivate:
            # 应用程序失去焦点时隐藏菜单
            self._hide_menu()
            return True
        
        return super().eventFilter(obj, event)
    
    def _hide_menu(self):
        if not self._menu or not self._menu.isVisible() or self._is_animating:
            return
        
        self._is_animating = True
        
        # 移除全局过滤器
        self._remove_global_filter()
        
        def on_finished():
            self._menu.hide()
            self._is_animating = False
        
        self._menu.set_opacity_animation(1.0, 0.0, 200, 
                                         easing=QEasingCurve.Type.OutExpo)
        self._menu.set_scale_animation(1.0, 0.7, 250,
                                       easing=QEasingCurve.Type.OutExpo,
                                       finished=on_finished)
    
    def addButton(self, text, onClick=None):
        self._ensure_menu()
        self._menu.addButton(str(text), onClick, button_height=self.button_height)
    
    def addTaskButton(self, text, onClick=None):
        self._ensure_menu()
        self._menu.addTaskButton(str(text), onClick, button_height=self.button_height)
    
    def clear(self):
        if self._menu:
            self._menu.clearButtons()
    
    def addSeparator(self):
        if self._menu:
            self._menu.addSeparator()
    
    def addWidget(self, widget):
        if self._menu:
            self._menu.addWidget(widget)