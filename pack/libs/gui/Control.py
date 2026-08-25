
from pack.libs.gui.widget import *
from pack.libs.gui.widget import *
from pack.libs.gui.QtPack import *
from pack.libs.gui.shadow import *
from pack.libs.gui.frame import *
from pack.libs.gui.button import *
from pack.libs.gui.TaskButton import *
from pack.libs.gui.InvertedImageButton import *
import configparser
import pathlib
import random
_config_file = pathlib.Path(__file__).resolve().parent 
def get_random_position(self):
    parent = self.parent()
    if parent:
        parent_width = parent.width()
        parent_height = parent.height()
        
        window_width = 340
        window_height = 260
        
        max_x = max(0, parent_width - window_width - 50)
        max_y = max(0, parent_height - window_height - 80)
        
        if max_x > 0 and max_y > 0:
            random_x = random.randint(20, max_x)
            random_y = random.randint(20, max_y)
        else:
            random_x = 30 + (EMdiSubWindow._window_counter * 25) % max(100, parent_width // 2)
            random_y = 30 + (EMdiSubWindow._window_counter * 15) % max(80, parent_height // 2)
        
        return random_x, random_y
    return 50, 50

def clear_layout(layout: QVBoxLayout):
    """删除布局中的所有控件"""
    while layout.count():
        item = layout.takeAt(0)  # 取出第一个项目
        widget = item.widget()   # 获取控件
        if widget:
            widget.deleteLater()  # 安全删除控件
        else:
            # 如果是子布局，递归删除
            sub_layout = item.layout()
            if sub_layout:
                clear_layout(sub_layout)
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

class TaskBar(QWidget):
    def __init__ (self,parent : QWidget,FixedHeight : int = 30):
        super().__init__(parent)

        self.setFixedHeight(FixedHeight)
        
class EImageWidget(ImageWidget):

    menuItemTriggered = pyqtSignal(str)
    
    def __init__(self, parent=None, image=""):
        super().__init__(parent, image)
        
        self._menu = None
        self._menu_actions = {}
        self._dynamic_menu_callback = None
        
        # 拖拽相关属性
        self._dragging = False
        self._drag_start_pos = None
        self._grid_size = 80  # 网格大小，对齐间距
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        

    def Set_Background_Image(self, image_path: str):
        """
        设置背景图片
        
        :param image_path: 图片文件路径
        :return: bool - 是否成功加载图片
        """
        if not image_path:
            return False
        
        # 检查文件是否存在
        if not pathlib.Path(image_path).exists():
            print(f"Warning: Image file not found: {image_path}")
            return False
        
        try:
            # 直接调用继承的 load_image 方法
            self.load_image(image_path)
            self._current_background_path = image_path
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
        
    def set_grid_size(self, size: int):
        """设置对齐网格的大小"""
        self._grid_size = max(10, size)
        self._snap_to_grid()
    
    def _snap_to_grid(self):
        """将控件对齐到最近的网格点"""
        x = round(self.x() / self._grid_size) * self._grid_size
        y = round(self.y() / self._grid_size) * self._grid_size
        # 确保不超出父窗口边界
        if self.parent():
            x = max(0, min(x, self.parent().width() - self.width()))
            y = max(0, min(y, self.parent().height() - self.height()))
        self.move(x, y)
    
    
    
    # 以下是你原有的方法，保持不变
    def set_menu(self, menu: QMenu):
        self._menu = menu
    
    def add_menu_action(self, title: str, callback=None, icon=None):
        if self._menu is None:
            self._menu = QMenu(self)
        
        if icon:
            action = self._menu.addAction(icon, title)
        else:
            action = self._menu.addAction(title)
        
        if callback:
            action.triggered.connect(callback)
        self._menu_actions[title] = callback
        return action
    
    def add_menu_separator(self):
        if self._menu is None:
            self._menu = QMenu(self)
        self._menu.addSeparator()
    
    def clear_menu(self):
        if self._menu:
            self._menu.clear()
            self._menu_actions.clear()
    
    def set_dynamic_menu_callback(self, callback):
        self._dynamic_menu_callback = callback

    def _show_menu(self, pos: QPoint):
        if self._dynamic_menu_callback:
            temp_menu = QMenu(self)
            self._dynamic_menu_callback(temp_menu)
            temp_menu.exec(self.mapToGlobal(pos))
        elif self._menu:
            self._menu.exec(self.mapToGlobal(pos))

# class AnimatedWidget(QWidget):
#     """具有缩放动画和透明度动画效果的交互控件，支持窗口化模式"""
    
#     NORMAL = 0
#     HOVER = 1
#     PRESSED = 2
#     DISABLED = 3
    
#     EDGE_NONE = 0
#     EDGE_LEFT = 1
#     EDGE_RIGHT = 2
#     EDGE_TOP = 3
#     EDGE_BOTTOM = 4
#     EDGE_TOP_LEFT = 5
#     EDGE_TOP_RIGHT = 6
#     EDGE_BOTTOM_LEFT = 7
#     EDGE_BOTTOM_RIGHT = 8
    
#     ATTR_DRAG = "Drag"
#     ATTR_ZOOM = "Zoom"
    
#     hover = Signal(bool)
#     pressed = Signal(bool)
#     unhover = Signal(bool)
#     mouseReleased = Signal(bool)
#     mousePressed = Signal(bool)
#     focusOut = Signal()
    
#     windowResized = Signal(QRect)
#     windowMoved = Signal(QPoint)
#     windowClosed = Signal()
    
#     def __init__(self, parent=None, windowed: bool = False, Attribute: tuple = ()):
#         super().__init__(parent)
        
#         self.windowed = windowed
#         self.attribute = Attribute
        
#         self._drag_enabled = self.windowed and self.ATTR_DRAG not in self.attribute
#         self._zoom_enabled = self.windowed and self.ATTR_ZOOM not in self.attribute
        
#         self._is_dragging = False
#         self._is_resizing = False
#         self._drag_position = None
#         self._resize_edge = self.EDGE_NONE
#         self._resize_start_rect = None
        
#         self.resize_margin = 8
#         self.minimum_width = 100
#         self.minimum_height = 60
        
#         self._current_state = self.NORMAL
#         self._scale_factor = 1.0
#         self._opacity = 1.0
#         self._pulse_radius = 0.0
#         self._pulse_opacity = 1.0

#         self._scale_children = True
#         self._is_animating_scale = False
#         self._saved_geometries = {}
        
#         self.border_radius = 3
#         self.animation_duration = 300
        
#         QApplication.instance().paletteChanged.connect(self.update_colors)
#         self.update_colors()
        
#         self.scale_animation = QPropertyAnimation(self, b"scale_factor")
#         self.scale_animation.setDuration(300)
#         self.scale_animation.setEasingCurve(QEasingCurve.Type.OutExpo)
#         self.scale_animation.finished.connect(self._on_scale_animation_finished)
        
#         self.opacity_animation = QPropertyAnimation(self, b"opacity")
#         self.opacity_animation.setDuration(300)
#         self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
#         if self.windowed and self._zoom_enabled:
#             self.setMouseTracking(True)
    
#     def _on_scale_animation_finished(self):
#         self._is_animating_scale = False
#         if self._scale_factor == 1.0:
#             self._restore_layout_control()
    
#     def _restore_layout_control(self):
#         for child in list(self._saved_geometries.keys()):
#             try:
#                 if child and not child.isHidden() and child.parent() == self:
#                     if hasattr(child, '_manual_geometry_set'):
#                         child.setParent(None)
#                         child.setParent(self)
#                         delattr(child, '_manual_geometry_set')
#             except (RuntimeError, AttributeError):
#                 pass
#         self._saved_geometries.clear()
#         self.updateGeometry()
#         if hasattr(self, 'main_layout') and self.main_layout:
#             self.main_layout.activate()
    
#     def add_widget(self, widget):
#         if hasattr(self, 'main_layout'):
#             self.main_layout.addWidget(widget)
    
#     def update_colors(self):
#         palette = QApplication.palette()
#         is_dark = palette.window().color().lightness() < 128

#         if is_dark:
#             self.normal_bg_color = QColor(20, 20, 20)
#             self.hover_bg_color = QColor(20, 20, 20)
#             self.pressed_bg_color = QColor(20, 20, 20)
#             self.disabled_bg_color = QColor(20, 20, 29)
#         else:
#             self.normal_bg_color = QColor(255, 255, 255)
#             self.hover_bg_color = QColor(255, 255, 255)
#             self.pressed_bg_color = QColor(255, 255, 255)
#             self.disabled_bg_color = QColor(255, 255, 255)
    
#     def focusInEvent(self, event):
#         self.raise_()
#         return super().focusInEvent(event)
    
#     def set_scale_animation(self, start: float, end: float, duration: int = 300, 
#                            finished=None, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
#         self._is_animating_scale = True
#         self.scale_animation.stop()
        
#         if start != 1.0 and end == 1.0:
#             self._save_children_geometries()
        
#         self.scale_animation.setStartValue(start)
#         self.scale_animation.setEndValue(end)
#         self.scale_animation.setDuration(duration)
#         self.scale_animation.setEasingCurve(easing)
        
#         try:
#             self.scale_animation.finished.disconnect()
#         except:
#             pass
        
#         if finished:
#             self.scale_animation.finished.connect(finished)
        
#         self.scale_animation.start()
    
#     def _save_children_geometries(self):
#         self._saved_geometries.clear()
#         for child in self.findChildren(QWidget):
#             try:
#                 if child is self or child.parent() != self:
#                     continue
#                 if not child.isHidden():
#                     self._saved_geometries[child] = child.geometry()
#             except (RuntimeError, AttributeError):
#                 continue
    
#     def set_opacity_animation(self, start: float, end: float, duration: int = 300,
#                              finished=None, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
#         self.opacity_animation.stop()
#         self.opacity_animation.setStartValue(start)
#         self.opacity_animation.setEndValue(end)
#         self.opacity_animation.setDuration(duration)
#         self.opacity_animation.setEasingCurve(easing)
#         self.opacity_animation.start()
#         if finished is not None:
#             self.opacity_animation.finished.connect(finished)

#     def get_scale_factor(self):
#         return self._scale_factor

#     def set_scale_factor(self, value):
#         old_value = self._scale_factor
#         self._scale_factor = value
#         try:
#             self._update_children_geometry()
#         except RuntimeError:
#             pass
#         self.update()
    
#     def _update_children_geometry(self):
#         if not self._scale_children or self._scale_factor == 1.0:
#             return
        
#         if not self._saved_geometries:
#             return
        
#         cx, cy = self.width() / 2, self.height() / 2
        
#         for child, orig_geom in list(self._saved_geometries.items()):
#             try:
#                 if child is None:
#                     continue
#                 if child.parent() != self:
#                     continue
#                 if child.isHidden():
#                     continue
                
#                 x = (orig_geom.x() - cx) * self._scale_factor + cx
#                 y = (orig_geom.y() - cy) * self._scale_factor + cy
#                 w = orig_geom.width() * self._scale_factor
#                 h = orig_geom.height() * self._scale_factor
                
#                 child.setGeometry(int(x), int(y), int(w), int(h))
#                 child._manual_geometry_set = True
#             except (RuntimeError, AttributeError):
#                 continue
    
#     def get_opacity(self) -> float:
#         return self._opacity
    
#     def set_opacity(self, value: float):
#         self._opacity = max(0.0, min(1.0, value))
#         self.update()

#     scale_factor = Property(float, get_scale_factor, set_scale_factor)
#     opacity = Property(float, get_opacity, set_opacity)
    
#     def setFocusOutEvent(self, handler):
#         self.focusOut.connect(handler)
    
#     def set_windowed_mode(self, windowed: bool, Attribute: tuple = None):
#         self.windowed = windowed
        
#         if Attribute is not None:
#             self.attribute = Attribute
        
#         self._drag_enabled = self.windowed and self.ATTR_DRAG not in self.attribute
#         self._zoom_enabled = self.windowed and self.ATTR_ZOOM not in self.attribute
        
#         self.setMouseTracking(self.windowed and self._zoom_enabled)
        
#         if not windowed:
#             self._is_dragging = False
#             self._is_resizing = False
#             self.setCursor(Qt.CursorShape.ArrowCursor)
    
#     def get_resize_edge(self, pos: QPoint) -> int:
#         if not self.windowed or not self._zoom_enabled:
#             return self.EDGE_NONE
        
#         rect = self.rect()
#         margin = self.resize_margin
        
#         left = pos.x() <= margin
#         right = pos.x() >= rect.width() - margin
#         top = pos.y() <= margin
#         bottom = pos.y() >= rect.height() - margin
        
#         if left and top:
#             return self.EDGE_TOP_LEFT
#         elif right and top:
#             return self.EDGE_TOP_RIGHT
#         elif left and bottom:
#             return self.EDGE_BOTTOM_LEFT
#         elif right and bottom:
#             return self.EDGE_BOTTOM_RIGHT
#         elif left:
#             return self.EDGE_LEFT
#         elif right:
#             return self.EDGE_RIGHT
#         elif top:
#             return self.EDGE_TOP
#         elif bottom:
#             return self.EDGE_BOTTOM
#         else:
#             return self.EDGE_NONE
    
#     def update_cursor(self, edge: int):
#         if not self.windowed or not self._zoom_enabled:
#             self.setCursor(Qt.CursorShape.ArrowCursor)
#             return
        
#         cursor_map = {
#             self.EDGE_LEFT: Qt.CursorShape.SizeHorCursor,
#             self.EDGE_RIGHT: Qt.CursorShape.SizeHorCursor,
#             self.EDGE_TOP: Qt.CursorShape.SizeVerCursor,
#             self.EDGE_BOTTOM: Qt.CursorShape.SizeVerCursor,
#             self.EDGE_TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
#             self.EDGE_BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
#             self.EDGE_TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
#             self.EDGE_BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
#         }
#         self.setCursor(cursor_map.get(edge, Qt.CursorShape.ArrowCursor))
    
#     def mouseMoveEvent(self, event):
#         if not self.windowed:
#             return super().mouseMoveEvent(event)
        
#         pos = event.pos()
        
#         if self._zoom_enabled and self._is_resizing and event.buttons() == Qt.MouseButton.LeftButton:
#             self.resize_widget(pos)
#         elif self._drag_enabled and self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
#             self.move_widget(event.globalPosition().toPoint())
#         elif self._zoom_enabled:
#             edge = self.get_resize_edge(pos)
#             self.update_cursor(edge)
        
#         super().mouseMoveEvent(event)
    
#     def mousePressEvent(self, event):
#         self.mousePressed.emit(True)
#         self.raise_()
        
#         if self.windowed and event.button() == Qt.MouseButton.LeftButton:
#             pos = event.pos()
#             edge = self.get_resize_edge(pos)
            
#             if self._zoom_enabled and edge != self.EDGE_NONE:
#                 self._is_resizing = True
#                 self._resize_edge = edge
#                 self._resize_start_rect = self.geometry()
#                 self._drag_position = event.globalPosition().toPoint()
#             elif self._drag_enabled:
#                 self._is_dragging = True
#                 self._drag_position = event.globalPosition().toPoint()
        
#         super().mousePressEvent(event)
    
#     def mouseReleaseEvent(self, event):
#         self.mouseReleased.emit(True)
        
#         if self.windowed:
#             self._is_dragging = False
#             self._is_resizing = False
            
#             if self._zoom_enabled:
#                 pos = event.pos()
#                 edge = self.get_resize_edge(pos)
#                 self.update_cursor(edge)
#             else:
#                 self.setCursor(Qt.CursorShape.ArrowCursor)
        
#         super().mouseReleaseEvent(event)
    
#     def move_widget(self, global_pos: QPoint):
#         if not self.windowed or not self._drag_enabled or self._drag_position is None:
#             return
        
#         delta = global_pos - self._drag_position
#         new_pos = self.pos() + delta
#         self.move(new_pos)
#         self._drag_position = global_pos
        
#         self.windowMoved.emit(self.pos())
    
#     def resize_widget(self, pos: QPoint):
#         if not self.windowed or not self._zoom_enabled or self._resize_start_rect is None or self._drag_position is None:
#             return
        
#         global_delta = self.mapToGlobal(pos) - self._drag_position
        
#         new_rect = QRect(self._resize_start_rect)
        
#         if self._resize_edge in [self.EDGE_LEFT, self.EDGE_TOP_LEFT, self.EDGE_BOTTOM_LEFT]:
#             new_width = max(self.minimum_width, self._resize_start_rect.width() - global_delta.x())
#             new_rect.setLeft(new_rect.right() - new_width)
        
#         if self._resize_edge in [self.EDGE_RIGHT, self.EDGE_TOP_RIGHT, self.EDGE_BOTTOM_RIGHT]:
#             new_width = max(self.minimum_width, self._resize_start_rect.width() + global_delta.x())
#             new_rect.setWidth(new_width)
        
#         if self._resize_edge in [self.EDGE_TOP, self.EDGE_TOP_LEFT, self.EDGE_TOP_RIGHT]:
#             new_height = max(self.minimum_height, self._resize_start_rect.height() - global_delta.y())
#             new_rect.setTop(new_rect.bottom() - new_height)
        
#         if self._resize_edge in [self.EDGE_BOTTOM, self.EDGE_BOTTOM_LEFT, self.EDGE_BOTTOM_RIGHT]:
#             new_height = max(self.minimum_height, self._resize_start_rect.height() + global_delta.y())
#             new_rect.setHeight(new_height)
        
#         self.setGeometry(new_rect)
#         self.windowResized.emit(new_rect)
    
#     def enterEvent(self, event):
#         self._current_state = self.HOVER
#         self.hover.emit(True)
#         super().enterEvent(event)
    
#     def leaveEvent(self, event):
#         self._current_state = self.NORMAL
#         self.unhover.emit(True)
#         if self.windowed:
#             self.setCursor(Qt.CursorShape.ArrowCursor)
#         super().leaveEvent(event)
    
#     def paintEvent(self, event):
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
#         width = self.width()
#         height = self.height()
#         center = QPoint(width // 2, height // 2)
        
#         if not self.isEnabled():
#             bg_color = self.disabled_bg_color
#         elif self._current_state == self.PRESSED:
#             bg_color = self.pressed_bg_color
#         elif self._current_state == self.HOVER:
#             bg_color = self.hover_bg_color
#         else:
#             bg_color = self.normal_bg_color
        
#         gradient = QLinearGradient(0, 0, 0, height)
#         gradient.setColorAt(0, bg_color.lighter(110))
#         gradient.setColorAt(1, bg_color)
        
#         painter.save()
        
#         transform = QTransform()
#         transform.translate(center.x(), center.y())
#         transform.scale(self._scale_factor, self._scale_factor)
#         transform.translate(-center.x(), -center.y())
#         painter.setTransform(transform)
        
#         rect = self.rect()
#         path = QPainterPath()
#         path.addRoundedRect(rect, self.border_radius, self.border_radius)
        
#         painter.setOpacity(self._opacity)
#         painter.fillPath(path, gradient)
        
#         border_color = bg_color.darker(120)
#         painter.setPen(QPen(border_color, 1))
#         painter.drawPath(path)
        
#         painter.restore()
        
#         if self.windowed and self._zoom_enabled and self.hasFocus():
#             painter.save()
#             painter.setOpacity(self._opacity)
#             painter.setPen(QPen(QColor(100, 100, 255, 100), 1))
#             painter.setBrush(Qt.BrushStyle.NoBrush)
#             margin = self.resize_margin
#             rect = self.rect().adjusted(margin, margin, -margin, -margin)
#             painter.drawRect(rect)
#             painter.restore()
    
#     def resizeEvent(self, event):
#         super().resizeEvent(event)
#         if self._is_animating_scale and self._scale_factor != 1.0:
#             try:
#                 self._update_children_geometry()
#             except RuntimeError:
#                 pass
class AnimatedWidget(QWidget):
    """具有缩放动画和透明度动画效果的交互控件，支持窗口化模式"""
    
    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    DISABLED = 3
    
    EDGE_NONE = 0
    EDGE_LEFT = 1
    EDGE_RIGHT = 2
    EDGE_TOP = 3
    EDGE_BOTTOM = 4
    EDGE_TOP_LEFT = 5
    EDGE_TOP_RIGHT = 6
    EDGE_BOTTOM_LEFT = 7
    EDGE_BOTTOM_RIGHT = 8
    
    ATTR_DRAG = "Drag"
    ATTR_ZOOM = "Zoom"
    
    hover = pyqtSignal(bool)
    pressed = pyqtSignal(bool)
    unhover = pyqtSignal(bool)
    mouseReleased = pyqtSignal(bool)
    mousePressed = pyqtSignal(bool)
    focusOut = pyqtSignal()
    
    windowResized = pyqtSignal(QRect)
    windowMoved = pyqtSignal(QPoint)
    windowClosed = pyqtSignal()
    
    def __init__(self, parent=None, windowed: bool = False, Attribute: tuple = ()):
        super().__init__(parent)
        
        self.windowed = windowed
        self.attribute = Attribute
        
        self._drag_enabled = self.windowed and self.ATTR_DRAG not in self.attribute
        self._zoom_enabled = self.windowed and self.ATTR_ZOOM not in self.attribute
        
        self._is_dragging = False
        self._is_resizing = False
        self._drag_position = None
        self._resize_edge = self.EDGE_NONE
        self._resize_start_rect = None
        
        self.resize_margin = 8
        self.minimum_width = 100
        self.minimum_height = 60
        
        self._current_state = self.NORMAL
        self._scale_factor = 1.0
        self._opacity = 1.0
        self._pulse_radius = 0.0
        self._pulse_opacity = 1.0

        self._scale_children = True
        self._is_animating_scale = False
        self._saved_geometries = {}
        self._child_opacity_effects = {}
        
        self.border_radius = 3
        self.animation_duration = 300
        
        QApplication.instance().paletteChanged.connect(self.update_colors)
        self.update_colors()
        
        self.scale_animation = QPropertyAnimation(self, b"scale_factor")
        self.scale_animation.setDuration(300)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutExpo)
        self.scale_animation.finished.connect(self._on_scale_animation_finished)
        
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if self.windowed and self._zoom_enabled:
            self.setMouseTracking(True)
    
    def _on_scale_animation_finished(self):
        self._is_animating_scale = False
        if self._scale_factor == 1.0:
            self._restore_layout_control()
    
    def _restore_layout_control(self):
        for child in list(self._saved_geometries.keys()):
            try:
                if child and not child.isHidden() and child.parent() == self:
                    if hasattr(child, '_manual_geometry_set'):
                        child.setParent(None)
                        child.setParent(self)
                        delattr(child, '_manual_geometry_set')
            except (RuntimeError, AttributeError):
                pass
        self._saved_geometries.clear()
        self.updateGeometry()
        if hasattr(self, 'main_layout') and self.main_layout:
            self.main_layout.activate()
    
    def add_widget(self, widget):
        if hasattr(self, 'main_layout'):
            self.main_layout.addWidget(widget)
    
    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128

        if is_dark:
            self.normal_bg_color = QColor(30, 30, 30)
            self.hover_bg_color = QColor(30, 30, 30)
            self.pressed_bg_color = QColor(30, 30, 30)
            self.disabled_bg_color = QColor(30, 30, 30)
        else:
            self.normal_bg_color = QColor(255, 255, 255)
            self.hover_bg_color = QColor(255, 255, 255)
            self.pressed_bg_color = QColor(255, 255, 255)
            self.disabled_bg_color = QColor(255, 255, 255)
    
    def focusInEvent(self, event):
        self.raise_()
        return super().focusInEvent(event)
    
    def set_scale_animation(self, start: float, end: float, duration: int = 300, 
                           finished=None, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
        self._is_animating_scale = True
        self.scale_animation.stop()
        
        if start != 1.0 and end == 1.0:
            self._save_children_geometries()
        
        self.scale_animation.setStartValue(start)
        self.scale_animation.setEndValue(end)
        self.scale_animation.setDuration(duration)
        self.scale_animation.setEasingCurve(easing)
        
        try:
            self.scale_animation.finished.disconnect()
        except:
            pass
        
        if finished:
            self.scale_animation.finished.connect(finished)
        
        self.scale_animation.start()
    
    def _save_children_geometries(self):
        self._saved_geometries.clear()
        for child in self.findChildren(QWidget):
            try:
                if child is self or child.parent() != self:
                    continue
                if not child.isHidden():
                    self._saved_geometries[child] = child.geometry()
            except (RuntimeError, AttributeError):
                continue
    
    def set_opacity_animation(self, start: float, end: float, duration: int = 300,
                             finished=None, easing: QEasingCurve.Type = QEasingCurve.Type.OutExpo):
        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(start)
        self.opacity_animation.setEndValue(end)
        self.opacity_animation.setDuration(duration)
        self.opacity_animation.setEasingCurve(easing)
        try:
            self.opacity_animation.finished.disconnect()
        except TypeError:
            pass
        if finished is not None:
            self.opacity_animation.finished.connect(finished)
        self.opacity_animation.start()

    def get_scale_factor(self):
        return self._scale_factor

    def set_scale_factor(self, value):
        old_value = self._scale_factor
        self._scale_factor = value
        try:
            self._update_children_geometry()
        except RuntimeError:
            pass
        self.update()
    
    def _update_children_geometry(self):
        if not self._scale_children or self._scale_factor == 1.0:
            return
        
        if not self._saved_geometries:
            return
        
        cx, cy = self.width() / 2, self.height() / 2
        
        for child, orig_geom in list(self._saved_geometries.items()):
            try:
                if child is None:
                    continue
                if child.parent() != self:
                    continue
                if child.isHidden():
                    continue
                
                x = (orig_geom.x() - cx) * self._scale_factor + cx
                y = (orig_geom.y() - cy) * self._scale_factor + cy
                w = orig_geom.width() * self._scale_factor
                h = orig_geom.height() * self._scale_factor
                
                child.setGeometry(int(x), int(y), int(w), int(h))
                child._manual_geometry_set = True
            except (RuntimeError, AttributeError):
                continue
    
    def get_opacity(self) -> float:
        return self._opacity
    
    def set_opacity(self, value: float):
        self._opacity = max(0.0, min(1.0, value))
        self._update_children_opacity()
        self.update()
    
    def _update_children_opacity(self):
        """更新所有子控件的透明度"""
        for child in self.findChildren(QWidget):
            try:
                if child is self or child.parent() != self:
                    continue
                if child.isHidden():
                    continue
                
                if self._opacity >= 0.99:
                    if child in self._child_opacity_effects:
                        effect = self._child_opacity_effects.pop(child)
                        if effect:
                            effect.deleteLater()
                    child.setGraphicsEffect(None)
                else:
                    if child not in self._child_opacity_effects:
                        effect = QGraphicsOpacityEffect(child)
                        effect.setOpacity(self._opacity)
                        child.setGraphicsEffect(effect)
                        self._child_opacity_effects[child] = effect
                    else:
                        effect = self._child_opacity_effects[child]
                        if effect:
                            effect.setOpacity(self._opacity)
                    
            except (RuntimeError, AttributeError):
                continue
    
    def childEvent(self, event):
        """监听子控件添加事件，自动添加透明度效果"""
        if event.type() == QEvent.ChildAdded:
            child = event.child()
            if isinstance(child, QWidget) and child != self:
                if self._opacity < 0.99:
                    effect = QGraphicsOpacityEffect(child)
                    effect.setOpacity(self._opacity)
                    child.setGraphicsEffect(effect)
                    self._child_opacity_effects[child] = effect
        super().childEvent(event)

    scale_factor = pyqtProperty(float, get_scale_factor, set_scale_factor)
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def setFocusOutEvent(self, handler):
        self.focusOut.connect(handler)
    
    def set_windowed_mode(self, windowed: bool, Attribute: tuple = None):
        self.windowed = windowed
        
        if Attribute is not None:
            self.attribute = Attribute
        
        self._drag_enabled = self.windowed and self.ATTR_DRAG not in self.attribute
        self._zoom_enabled = self.windowed and self.ATTR_ZOOM not in self.attribute
        
        self.setMouseTracking(self.windowed and self._zoom_enabled)
        
        if not windowed:
            self._is_dragging = False
            self._is_resizing = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def get_resize_edge(self, pos: QPoint) -> int:
        if not self.windowed or not self._zoom_enabled:
            return self.EDGE_NONE
        
        rect = self.rect()
        margin = self.resize_margin
        
        left = pos.x() <= margin
        right = pos.x() >= rect.width() - margin
        top = pos.y() <= margin
        bottom = pos.y() >= rect.height() - margin
        
        if left and top:
            return self.EDGE_TOP_LEFT
        elif right and top:
            return self.EDGE_TOP_RIGHT
        elif left and bottom:
            return self.EDGE_BOTTOM_LEFT
        elif right and bottom:
            return self.EDGE_BOTTOM_RIGHT
        elif left:
            return self.EDGE_LEFT
        elif right:
            return self.EDGE_RIGHT
        elif top:
            return self.EDGE_TOP
        elif bottom:
            return self.EDGE_BOTTOM
        else:
            return self.EDGE_NONE
    
    def update_cursor(self, edge: int):
        if not self.windowed or not self._zoom_enabled:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        
        cursor_map = {
            self.EDGE_LEFT: Qt.CursorShape.SizeHorCursor,
            self.EDGE_RIGHT: Qt.CursorShape.SizeHorCursor,
            self.EDGE_TOP: Qt.CursorShape.SizeVerCursor,
            self.EDGE_BOTTOM: Qt.CursorShape.SizeVerCursor,
            self.EDGE_TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
            self.EDGE_BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
            self.EDGE_TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
            self.EDGE_BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
        }
        self.setCursor(cursor_map.get(edge, Qt.CursorShape.ArrowCursor))
    
    def mouseMoveEvent(self, event):
        if not self.windowed:
            return super().mouseMoveEvent(event)
        
        pos = event.pos()
        
        if self._zoom_enabled and self._is_resizing and event.buttons() == Qt.MouseButton.LeftButton:
            self.resize_widget(pos)
        elif self._drag_enabled and self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move_widget(event.globalPos())
        elif self._zoom_enabled:
            edge = self.get_resize_edge(pos)
            self.update_cursor(edge)
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        self.mousePressed.emit(True)
        self.raise_()
        
        if self.windowed and event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            edge = self.get_resize_edge(pos)
            
            if self._zoom_enabled and edge != self.EDGE_NONE:
                self._is_resizing = True
                self._resize_edge = edge
                self._resize_start_rect = self.geometry()
                self._drag_position = event.globalPos()
            elif self._drag_enabled:
                self._is_dragging = True
                self._drag_position = event.globalPos()
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.mouseReleased.emit(True)
        
        if self.windowed:
            self._is_dragging = False
            self._is_resizing = False
            
            if self._zoom_enabled:
                pos = event.pos()
                edge = self.get_resize_edge(pos)
                self.update_cursor(edge)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        
        super().mouseReleaseEvent(event)
    
    def move_widget(self, global_pos: QPoint):
        if not self.windowed or not self._drag_enabled or self._drag_position is None:
            return
        
        delta = global_pos - self._drag_position
        new_pos = self.pos() + delta
        self.move(new_pos)
        self._drag_position = global_pos
        
        self.windowMoved.emit(self.pos())
    
    def resize_widget(self, pos: QPoint):
        if not self.windowed or not self._zoom_enabled or self._resize_start_rect is None or self._drag_position is None:
            return
        
        global_delta = self.mapToGlobal(pos) - self._drag_position
        
        new_rect = QRect(self._resize_start_rect)
        
        if self._resize_edge in [self.EDGE_LEFT, self.EDGE_TOP_LEFT, self.EDGE_BOTTOM_LEFT]:
            new_width = max(self.minimum_width, self._resize_start_rect.width() - global_delta.x())
            new_rect.setLeft(new_rect.right() - new_width)
        
        if self._resize_edge in [self.EDGE_RIGHT, self.EDGE_TOP_RIGHT, self.EDGE_BOTTOM_RIGHT]:
            new_width = max(self.minimum_width, self._resize_start_rect.width() + global_delta.x())
            new_rect.setWidth(new_width)
        
        if self._resize_edge in [self.EDGE_TOP, self.EDGE_TOP_LEFT, self.EDGE_TOP_RIGHT]:
            new_height = max(self.minimum_height, self._resize_start_rect.height() - global_delta.y())
            new_rect.setTop(new_rect.bottom() - new_height)
        
        if self._resize_edge in [self.EDGE_BOTTOM, self.EDGE_BOTTOM_LEFT, self.EDGE_BOTTOM_RIGHT]:
            new_height = max(self.minimum_height, self._resize_start_rect.height() + global_delta.y())
            new_rect.setHeight(new_height)
        
        self.setGeometry(new_rect)
        self.windowResized.emit(new_rect)
    
    def enterEvent(self, event):
        self._current_state = self.HOVER
        self.hover.emit(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._current_state = self.NORMAL
        self.unhover.emit(True)
        if self.windowed:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center = QPoint(width // 2, height // 2)
        
        if not self.isEnabled():
            bg_color = self.disabled_bg_color
        elif self._current_state == self.PRESSED:
            bg_color = self.pressed_bg_color
        elif self._current_state == self.HOVER:
            bg_color = self.hover_bg_color
        else:
            bg_color = self.normal_bg_color
        
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, bg_color.lighter(110))
        gradient.setColorAt(1, bg_color)
        
        painter.save()
        
        transform = QTransform()
        transform.translate(center.x(), center.y())
        transform.scale(self._scale_factor, self._scale_factor)
        transform.translate(-center.x(), -center.y())
        painter.setTransform(transform)
        
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, self.border_radius, self.border_radius)
        
        painter.setOpacity(self._opacity)
        painter.fillPath(path, gradient)
        
        border_color = bg_color.darker(120)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)
        
        painter.restore()
        
        if self.windowed and self._zoom_enabled and self.hasFocus():
            painter.save()
            painter.setOpacity(self._opacity)
            painter.setPen(QPen(QColor(100, 100, 255, 100), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            margin = self.resize_margin
            rect = self.rect().adjusted(margin, margin, -margin, -margin)
            painter.drawRect(rect)
            painter.restore()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_animating_scale and self._scale_factor != 1.0:
            try:
                self._update_children_geometry()
            except RuntimeError:
                pass

# class EMdiSubWindow(AnimatedWidget):
    
#     closeAnimationFinished = Signal()
    
#     def __init__(self, parent: QWidget = None, title: str = "Python"):
#         super().__init__(parent, windowed=False)
#         self.setWindowTitle(title)
#         self.setMinimumSize(140, 50)
#         self.resize(340, 260)
#         self.title = title
#         self.border_radius = 5
        
#         self.set_opacity(0.0)
#         self.set_scale_factor(0.8)
        
#         self._is_animating_in = False
#         self._is_closing = False
#         self._close_callback = None
#         self._drag_position = None
#         self._is_dragging = False
        
#         self.Shadow = Shadow.Show(self,dy=3,r=25,color=QColor("#000000"))

#         QTimer.singleShot(10, self.play_show_animation)
    
#     def _init_gui(self):
#         self.main_layout = QVBoxLayout(self)
#         self.main_layout.setContentsMargins(0,0,0,0)
#         self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
#         self.main_layout.setSpacing(0)
        
#         self.main_Frame = QWidget()
#         self.main_Frame.setSizePolicy(
#             QSizePolicy.Policy.Expanding, 
#             QSizePolicy.Policy.Expanding
#         )
#         self.main_layout.addWidget(self.main_Frame)

        

#         self.main_frame_layout = QHBoxLayout(self.main_Frame)
#         self.main_frame_layout.setContentsMargins(0,5,0,0)
#         self.main_frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
#         self.main_frame_layout.setSpacing(0)
        
#         self.TitleBar = QWidget()
#         self.TitleBar.setFixedHeight(25)
#         self.titlebar_layout = QHBoxLayout(self.TitleBar)
#         self.titlebar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
#         self.titlebar_layout.setContentsMargins(10,0,10,0)

#         TITLE = QLabel(str(self.title))
#         TITLE.setFont(QFont(QApplication.font().family(),10))

#         icon_widget = EImageWidget(image=r"C:\Users\wuyue\Desktop\Embark\Theme\logo.png")
#         icon_widget.setFixedSize(20,20)
#         self.titlebar_layout.addWidget(icon_widget)
#         self.titlebar_layout.addWidget(TITLE)
#         self.titlebar_layout.addStretch()

#         closeButton = Button("x",None,border_radius=5,border_width=0)
#         closeButton.setFixedSize(20,20)
#         closeButton.clicked.connect(self.close_with_callback)
#         self.titlebar_layout.addWidget(closeButton)

#         self.main_frame_layout.addWidget(self.TitleBar)
        
#         self.TitleBar.mousePressEvent = self._titlebar_mouse_press
#         self.TitleBar.mouseMoveEvent = self._titlebar_mouse_move
#         self.TitleBar.mouseReleaseEvent = self._titlebar_mouse_release
#         self.TitleBar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
#         self.TitleBar.customContextMenuRequested.connect(self._show_titlebar_menu)
    
#     def _titlebar_mouse_press(self, event):
#         if event.button() == Qt.MouseButton.LeftButton:
#             self._is_dragging = True
#             self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
#             event.accept()
    
#     def _titlebar_mouse_move(self, event):
#         if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
#             new_pos = event.globalPosition().toPoint() - self._drag_position
#             self.move(new_pos)
#             event.accept()
    
#     def _titlebar_mouse_release(self, event):
#         if event.button() == Qt.MouseButton.LeftButton:
#             self._is_dragging = False
#             event.accept()
    
#     def _show_titlebar_menu(self, position):
#         menu = QMenu(self.TitleBar)
        
#         minimize_action = menu.addAction("最小化")
#         maximize_action = menu.addAction("最大化")
#         restore_action = menu.addAction("还原")
#         menu.addSeparator()
#         close_action = menu.addAction("关闭")
        
#         if self.isMaximized():
#             maximize_action.setEnabled(False)
#             restore_action.setEnabled(True)
#         else:
#             maximize_action.setEnabled(True)
#             restore_action.setEnabled(False)
        
#         minimize_action.triggered.connect(self.showMinimized)
#         maximize_action.triggered.connect(self.showMaximized)
#         restore_action.triggered.connect(self.showNormal)
#         close_action.triggered.connect(self.close_with_callback)
        
#         menu.exec(self.TitleBar.mapToGlobal(position))
    
#     def play_show_animation(self):
#         if self._is_animating_in:
#             return
        
#         self._is_animating_in = True
#         self.set_opacity_animation(0.0, 1.0, 400, 
#                                    easing=QEasingCurve.Type.OutCubic)

#         self.set_scale_animation(0.9, 1.0, 400,
#                                  easing=QEasingCurve.Type.OutExpo,
#                                  finished=self._on_show_animation_finished)
    
#     def _on_show_animation_finished(self):
#         self._is_animating_in = False
#         self._init_gui()

    
#     def play_close_animation(self, callback=None):
#         if self._is_closing:
#             return
        
#         self._is_closing = True
#         self._close_callback = callback

#         self.set_opacity_animation(1.0, 0.0, 300,
#                                    easing=QEasingCurve.Type.InCubic)

#         self.set_scale_animation(1.0, 0.8, 300,
#                                  easing=QEasingCurve.Type.InCubic,
#                                  finished=self._on_close_animation_finished)

#     def _on_close_animation_finished(self):
#         self.closeAnimationFinished.emit()

#         if self._close_callback is not None:
#             self._close_callback = None
        
#         self.close()
    
#     def closeEvent(self, event):
#         if self._is_closing:
#             event.accept()
#             return
        
#         event.ignore()
#         self.play_close_animation()
    
#     def close_with_callback(self, callback=None):
#         if hasattr(self, 'main_layout'):
#             self.main_layout.deleteLater()
#             clear_layout(self.main_layout)
#         self.play_close_animation(callback)
        
#     def enterEvent(self, event):
#         self.raise_()
#         super().enterEvent(event)
class TaskBarWindowManager(QObject):
    """任务栏窗口管理器"""
    
    windowRegistered = pyqtSignal(object)
    windowUnregistered = pyqtSignal(object)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 注意：必须先调用 super().__init__() 构造 C++ 基类，
        # 否则在 PyQt5 下访问 self 任意属性都会触发
        # "RuntimeError: super-class __init__() ... was never called"。
        super().__init__()
        # 单例守卫：__new__ 保证只创建一个实例，但 __init__ 会被多次调用，
        # 若重复执行会把 _taskbar_widget 重置为 None，导致窗口无法注册。
        if getattr(self, '_initialized', False):
            return
        self._initialized = True
        self._taskbar_windows = {}
        self._taskbar_widget = None
    
    def set_taskbar_widget(self, taskbar_widget):
        """设置任务栏控件"""
        self._taskbar_widget = taskbar_widget
    
    def register_window(self, window, icon_path, title):
        """向任务栏注册窗口"""
        if not self._taskbar_widget:
            return None
        
        window_id = id(window)
        
        if window_id in self._taskbar_windows:
            return self._taskbar_windows[window_id]
        
        button = TaskButtonWithIcon(title, icon_path, None, border_radius=3, border_width=0)
        button.setFixedHeight(28)
        button.setFixedWidth(120)
        button._target_window = window
        
        def on_button_click():
            if window.isMinimized():
                window.showNormal()
            window.raise_()
            window.activateWindow()
            window.setWindowState(window.windowState() & ~Qt.WindowState.WindowMinimized)
        
        button.clicked.connect(on_button_click)
        
        def on_window_focus():
            for btn in self._taskbar_windows.values():
                btn.set_focus_state(False)
            button.set_focus_state(True)
        
        original_focus_in = window.focusInEvent
        def new_focus_in(event):
            on_window_focus()
            if original_focus_in:
                original_focus_in(event)
        window.focusInEvent = new_focus_in
        
        def on_window_closed():
            self.unregister_window(window)
        
        window.destroyed.connect(on_window_closed)
        
        self._taskbar_widget._layout.addWidget(button)
        self._taskbar_windows[window_id] = button
        
        button.animate_fade_in()
        
        self.windowRegistered.emit(window)
        
        return button
    
    def unregister_window(self, window):
        """从任务栏注销窗口 - 带动画归位效果"""
        window_id = id(window)
        
        if window_id not in self._taskbar_windows:
            return
        
        button = self._taskbar_windows.pop(window_id)
        if not button:
            return
        
        layout = self._taskbar_widget._layout
        button_index = -1
        for i in range(layout.count()):
            if layout.itemAt(i).widget() == button:
                button_index = i
                break
        
        if button_index == -1:
            button.deleteLater()
            self.windowUnregistered.emit(window)
            return
        
        button.animate_width_to_zero()
        button.animate_fade_out(lambda: button.deleteLater())
        
        self.windowUnregistered.emit(window)
    
    def update_window_title(self, window, title):
        """更新任务栏按钮标题"""
        window_id = id(window)
        if window_id in self._taskbar_windows:
            self._taskbar_windows[window_id].setText(title)
    
    def update_window_icon(self, window, icon_path):
        """更新任务栏按钮图标"""
        window_id = id(window)
        if window_id in self._taskbar_windows:
            self._taskbar_windows[window_id].load_image(icon_path, 20)
    
    def set_focus_to_window(self, window):
        """设置窗口焦点并高亮对应按钮"""
        window_id = id(window)
        for wid, btn in self._taskbar_windows.items():
            btn.set_focus_state(wid == window_id)


class _WindowWorker(QObject):
    """每个 EMdiSubWindow 专属的后台工作对象，运行在独立线程的事件循环中。

    窗口的耗时 / 阻塞任务（如 IO、子进程、计算）通过 post_task 投递到这里执行，
    避免堆积在主线程导致 UI 卡顿。窗口本身仍在主线程渲染。
    """
    task = pyqtSignal(object, tuple, dict)  # (callable, args, kwargs)

    def __init__(self):
        super().__init__()
        self.task.connect(self._run)

    @pyqtSlot(object, tuple, dict)
    def _run(self, func, args, kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print("Window worker task error:", e)


class EMdiSubWindow(AnimatedWidget):
    
    closeAnimationFinished = pyqtSignal()
    _window_counter = 0
    
    def __init__(self, parent: QWidget = None, title: str = "Python", 
                 allow_resize: bool = True, allow_maxmin_buttons: bool = True, icon_path: str = None):
        super().__init__(parent, windowed=False)
        self.setWindowTitle(title)
        
        EMdiSubWindow._window_counter += 1
        if icon_path is None:
            self.icon_path = _config_file / "Theme/logo.png"
        else:
            self.icon_path = icon_path
        
        self.title = title
        self.border_radius = 5
        self.allow_resize = allow_resize
        self.allow_maxmin_buttons = allow_maxmin_buttons
        
        self._is_animating_in = False
        self._is_closing = False
        self._is_maximizing = False
        self._close_callback = None
        self._drag_position = None
        self._is_dragging = False
        self._normal_geometry = None
        self._taskbar_registered = False
        
        # ---- 边缘缩放状态 ----
        self._is_resizing = False
        self._resize_edge = self.EDGE_NONE
        self._resize_start_rect = None
        self._resize_drag_pos = None
        self.resize_margin = 8
        self.minimum_width = 200
        self.minimum_height = 150
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.installEventFilter(self)
        
        self.set_opacity(0.0)
        self.set_scale_factor(0.8)
        
        self._taskbar_manager = TaskBarWindowManager()
        
        x, y = self.get_random_position()
        self.setGeometry(x, y, 340, 260)
        
        self._init_gui()

        # 为窗口分配独立工作线程（窗口 UI 仍在主线程，后台任务走独立线程）
        self._worker_thread = QThread()
        self._worker_thread.setObjectName(f"WinThread-{title}-{EMdiSubWindow._window_counter}")
        self._worker = _WindowWorker()
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.start()

        QTimer.singleShot(50, self._register_and_show)
    
    def _register_and_show(self):
        """向任务栏注册后显示窗口"""
        if self._taskbar_manager._taskbar_widget:
            self._taskbar_manager.register_window(self, self.icon_path, self.title)
            self._taskbar_registered = True
        
        self.play_show_animation()
    
    def _init_gui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSpacing(0)
        
        self.main_Frame = QWidget()
        self.main_Frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        self.main_layout.addWidget(self.main_Frame)
        self.main_frame_layout = QVBoxLayout(self.main_Frame)
        self.main_frame_layout.setContentsMargins(0, 5, 0, 0)
        self.main_frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_frame_layout.setSpacing(0)
        
        self.TitleBar = QWidget()
        self.TitleBar.setFixedHeight(25)
        self.titlebar_layout = QHBoxLayout(self.TitleBar)
        self.titlebar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.titlebar_layout.setContentsMargins(10, 0, 10, 0)
        
        self.title_label = QLabel(str(self.title))
        self.title_label.setFont(QFont(QApplication.font().family(), 10))
        
        icon_widget = EImageWidget(image=self.icon_path)
        icon_widget.setFixedSize(20, 20)
        self.titlebar_layout.addWidget(icon_widget)
        self.titlebar_layout.addWidget(self.title_label)
        self.titlebar_layout.addStretch()
        
        if self.allow_maxmin_buttons:
            self.minimizeButton = Button("_", None, border_radius=3, border_width=0)
            self.minimizeButton.setFixedSize(25, 25)
            self.minimizeButton.clicked.connect(self.animate_minimize)
            self.titlebar_layout.addWidget(self.minimizeButton)
            
            if self.allow_resize:
                self.maximizeButton = Button("o", None, border_radius=3, border_width=0)
                self.maximizeButton.setFixedSize(25, 25)
                self.maximizeButton.clicked.connect(self.animate_maximize_restore)
                self.titlebar_layout.addWidget(self.maximizeButton)
        
        closeButton = Button("x", None, border_radius=3, border_width=0,font_size=11)
        closeButton.setFixedSize(25, 25)

        closeButton.clicked.connect(self.close_with_callback)
        self.titlebar_layout.addWidget(closeButton)
        
        self.main_frame_layout.addWidget(self.TitleBar)
        
        self.TitleBar.mousePressEvent = self._titlebar_mouse_press
        self.TitleBar.mouseMoveEvent = self._titlebar_mouse_move
        self.TitleBar.mouseReleaseEvent = self._titlebar_mouse_release
        self.TitleBar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.TitleBar.customContextMenuRequested.connect(self._show_titlebar_menu)
        
        if self.allow_resize:
            self.setMouseTracking(True)
        else:
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    def set_title(self, new_title: str):
        """更新窗口标题（标题栏 + 窗口标题 + 任务栏按钮）。"""
        self.title = new_title
        self.setWindowTitle(new_title)
        if hasattr(self, 'title_label') and self.title_label is not None:
            self.title_label.setText(new_title)
        if self._taskbar_registered and hasattr(self, '_taskbar_manager'):
            self._taskbar_manager.update_window_title(self, new_title)
    
    def set_taskbar_manager(self, taskbar_widget):
        """设置任务栏管理器"""
        self._taskbar_manager.set_taskbar_widget(taskbar_widget)
        if not self._taskbar_registered and not self._is_animating_in:
            self._taskbar_manager.register_window(self, self.icon_path, self.title)
            self._taskbar_registered = True
    
    # ---- 边缘缩放 ----

    def _get_edge_at_pos(self, pos: QPoint) -> int:
        """检测鼠标位置所在的缩放边缘"""
        if not self.allow_resize or self.isMaximized():
            return self.EDGE_NONE
        rect = self.rect()
        m = self.resize_margin
        left = pos.x() <= m
        right = pos.x() >= rect.width() - m
        top = pos.y() <= m
        bottom = pos.y() >= rect.height() - m
        if left and top:
            return self.EDGE_TOP_LEFT
        if right and top:
            return self.EDGE_TOP_RIGHT
        if left and bottom:
            return self.EDGE_BOTTOM_LEFT
        if right and bottom:
            return self.EDGE_BOTTOM_RIGHT
        if left:
            return self.EDGE_LEFT
        if right:
            return self.EDGE_RIGHT
        if top:
            return self.EDGE_TOP
        if bottom:
            return self.EDGE_BOTTOM
        return self.EDGE_NONE

    _EDGE_CURSOR_MAP = {
        AnimatedWidget.EDGE_LEFT: Qt.CursorShape.SizeHorCursor,
        AnimatedWidget.EDGE_RIGHT: Qt.CursorShape.SizeHorCursor,
        AnimatedWidget.EDGE_TOP: Qt.CursorShape.SizeVerCursor,
        AnimatedWidget.EDGE_BOTTOM: Qt.CursorShape.SizeVerCursor,
        AnimatedWidget.EDGE_TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
        AnimatedWidget.EDGE_BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
        AnimatedWidget.EDGE_TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
        AnimatedWidget.EDGE_BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
    }

    def _do_resize(self, global_pos: QPoint):
        """执行缩放"""
        if not self._is_resizing or self._resize_start_rect is None or self._resize_drag_pos is None:
            return
        delta = global_pos - self._resize_drag_pos
        new_rect = QRect(self._resize_start_rect)
        e = self._resize_edge
        if e in (self.EDGE_LEFT, self.EDGE_TOP_LEFT, self.EDGE_BOTTOM_LEFT):
            nw = max(self.minimum_width, self._resize_start_rect.width() - delta.x())
            new_rect.setLeft(new_rect.right() - nw)
        if e in (self.EDGE_RIGHT, self.EDGE_TOP_RIGHT, self.EDGE_BOTTOM_RIGHT):
            nw = max(self.minimum_width, self._resize_start_rect.width() + delta.x())
            new_rect.setWidth(nw)
        if e in (self.EDGE_TOP, self.EDGE_TOP_LEFT, self.EDGE_TOP_RIGHT):
            nh = max(self.minimum_height, self._resize_start_rect.height() - delta.y())
            new_rect.setTop(new_rect.bottom() - nh)
        if e in (self.EDGE_BOTTOM, self.EDGE_BOTTOM_LEFT, self.EDGE_BOTTOM_RIGHT):
            nh = max(self.minimum_height, self._resize_start_rect.height() + delta.y())
            new_rect.setHeight(nh)
        self.setGeometry(new_rect)

    def mousePressEvent(self, event):
        if self.allow_resize and event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_edge_at_pos(event.pos())
            if edge != self.EDGE_NONE:
                self._is_resizing = True
                self._resize_edge = edge
                self._resize_start_rect = self.geometry()
                self._resize_drag_pos = event.globalPos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.allow_resize:
            if self._is_resizing and event.buttons() == Qt.MouseButton.LeftButton:
                self._do_resize(event.globalPos())
                event.accept()
                return
            if not event.buttons():
                edge = self._get_edge_at_pos(event.pos())
                self.setCursor(self._EDGE_CURSOR_MAP.get(edge, Qt.CursorShape.ArrowCursor))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_resizing:
            self._is_resizing = False
            self._resize_edge = self.EDGE_NONE
            self._resize_start_rect = None
            self._resize_drag_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.isAncestorOf(obj) or obj is self:
                self.raise_()
                self.activateWindow()
        return super().eventFilter(obj, event)
    
    def addWidget(self, widget):
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_frame_layout.addWidget(widget, 1)
    
    def animate_maximize_restore(self):
        if self._is_maximizing:
            return
        
        if self.isMaximized():
            self.animate_restore()
        else:
            self.animate_maximize()
    
    def get_random_position(self):
        parent = self.parent()
        if parent:
            parent_width = parent.width()
            parent_height = parent.height()
            
            window_width = 340
            window_height = 260
            
            offset_x = (EMdiSubWindow._window_counter * 30) % 200
            offset_y = (EMdiSubWindow._window_counter * 20) % 150
            
            max_x = max(0, parent_width - window_width - 50)
            max_y = max(0, parent_height - window_height - 80)
            
            x = min(offset_x + 30, max_x) if max_x > 0 else offset_x + 30
            y = min(offset_y + 30, max_y) if max_y > 0 else offset_y + 30
            
            return x, y
        return 50, 50
    
    def animate_maximize(self):
        if self._is_maximizing:
            return
        
        self._is_maximizing = True
        self._normal_geometry = self.geometry()
        
        parent = self.parent()
        if parent:
            target_rect = parent.rect()
            if isinstance(parent, QMdiArea):
                target_rect = parent.viewport().rect()
            
            target_rect.setHeight(target_rect.height() - 35)
            
            start_geometry = self.geometry()
            self.raise_()
            self.geometry_animation = QPropertyAnimation(self, b"geometry")
            self.geometry_animation.setDuration(220)
            self.geometry_animation.setStartValue(start_geometry)
            self.geometry_animation.setEndValue(target_rect)
            self.geometry_animation.setEasingCurve(QEasingCurve.Type.OutExpo)
            self.geometry_animation.finished.connect(self._on_maximize_finished)
            self.geometry_animation.start()
    
    def animate_restore(self):
        if self._is_maximizing or not self._normal_geometry:
            return
        
        self._is_maximizing = True
        
        start_geometry = self.geometry()
        
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(250)
        self.geometry_animation.setStartValue(start_geometry)
        self.geometry_animation.setEndValue(self._normal_geometry)
        self.geometry_animation.setEasingCurve(QEasingCurve.Type.OutExpo)
        self.geometry_animation.finished.connect(self._on_restore_finished)
        self.geometry_animation.start()
    
    def _on_maximize_finished(self):
        self._is_maximizing = False
        self.showMaximized()
    
    def _on_restore_finished(self):
        self._is_maximizing = False
        self.showNormal()
        self.setGeometry(self._normal_geometry)
        if hasattr(self, 'maximizeButton'):
            self.maximizeButton.setText("□")
    
    def animate_minimize(self):
        self.raise_()
        self.minimize_animation = QPropertyAnimation(self, b"windowOpacity")
        self.minimize_animation.setDuration(150)
        self.minimize_animation.setStartValue(1.0)
        self.minimize_animation.setEndValue(0.0)
        self.minimize_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.minimize_animation.finished.connect(self._on_minimize_finished)
        self.minimize_animation.start()
    
    def _on_minimize_finished(self):
        self.setWindowOpacity(0.0)
        self.showMinimized()
        self.setWindowOpacity(1.0)
    
    def _titlebar_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.isMaximized():
                self._is_dragging = True
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            else:
                self._drag_position = event.globalPos()
                self.animate_restore()
                self._is_dragging = True
            event.accept()
    
    def _titlebar_mouse_move(self, event):
        if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton and not self.isMaximized():
            new_pos = event.globalPos() - self._drag_position
            self.move(new_pos)
            event.accept()
    
    def _titlebar_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            event.accept()
    
    def _show_titlebar_menu(self, position):
        menu = QMenu(self.TitleBar)
        
        minimize_action = menu.addAction("最小化")
        if self.allow_resize:
            if self.isMaximized():
                restore_action = menu.addAction("还原")
                maximize_action = menu.addAction("最大化")
                maximize_action.setEnabled(False)
            else:
                maximize_action = menu.addAction("最大化")
                restore_action = menu.addAction("还原")
                restore_action.setEnabled(False)
        menu.addSeparator()
        close_action = menu.addAction("关闭")
        
        minimize_action.triggered.connect(self.animate_minimize)
        if self.allow_resize:
            maximize_action.triggered.connect(self.animate_maximize)
            restore_action.triggered.connect(self.animate_restore)
        close_action.triggered.connect(self.close_with_callback)
        
        menu.exec(self.TitleBar.mapToGlobal(position))
    
    def play_show_animation(self):
        if self._is_animating_in:
            return
        
        self._is_animating_in = True
        # 去掉缩放子控件几何的高开销动画，只保留轻量的淡入
        self.set_scale_factor(1.0)
        self.set_opacity_animation(0.0, 1.0, 220,
                                   easing=QEasingCurve.Type.OutCubic,
                                   finished=self._on_show_animation_finished)
    
    def _on_show_animation_finished(self):
        self._is_animating_in = False
        if hasattr(self, 'main_layout') and self.main_layout:
            self.main_layout.activate()
    
    def play_close_animation(self, callback=None):
        if self._is_closing:
            return
        
        self._is_closing = True
        self._close_callback = callback
        
        if self._taskbar_registered:
            self._taskbar_manager.unregister_window(self)
            self._taskbar_registered = False
        
        # 只做轻量淡出，省去缩放子控件的开销
        self.set_opacity_animation(1.0, 0.0, 200,
                                   easing=QEasingCurve.Type.InCubic,
                                   finished=self._on_close_animation_finished)
    
    def _on_close_animation_finished(self):
        self.closeAnimationFinished.emit()

        # 窗口真正关闭时终止其后台线程
        self.terminate_thread()

        if self._close_callback is not None:
            self._close_callback = None
        
        self.close()
    
    def closeEvent(self, event):
        if self._is_closing:
            event.accept()
            return
        
        event.ignore()
        self.play_close_animation()
    
    def close_with_callback(self, callback=None):
        self.raise_()
        if hasattr(self, 'main_layout'):
            self.main_layout.deleteLater()
            clear_layout(self.main_layout)
        self.play_close_animation(callback)

    # ----------------------------------------------------------------
    # 线程生命周期管理（公开 API）
    # ----------------------------------------------------------------

    def post_task(self, func, *args, **kwargs):
        """把函数投递到该窗口的独立线程执行（不阻塞主线程）。"""
        worker = getattr(self, '_worker', None)
        if worker is not None:
            worker.task.emit(func, args, kwargs)

    def terminate_thread(self):
        """终止该窗口的后台线程（先优雅退出，超时则强制终止）。"""
        t = getattr(self, '_worker_thread', None)
        if t is None:
            return
        if t.isRunning():
            t.quit()
            if not t.wait(1000):
                t.terminate()
                t.wait(1000)

    def close_and_terminate(self):
        """公开 API：关闭窗口并终止其后台线程。供任务按钮右键菜单等外部调用。"""
        self.terminate_thread()
        self.close_with_callback()
    
    def resizeEvent(self, event):
        if not self.allow_resize and not self.isMaximized():
            event.ignore()
            return
        super().resizeEvent(event)
    
    def focusInEvent(self, event):
        self.raise_()
        if self._taskbar_registered:
            window_id = id(self)
            if window_id in self._taskbar_manager._taskbar_windows:
                button = self._taskbar_manager._taskbar_windows[window_id]
                button.setStyleSheet("background-color: rgba(255, 255, 255, 30); border-radius: 3px;")
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        if self._taskbar_registered:
            window_id = id(self)
            if window_id in self._taskbar_manager._taskbar_windows:
                button = self._taskbar_manager._taskbar_windows[window_id]
                button.setStyleSheet("")
        super().focusOutEvent(event)

class ETaskBar(QFrame):
    def __init__(self,parent : QWidget = None):
        super().__init__(parent)
        
        self.setFixedHeight(30)
        self.setAcceptDrops(True)
        self._init_gui_()
        self.update_colors()
        QApplication.instance().paletteChanged.connect(self.update_colors)
        
        self._window_manager = TaskBarWindowManager()
        self._window_manager.set_taskbar_widget(self)
    
    def get_window_manager(self):
        """获取任务栏窗口管理器"""
        return self._window_manager
    
    def dragEnterEvent(self, event):
        """任务栏拖拽进入"""
        if event.mimeData().hasFormat("application/x-button-index"):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """任务栏放下"""
        if not event.mimeData().hasFormat("application/x-button-index"):
            return
        
        data = event.mimeData().data("application/x-button-index").data()
        if not data:
            return
        
        try:
            source_index = int(data.decode())
        except (ValueError, UnicodeDecodeError):
            return
        
        layout = self._layout
        if not layout:
            return
        
        if source_index < 0 or source_index >= layout.count():
            return
        
        drop_pos = event.pos()
        target_index = -1
        
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget.geometry().contains(drop_pos):
                    target_index = i
                    break
        
        if target_index == -1 and layout.count() > 0:
            last_widget = layout.itemAt(layout.count() - 1).widget()
            if last_widget and drop_pos.x() > last_widget.geometry().right():
                target_index = layout.count()
        
        if target_index == -1:
            target_index = layout.count()
        
        if source_index == target_index:
            event.acceptProposedAction()
            return
        
        if target_index < 0 or target_index > layout.count():
            event.acceptProposedAction()
            return
        
        source_widget = layout.itemAt(source_index).widget()
        if not source_widget:
            event.acceptProposedAction()
            return
        
        layout.insertWidget(target_index, source_widget)
        event.acceptProposedAction()
    
    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128
        
        if is_dark:
            default = read_config_value("Theme_Dark", "default_theme_color")
            if default:
                background = re.findall(r'taskbar_color:(.+?);', default)
                color = re.findall(r'color:(.+?);', default)
                if background and color:
                    self.setStyleSheet(f"""
                    QFrame{{
                        background-color : {background[0]};
                        color : {color[0]}            
                    }}
                    """)
        else:
            default = read_config_value("Theme_Light", "default_theme_color")
            if default:
                background = re.findall(r'taskbar_color:(.+?);', default)
                color = re.findall(r'color:(.+?);', default)
                if background and color:
                    self.setStyleSheet(f"""
                    QFrame{{
                        background-color : {background[0]};
                        color : {color[0]}            
                    }}
                    """)
    
    def _init_gui_(self):
        self._layout = QHBoxLayout(self)
        self._layout.setSpacing(5)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._layout.setContentsMargins(10, 0, 10, 0)
    
    def addStretch(self):
        self._layout.addStretch()
    
    def addWidget(self, widget: QWidget, stretch: int = 0):
        """向任务栏末尾添加任意控件"""
        self._layout.addWidget(widget, stretch)
    
    def addButton(self, info: str, width: int = 0, event=air):
        button = Button(info, None, border_radius=3, border_width=0, transparent=255)
        button.setFixedHeight(30)

        button.clicked.connect(event)
        
        if width > 0:
            button.setFixedWidth(width)
        self._layout.addWidget(button)