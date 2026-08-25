from pack.libs.gui.QtPack import *
# ImportError ('Missing resource pack "QMarkdownWidget"')

class MarkLabel(QWidget):
    def __init__(self, text: str = "", parent: QWidget = None, text_alignment: Qt.AlignmentFlag = Qt.AlignLeft):
        super().__init__(parent)
        
        self._text = text
        self._alignment = text_alignment
        self._word_wrap = True
        
        # 创建滚动区域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 滚动区域透明背景
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent !important;
                border: none !important; 
            }
        """)
        
        # 创建容器
        self.container = QWidget(self.scroll_area)
        self.container.setStyleSheet("background: transparent !important;")
        
        # 创建 Markdown 标签
        self.label = QLabel(text, self.container)
        self.label.setAlignment(text_alignment)
        self.label.setStyleSheet("""
            QMLabel {
                background: transparent !important;
                padding: 4px!important;
            }
        """)
        
        # 容器布局
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.label)
        
        self.scroll_area.setWidget(self.container)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)
        
        # 设置滚动条样式
        self._setup_scrollbar_style()
        
        # 🔥 关键修复：安装事件过滤器到容器
        self.container.installEventFilter(self)
        
        # 延迟初始化宽度
        QTimer.singleShot(50, self._update_label_width)
    
    def eventFilter(self, obj, event):
        """🔥 修复：使用 QEvent.Resize 而不是 event.Resize"""
        if obj == self.container and event.type() == QEvent.Resize:
            self._update_label_width()
        return super().eventFilter(obj, event)
    
    def _update_label_width(self):
        """设置标签宽度实现换行"""
        if self._word_wrap:
            width = self.container.width() - 8
            if width > 10:
                self.label.setFixedWidth(width)
        else:
            self.label.setFixedWidth(16777215)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_label_width()
    
    def showEvent(self, event):
        super().showEvent(event)
        # 显示时确保宽度正确
        self._update_label_width()
    
    def setText(self, text: str):
        self._text = text
        self.label.setText(text)
        QTimer.singleShot(10, self._update_label_width)
    
    def text(self) -> str:
        return self._text
    
    def setAlignment(self, alignment: Qt.AlignmentFlag):
        self._alignment = alignment
        self.label.setAlignment(alignment)
    
    def alignment(self) -> Qt.AlignmentFlag:
        return self._alignment
    
    def setWordWrap(self, enabled: bool):
        self._word_wrap = enabled
        self._update_label_width()
    
    def wordWrap(self) -> bool:
        return self._word_wrap
    
    def _setup_scrollbar_style(self):
        """自定义滚动条样式"""
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent !important;
                border: none;
            }
            
            QScrollBar:vertical {
                background: transparent !important;
                width: 6px;
                border: none;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(128, 128, 128, 0.5) !important;
                border-radius: 3px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(128, 128, 128, 0.8) !important;
            }
            
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical {
                height: 0px;
                background: transparent;
            }
            
            QScrollBar:horizontal {
                height: 0px;
                background: transparent;
            }
        """)