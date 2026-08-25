from pack.libs.gui.QtPack import *


class Separator(QFrame):
    def __init__(self, parent: QWidget = None, orientation: Qt.Orientation = Qt.Horizontal, style_type: str = "modern"):
        super().__init__(parent)
        
        self.orientation = orientation
        self.style_type = style_type
        
        # 设置框架形状
        if orientation == Qt.Horizontal:
            self.setFrameShape(QFrame.HLine)
            self.setFixedHeight(2)  # 基础厚度
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        else:
            self.setFrameShape(QFrame.VLine)
            self.setFixedWidth(2)
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            
        self.setFrameShadow(QFrame.Plain)
        self.setObjectName("Separator")
        
        # 应用样式
        self.apply_style(style_type)
    
    def apply_style(self, style_type: str = None):
        """应用不同的分隔符样式"""
        if style_type:
            self.style_type = style_type
            
        # 🔥 修复：所有样式都加上 min-height/width 防止被压缩
        if self.orientation == Qt.Horizontal:
            base_style = """
            Separator {
                background-color: #e0e0e0;
                border: none;
                margin: 1px 0px;
                min-height: 1px;
            }
            """
        else:
            base_style = """
            Separator {
                background-color: #e0e0e0;
                border: none;
                margin: 0px 1px;
                min-width: 1px;
            }
            """
        
        # 根据样式类型微调
        if self.style_type == "modern":
            style = base_style
        elif self.style_type == "minimal":
            style = base_style.replace("#e0e0e0", "#f0f0f0")
        elif self.style_type == "bold":
            if self.orientation == Qt.Horizontal:
                style = base_style.replace("#e0e0e0", "#cccccc").replace("margin: 1px 0px;", "margin: 2px 0px;")
            else:
                style = base_style.replace("#e0e0e0", "#cccccc").replace("margin: 0px 1px;", "margin: 0px 2px;")
        elif self.style_type == "gradient":
            if self.orientation == Qt.Horizontal:
                gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 #c0c0c0, stop:1 transparent)"
                margin_val = "margin: 1px 0px;"
            else:
                gradient = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 transparent, stop:0.5 #c0c0c0, stop:1 transparent)"
                margin_val = "margin: 0px 1px;"
            style = f"""
            Separator {{
                background: {gradient};
                border: none;
                {margin_val}
                min-height: 1px;
                min-width: 1px;
            }}
            """
        elif self.style_type == "dotted":
            if self.orientation == Qt.Horizontal:
                style = """
                Separator {
                    background: repeating-linear-gradient(to right, #c0c0c0, #c0c0c0 2px, transparent 2px, transparent 4px);
                    border: none;
                    margin: 1px 0px;
                    min-height: 1px;
                }
                """
            else:
                style = """
                Separator {
                    background: repeating-linear-gradient(to bottom, #c0c0c0, #c0c0c0 2px, transparent 2px, transparent 4px);
                    border: none;
                    margin: 0px 1px;
                    min-width: 1px;
                }
                """
        else:
            style = base_style
        
        self.setStyleSheet(style)
    
    def set_color(self, color: str):
        """动态设置分隔符颜色"""
        if self.orientation == Qt.Horizontal:
            margin_val = "margin: 1px 0px;"
            size_rule = "min-height: 1px;"
        else:
            margin_val = "margin: 0px 1px;"
            size_rule = "min-width: 1px;"
            
        style = f"""
        Separator {{
            background-color: {color};
            border: none;
            {margin_val}
            {size_rule}
        }}
        """
        self.setStyleSheet(style)
    
    def set_thickness(self, thickness: int):
        """设置分隔符粗细"""
        if self.orientation == Qt.Horizontal:
            self.setFixedHeight(thickness)
            self.setMinimumHeight(thickness)
        else:
            self.setFixedWidth(thickness)
            self.setMinimumWidth(thickness)