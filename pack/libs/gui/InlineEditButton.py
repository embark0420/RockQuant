from pack.libs.gui.QtPack import *
from pack.libs.gui.TaskButton import *
from pack.libs.gui.TaskButton import *
from pack.libs.gui.lineedit import *

class InlineEditButton(TaskButton):
    editCompleted = pyqtSignal(str)  # 编辑完成信号，发射新文本

    def __init__(self, text="", parent=None, border_width=1, text_alignment="center", shadow=False,setPlaceholderText :str = "回车确定...",ModifyTheOriginalText:bool = False):
        super().__init__(text, parent, border_radius=border_width, border_width=border_width, text_alignment=text_alignment)

        self.clicked.connect(self._click_event_)
        self.acx = 0
        self.lineedit = None
        self.setPlaceholderText = setPlaceholderText
        self.ModifyTheOriginalText = ModifyTheOriginalText
        self.ReturnText = None
        self.InputText = ""

    def _click_event_(self):
        self.acx = 1
        self.setEnabled(False)
        self.setVisible(False)
        
        # 创建简单的弹出窗口
        self.lineedit = QWidget()
        self.lineedit.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.lineedit.resize(self.width(), self.height())
        
        layout = QVBoxLayout(self.lineedit)
        layout.setContentsMargins(0, 0, 0, 0)  # 留点边距
        
        self.inner_edit = LineEdit(border_radius=0)
        self.inner_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inner_edit.setFixedHeight(self.height())
        self.inner_edit.setPlaceholderText(str(self.setPlaceholderText))
        self.inner_edit.returnPressed.connect(self.on_return_pressed)
        layout.addWidget(self.inner_edit)

        pos = self.mapToGlobal(QPoint(0, 0))
        self.lineedit.move(pos)
        self.lineedit.show()
        self.inner_edit.setFocus()
        if self.ModifyTheOriginalText == True:
            self.inner_edit.setText(str(self.text()))
        else:
            self.inner_edit.setText(str(self.InputText))
        # 安装应用程序级别的事件过滤器来检测外部点击
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.MouseButtonPress and 
            self.lineedit and 
            self.lineedit.isVisible() and
            obj != self.inner_edit and  # 不是内部编辑框
            not self._is_child_of_popup(obj)):  # 不是弹出窗口的子部件
            self.restore_button()
            return True
            
        return super().eventFilter(obj, event)
    
    def _is_child_of_popup(self, obj):
        """检查对象是否是弹出窗口的子部件"""
        if not isinstance(obj, QWidget):
            return False
        parent = obj.parent()
        while parent:
            if parent == self.lineedit:
                return True
            parent = parent.parent()
        return False

    def on_return_pressed(self):
        """回车键确认"""
        if self.ModifyTheOriginalText == True:
            self.setText(f"{self.inner_edit.text()}")
        else:
            if self.ModifyTheOriginalText == False:
                self.InputText = self.inner_edit.text()

        self.ReturnText = self.inner_edit.text()
        self.editCompleted.emit(self.ReturnText)
        self.restore_button()
    def return_text(self):
        return self.ReturnText
    def restore_button(self):
        """恢复按钮"""
        
        # 移除事件过滤器
        QApplication.instance().removeEventFilter(self)
        
        # 恢复按钮
        self.acx = 0
        self.setEnabled(True)
        self.setVisible(True)
        
        # 清理弹出窗口
        if self.lineedit:
            self.lineedit.hide()
            self.lineedit.deleteLater()
            self.lineedit = None
            
        self.update()


    def paintEvent(self, arg__1):
        return super().paintEvent(arg__1)
