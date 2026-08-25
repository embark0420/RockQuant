from pack.libs.gui.QtPack import *
from pack.libs.gui.widget import *
from pack.libs.gui.ReadConfigFile import *
from pack.libs.gui.RippleButton import *

class InfoWidget(QFrame):
    def __init__ (self, parent : QWidget = None, text : str = '', title : str = "", mode : str = "Node"):

        super().__init__(parent)

        self.mode = mode
        self.title = title
        self.text = text

        self._initgui()
        self._setStyleSheet(self.mode)
        self.xclose = RippleButton("x",self)
        self.xclose.clicked.connect(self.deleteLater)
    def _initgui(self):
        self.layoutc = QVBoxLayout(self)
        self.layoutc.setContentsMargins(5,5,5,5)
        self.layoutc.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layoutc.setSpacing(0)


        title = QWidget()
        title.setFixedHeight(30)
        title_layout = QHBoxLayout(title)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.setContentsMargins(0,0,0,0)

        self.iconA = ImageWidget(None, path / "Theme/node.png")
        self.iconA.setFixedWidth(30)

        title_label = QLabel(self.title)    
        title_label.setStyleSheet("QLabel{color : white; }")
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)

        title_layout.addWidget(self.iconA)
        title_layout.addWidget(title_label)


        self.layoutc.addWidget(title)

        # 正文文本显示区域
        self.body_label = QLabel(self.text)
        self.body_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.body_label.setWordWrap(True)          # 长文本自动换行
        self.body_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 可选中复制
        self.body_label.setStyleSheet("""
            QLabel{
                color: white;
                background: transparent;
                font-size: 12px;
            }
        """)
        self.layoutc.addWidget(self.body_label)

    def set_text(self, text: str):
        """更新正文文本"""
        self.text = text
        if hasattr(self, 'body_label') and self.body_label is not None:
            self.body_label.setText(text)

    def _setStyleSheet(self, mode):

        if mode == "Info":
            self.setStyleSheet("""
                InfoWidget{
                    color : white;
                    background-color : rgba(54,172,240,120);
                    border : 1px solid rgba(0,172,240,80);
                    border-top : 1px solid rgba(255,255,255,50);
                    border-radius : 6px;
                } 
            """)
        if mode == "Error":
            self.iconA.load_image(path / "Theme/error.png")
            self.setStyleSheet("""
                InfoWidget{
                    color : white;
                    background-color : rgba(229,54,54,190);
                    border : 1px solid rgba(255,35,35,80);
                    border-top : 1px solid rgba(255,255,255,50);
                    border-radius : 6px;
                } 
            """)
        if mode == "Wran":
            self.iconA.load_image(path / "Theme/wran.png")
            self.setStyleSheet("""
                InfoWidget{
                    color : white;
                    background-color : rgba(222,201,64,190);
                    border : 1px solid rgba(222,201,64,80);
                    border-top : 1px solid rgba(255,255,255,50);
                    border-radius : 6px;
                } 
            """)
        if mode == "Node":
            self.iconA.load_image(path / "Theme/node.png")
            self.setStyleSheet("""
                InfoWidget{
                    color : white;
                    background-color : rgba(135,135,135,190);
                    border : 1px solid rgba(135,135,135,80);
                    border-top : 1px solid rgba(255,255,255,50);
                    border-radius : 6px;
                } 
            """)

    def resizeEvent(self,event):

        self.xclose.setGeometry(self.width()-35,5,30,30)
        super().resizeEvent(event)