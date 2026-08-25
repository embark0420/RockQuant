from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pack.libs.gui.ReadConfigFile import *
from PyQt5.QtCore import *
import re


class MainWindows(QMainWindow):
    def __init__ (self,parent : QWidget):
        super().__init__(parent)

        self.resize(420,450)
        self.setWindowTitle("MainWindows示例")
        self.update_colors()
        QApplication.instance().paletteChanged.connect(self.update_colors)

    def update_colors(self):
        palette = QApplication.palette()
        is_dark = palette.window().color().lightness() < 128
        
        if is_dark:
            self.setStyleSheet(f"""
            QMainWindow {{               
                background-color: {re.findall(r'taskbar_color:(.+?);', read_config_value('Theme_Dark', 'default_theme_color'))[0]}; color: {re.findall(r'color:(.+?);', read_config_value('Theme_Dark', 'default_theme_color'))[0]};
            }}
            """)
        else:
            self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {re.findall(r'taskbar_color:(.+?);', read_config_value('Theme_Light', 'default_theme_color'))[0]}; color: {re.findall(r'color:(.+?);', read_config_value('Theme_Light', 'default_theme_color'))[0]};
            }}
            """)