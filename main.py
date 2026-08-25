from PyQt5.QtWidgets import*
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pack.libs.gui.button import *
from pack.libs.gui.button.PopupMenuButton import *
from pack.libs.gui.lineedit import *
from pack.libs.gui.widget.InformationWidget import *
from pack.libs.gui.frame import *
from pack.libs.gui.label import *
from pack.libs.gui.shadow import *
from pack.libs.gui.widget import *
from pack.libs.gui.ProfilePictureWidget import *

import os
import sys
import subprocess


app = QApplication([])
from pack.libs.fonts.SegoeAssets import *

class MainWindow(QMainWindow):
    def __init__ (self, parent : QWidget = None):
        super().__init__(parent)

        self.S = False
        screen = QDesktopWidget().screenGeometry()
        width = screen.width()
        height = screen.height()
        
        # 设置窗口铺满屏幕
        self.setGeometry(0, 0, width, height)

        self._initgui()
    def _initgui(self):
        self.main_widget = ImageWidget(
            image=str(pathlib.Path(__file__).resolve().parent / "background.jpg"),
            blur_radius=40,  # 背景模糊半径（像素），>0 生效
        )
        self.setCentralWidget(self.main_widget)

        # ---------- 现代化配色 ----------
        PRIMARY = "#5b7cfa"      # 主色（蓝紫）
        PRIMARY_HOVER = "#7b97ff"
        PRIMARY_PRESSED = "#4a63d8"
        ACCENT_A = "#5b7cfa"     # 渐变起点
        ACCENT_B = "#8e5cff"     # 渐变终点
        TEXT_MAIN = "#f2f3f7"    # 主文字
        TEXT_SUB = "#9aa3b2"     # 次要文字
        INPUT_BG = "rgba(255,255,255,0.08)"
        INPUT_BG_HOVER = "rgba(255,255,255,0.13)"
        CARD_BG = "rgba(28,31,44,0.82)"
        CARD_BORDER = "rgba(255,255,255,0.12)"
        # 头像
        self.avatar = ProfilePictureWidget(
            parent=self,
            background_color="transparent",
            border_width = 4,
            image_path=r"C:\Users\wuyue\Downloads\debian_linux_5242.png"
        )
        

        title = Label("User", self, 22)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #ffffff !important;
                font-size: 22px !important;
                font-weight: 600 !important;
                background: transparent !important;
            }
        """)
        title.setGeometry(self.avatar.x(), self.avatar.y()+self.avatar.height(), self.avatar.width(), 32)


        # 账户输入
        self.username = LineEdit(self, border_radius=10, border_width=0, alpha=255)
        self.username.setPlaceholderText("账户")
        self.username.setGeometry(38, 92, 304, 42)

        # 密码输入
        self.password = LineEdit(self, border_radius=5, border_width=1, alpha=90)
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(QLineEdit.Password)   # 密码框显示为圆点
        self.password.setGeometry(38, 144, 304, 30)

        # 登录按钮（渐变 + 悬停/按下反馈）
        yes = RippleButton("登录", self, corner_radius=5, border_width=0)
        yes.setCursor(Qt.PointingHandCursor)
        yes.setGeometry(38, 206, 90, 30)
        yes.clicked.connect(self.login)                 # 点击登录触发提权流程

        # 电源按钮（右上角）
        Power = TaskPopupButton("\ue7e8", self.main_widget, direction='left', border_width=0)
        Power.setGeometry(self.width()-46, 12, 32, 32)
        Power.setFont(SegoeMDL2Assets.font)
        Power.addButton("关机")
        Power.addSeparator()
        Power.addButton("重启")



    def resizeEvent(self,event):

        if self.S == False:
            self.avatar.setFixedSize(180,180)
            self.avatar.setGeometry(int(self.width()/2-180/2),int(self.height()/3-180/2),180,180)
        super().resizeEvent(event)

    def login(self):
        """点击登录：校验密码后关闭 main.py 并启动 DesktopWidget.py。"""
        user = self.username.text().strip()
        pwd  = self.password.text()

        if not user or not pwd:
            self._show_error("用户名或密码不能为空")
            return

        desktop_script = str(pathlib.Path(__file__).resolve().parent / "DesktopWidget.py")

        if sys.platform.startswith("linux"):
            # Linux (Rock S0)：不使用默认密码，通过 sudo -S 验证真实密码
            try:
                check = subprocess.run(
                    ["sudo", "-S", "-k", "-v"],
                    input=(pwd + "\n").encode(),
                    capture_output=True,
                    timeout=10,
                )
                if check.returncode != 0:
                    self._show_error("密码错误，或无 sudo 权限")
                    return
            except Exception as e:
                self._show_error("sudo 验证出错")
                return

            # 密码有效：关闭当前登录窗口，再用 sudo 启动 DesktopWidget.py
            self.close()
            QApplication.processEvents()

            p = subprocess.Popen(
                ["sudo", "-S", sys.executable, desktop_script],
                stdin=subprocess.PIPE,
            )
            p.communicate((pwd + "\n").encode())
        else:
            # 非 Linux（开发环境）：直接启动
            self.close()
            QApplication.processEvents()
            subprocess.Popen([sys.executable, desktop_script])

        # 退出当前 main.py 进程
        QApplication.instance().quit()

    def _show_error(self, msg: str, mode: str = "Error"):
        """在窗口左下角弹出 InfoWidget 提示"""
        # 移除旧的提示
        old = getattr(self, '_info_widget', None)
        if old is not None:
            try:
                old.deleteLater()
            except RuntimeError:
                pass

        head = "错误" if mode == "Error" else ("警告" if mode == "Wran" else "提示")
        w = InfoWidget(self, text=msg, title=head, mode=mode)
        # 高度随正文自动伸缩（标题栏 30px + 正文行高）
        w.setFixedWidth(340)
        w.adjustSize()
        w.setFixedHeight(w.sizeHint().height())
        x = 16
        y = self.height() - w.height() - 16
        w.move(x, y)
        w.show()
        w.raise_()
        self._info_widget = w

if __name__ == "__main__":
    

    window = MainWindow()
    
    window.show()

    app.exec()