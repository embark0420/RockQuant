import os
import pathlib
import subprocess
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from pack.libs.gui.Control import EMdiSubWindow
from pack.libs.gui.button import *

IS_LINUX = sys.platform.startswith("linux")
IS_WIN   = sys.platform.startswith("win")


def _run(cmd, timeout=4000):
    """跨平台执行命令并返回 (exit_code, stdout_text)。找不到命令时返回 (None, '')。"""
    try:
        p = subprocess.run(cmd, capture_output=True, text=False, timeout=timeout / 1000.0)
        out = (p.stdout or b"").decode("utf-8", errors="replace")
        err = (p.stderr or b"").decode("utf-8", errors="replace")
        return p.returncode, out + err
    except FileNotFoundError:
        return None, ""
    except subprocess.TimeoutExpired:
        return -1, "(超时)"


def _hostname():
    try:
        return os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME", "Unknown")
    except Exception:
        return "Unknown"


class FormRow(QHBoxLayout):
    """一行“标签 + 控件”的经典表单行。"""
    def __init__(self, label: str, widget: QWidget):
        super().__init__()
        self.setContentsMargins(0, 2, 0, 2)
        self.setSpacing(6)
        lbl = QLabel(label)
        lbl.setFixedWidth(90)
        lbl.setObjectName("FormLabel")
        self.addWidget(lbl)
        self.addWidget(widget, 1)


class SettingWidget(QWidget):
    """Windows 98 经典复古风格的设置面板：左侧导航 + 右侧经典 3D 凹陷分组框。

    已适配 Linux / Windows：
    - 网络：拓扑探测 Wi-Fi / 以太网 / 蓝牙 / 代理，真实读取系统网络状态。
    - 个性化：壁纸与强调色通过信号交给宿主 DesktopWidget 应用（而非系统桌面）。
    """

    # 个性化应用请求：交给宿主（DesktopWidget）把壁纸/强调色作用到自身界面。
    wallpaperApplyRequested = pyqtSignal(str)     # 壁纸图片路径
    accentApplyRequested    = pyqtSignal(QColor)  # 强调色（用于任务栏等）

    NAV_ITEMS = ["系统", "网络", "个性化", "应用"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nav_buttons = []
        self._pages = {}
        self._init_ui()
        self._apply_style()
        self._switch_page("网络")
        # 进入后延迟刷新动态数据，避免阻塞弹窗
        QTimer.singleShot(120, self._refresh_network)
        QTimer.singleShot(160, self._refresh_personalization)

    # ==================================================================
    # UI 骨架
    # ==================================================================
    def _init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # ---------- 左侧导航（经典凹陷竖条） ----------
        self.sidebar = QFrame(self)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(140)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(4, 4, 4, 4)
        sidebar_layout.setSpacing(3)

        for name in self.NAV_ITEMS:
            btn = Button(name,border_width=0,border_radius=0,text_alignment = "left")
            btn.setCheckable(False)   # 非 toggle，按下立即弹回
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(25)
            btn.clicked.connect(lambda checked, n=name: self._switch_page(n))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # ---------- 右侧内容区（每页包一层 QScrollArea，内容超高时可滚动） ----------
        self.stack = QStackedWidget(self)
        builders = {
            "系统":   self._build_system_page,
            "网络":   self._build_network_page,
            "个性化": self._build_personalization_page,
            "应用":   self._build_apps_page,
        }
        self._scroll_areas = {}
        for name in self.NAV_ITEMS:
            page = builders[name]()
            self._pages[name] = page

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidget(page)

            # 记录滚动区域，便于切换页面时回到顶部或在外部调整
            self._scroll_areas[name] = scroll
            self.stack.addWidget(scroll)

        root.addWidget(self.sidebar)
        root.addWidget(self.stack, 1)

    def _wrap_scroll(self, page: QWidget) -> QScrollArea:
        """把页面包装进可滚动容器（供需要时复用）。"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(page)
        return scroll

    # ==================================================================
    # 页面通用外壳
    # ==================================================================
    def _page_scaffold(self, title: str):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)
        group = QGroupBox(title)
        glay = QVBoxLayout(group)
        glay.setContentsMargins(10, 18, 10, 10)
        glay.setSpacing(6)
        lay.addWidget(group)
        return page, group, glay

    def _switch_page(self, name):
        self.stack.setCurrentIndex(self.NAV_ITEMS.index(name))
        # 切换页面时把该页滚动区滚回顶部
        scroll = self._scroll_areas.get(name)
        if scroll is not None:
            scroll.verticalScrollBar().setValue(0)
            scroll.horizontalScrollBar().setValue(0)
        for btn in self._nav_buttons:
            btn.setProperty("active", btn.text() == name)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ==================================================================
    # 系统页
    # ==================================================================
    def _build_system_page(self):
        page, group, glay = self._page_scaffold("系统")
        self._sys_info = QLabel()
        self._sys_info.setObjectName("Mono")
        self._sys_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._sys_info.setText(
            f"主机名：{_hostname()}\n系统：{sys.platform}  (Python {sys.version.split()[0]})\n"
            "桌面：RockQuant (Windows 98 复古风格)"
        )
        glay.addWidget(self._sys_info)

        self._cpu_label = QLabel("处理器：…")
        self._mem_label = QLabel("内存：…")
        glay.addWidget(self._cpu_label)
        glay.addWidget(self._mem_label)

        refresh = QPushButton("刷新")
        refresh.setFixedWidth(90)
        refresh.clicked.connect(self._refresh_system)
        glay.addWidget(refresh, 0, Qt.AlignLeft)
        glay.addStretch()
        self._refresh_system()
        return page

    def _refresh_system(self):
        info = self._sys_info.text()
        if "主机名" not in info:
            self._sys_info.setText(
                f"主机名：{_hostname()}\n系统：{sys.platform}  (Python {sys.version.split()[0]})"
            )
        if IS_LINUX:
            cpu = _run(["sh", "-c", "grep 'model name' /proc/cpuinfo | head -1 | sed 's/.*: //'"])[1].strip()
            mem = _run(["sh", "-c",
                        "awk '/MemTotal/{t=$2} /MemAvailable/{a=$2} END{printf \"%.1f / %.1f GB\", a/1048576, t/1048576}' "
                        "/proc/meminfo"])[1].strip()
        else:
            cpu = _run(["wmic", "cpu", "get", "name"])[1].replace("Name", "").strip().splitlines()
            cpu = cpu[0].strip() if cpu and cpu[0].strip() else "(未知)"
            mem = "(Windows 内存信息)"
        self._cpu_label.setText(f"处理器：{cpu or '(未知)'}")
        self._mem_label.setText(f"内存：{mem or '(未知)'}")

    # ==================================================================
    # 网络页
    # ==================================================================
    # 站点名 -> (端口, 图标字符)。空端口表示无需代理。
    PROXY_TARGETS = [
        ("HTTP",      "8080"),
        ("HTTPS",     "8080"),
        ("FTP",       "8080"),
        ("SOCKS5",    "1080"),
    ]

    def _build_network_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # ---------- 状态总览 ----------
        overview = QGroupBox("网络状态")
        olay = QVBoxLayout(overview)
        olay.setContentsMargins(10, 18, 10, 10)
        olay.setSpacing(3)
        self.net_status = QLabel("正在检测网络…")
        self.net_status.setObjectName("Mono")
        self.net_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        olay.addWidget(self.net_status)

        btn_row = QHBoxLayout()
        refresh = QPushButton("重新检测")
        refresh.setFixedWidth(100)
        refresh.clicked.connect(self._refresh_network)
        btn_row.addWidget(refresh)
        btn_row.addStretch()
        olay.addLayout(btn_row)
        root.addWidget(overview)

        # ---------- Wi-Fi ----------
        wifi = QGroupBox("Wi-Fi")
        wlay = QVBoxLayout(wifi)
        wlay.setContentsMargins(10, 18, 10, 10)
        wlay.setSpacing(4)
        self.wifi_label = QLabel("…")
        self.wifi_label.setObjectName("Mono")
        self.wifi_label.setWordWrap(True)
        self.wifi_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        wlay.addWidget(self.wifi_label)

        self.wifi_list = QListWidget()
        self.wifi_list.setMaximumHeight(120)
        self.wifi_list.setToolTip("可用 Wi-Fi 网络（点击连接）")
        self.wifi_list.itemClicked.connect(self._on_wifi_pick)
        wlay.addWidget(self.wifi_list)

        wbtn = QPushButton("扫描 Wi-Fi")
        wbtn.setFixedWidth(120)
        wbtn.clicked.connect(self._refresh_wifi)
        wlay.addWidget(wbtn, 0, Qt.AlignLeft)
        root.addWidget(wifi)

        # ---------- 以太网 ----------
        eth = QGroupBox("以太网")
        elay = QVBoxLayout(eth)
        elay.setContentsMargins(10, 18, 10, 10)
        elay.setSpacing(4)
        self.eth_label = QLabel("…")
        self.eth_label.setObjectName("Mono")
        self.eth_label.setWordWrap(True)
        self.eth_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        elay.addWidget(self.eth_label)
        root.addWidget(eth)

        # ---------- 代理 ----------
        proxy = QGroupBox("代理")
        play = QVBoxLayout(proxy)
        play.setContentsMargins(10, 18, 10, 10)
        play.setSpacing(4)
        self.proxy_host = QLineEdit()
        self.proxy_host.setPlaceholderText("代理服务器地址，例如 127.0.0.1")
        play.addLayout(FormRow("服务器", self.proxy_host))

        port_grid = QGridLayout()
        port_grid.setHorizontalSpacing(8)
        port_grid.setVerticalSpacing(4)
        self._proxy_ports = {}
        for i, (name, default) in enumerate(self.PROXY_TARGETS):
            port_grid.addWidget(QLabel(name), i, 0)
            le = QLineEdit(default)
            le.setFixedWidth(70)
            port_grid.addWidget(le, i, 1)
            self._proxy_ports[name] = le
        play.addLayout(port_grid)

        proxy_row = QHBoxLayout()
        self.proxy_enabled = QCheckBox("启用代理")
        self.proxy_enabled.toggled.connect(self._toggle_proxy_fields)
        proxy_row.addWidget(self.proxy_enabled)
        proxy_row.addStretch()
        play.addLayout(proxy_row)
        root.addWidget(proxy)

        qbtn = QHBoxLayout()
        self.proxy_status = QLabel("")
        self.proxy_status.setObjectName("Mono")
        qbtn.addWidget(self.proxy_status)
        qbtn.addStretch()
        apply_proxy = QPushButton("应用代理")
        apply_proxy.setFixedWidth(100)
        apply_proxy.clicked.connect(self._apply_proxy)
        qbtn.addWidget(apply_proxy)
        play.addLayout(qbtn)

        root.addStretch()
        return page

    def _refresh_network(self):
        """刷新网络状态总览：IPv4 地址 / 网关 / DNS / 在线状态。"""
        if IS_LINUX:
            self._refresh_network_linux()
        elif IS_WIN:
            self._refresh_network_windows()
        else:
            self.net_status.setText("不支持自动检测的平台")
            return
        self._refresh_eth()
        self._refresh_wifi_if_capable()

    def _refresh_eth(self):
        """以太网接口状态：Linux 用 ip；Windows 用 netsh 接口信息。"""
        if IS_LINUX:
            rc, out = _run(["sh", "-c",
                            "ls /sys/class/net | grep -Ev '^(wlan|lo)' | tr '\\n' ' '"])
            ifaces = out.strip()
            self.eth_label.setText("有线接口：" + (ifaces or "(无)"))
            return
        if IS_WIN:
            rc, out = _run(["netsh", "interface", "show", "interface"])
            lines = [ln.strip() for ln in (out.splitlines() if out else [])
                     if "已连接" in ln or "Connected" in ln or "状态" in ln]
            self.eth_label.setText("Windows 接口信息：\n" + ("\n".join(lines) if lines else "(无法枚举)"))
            return
        self.eth_label.setText("(不支持)")

    def _refresh_network_linux(self):
        rc, out = _run(["sh", "-c",
                        "ip -4 addr show | grep -E '^\\s*inet ' | "
                        "grep -v '127.0.0.1' | awk '{print $NF, $2}'"])
        addrs = [ln for ln in (out.splitlines() if out else []) if ln.strip()]

        _, raw = _run(["sh", "-c", "ip route | grep default | awk '{print $3}'"])
        gw = raw.strip().splitlines()[0] if raw.strip() else "(无)"

        _, dns_raw = _run(["sh", "-c", "grep nameserver /etc/resolv.conf | awk '{print $2}'"])
        dnss = " ".join(dns_raw.split()) or "(无)"

        # 在线状态：尝试 ping 公共 DNS（超时短）
        rc4, _ = _run(["sh", "-c", "ping -c 1 -W 1 223.5.5.5 >/dev/null 2>&1 && echo up || echo down"])
        online = "在线" if rc4 == 0 else "离线/未探测"

        text = f"主机名：{_hostname()}\n"
        text += "IPv4 地址：\n  " + ("\n  ".join(addrs) if addrs else "(无活动接口)")
        text += f"\n默认网关：{gw}\nDNS 服务器：{dnss}\n网络连接：" + online
        self.net_status.setText(text)

    def _refresh_network_windows(self):
        rc, out = _run(["ipconfig"])
        if rc is None:
            self.net_status.setText("无法读取网络信息")
            return
        # 提取 IPv4 地址（合并多块输出）
        lines = [ln.strip() for ln in (out.splitlines() if out else [])]
        ips = []
        for ln in lines:
            if "IPv4" in ln and ":" in ln:
                ips.append(ln.split(":", 1)[1].strip())
        host = _hostname()
        self.net_status.setText(
            f"主机名：{host}\nIPv4 地址：\n  " + ("\n  ".join(ips) if ips else "(无 IPv4)")
        )

    def _refresh_wifi_if_capable(self):
        if IS_LINUX:
            self._refresh_wifi()
        elif IS_WIN:
            self._refresh_wifi_windows()

    def _refresh_wifi(self):
        """Linux：通过 nmcli 扫描可用网络并显示当前连接。"""
        self.wifi_list.clear()
        current, _ = _run(["nmcli", "-t", "-f", "SSID,SIGNAL,ACTIVE", "dev", "wifi", "list"])
        if current is None:
            self.wifi_label.setText("未检测到 nmcli，无法扫描 Wi-Fi。\n(Linux 请安装 NetworkManager)")
            return
        entries = []
        lines = [ln for ln in (current.splitlines() if current else []) if ln.strip() and ":" in ln]
        for ln in lines:
            parts = ln.split(":")
            if len(parts) < 2:
                continue
            ssid, signal = parts[0], parts[1] if len(parts) > 1 else ""
            active = len(parts) > 2 and parts[2] == "yes"
            entries.append((ssid, signal, active))
        if not entries:
            self.wifi_label.setText("附近没有可用的 Wi-Fi 网络。")
            return
        for ssid, signal, active in entries:
            item = QListWidgetItem(f"{'● 已连接 ' if active else '○ '}{ssid or '(隐藏网络)'}   信号 {signal}%")
            item.setData(Qt.UserRole, ssid)
            self.wifi_list.addItem(item)
            if active:
                self.wifi_list.setCurrentItem(item)
        # 若已连接，通过 nmcli 显示当前连接的强度信息
        self.wifi_label.setText(", ".join(
            f"{ssid}({sig}%)" for ssid, sig, act in entries if act) or "未连接到任何 Wi-Fi")

    def _refresh_wifi_windows(self):
        self.wifi_list.clear()
        rc, out = _run(["netsh", "wlan", "show", "interfaces"])
        seen = set()
        for ln in (out.splitlines() if out else []):
            if "SSID" in ln and ":" in ln and "BSSID" not in ln:
                ssid = ln.split(":", 1)[1].strip()
                if ssid and ssid not in seen:
                    seen.add(ssid)
                    item = QListWidgetItem("● 已连接  " + ssid)
                    item.setData(Qt.UserRole, ssid)
                    self.wifi_list.addItem(item)
        self.wifi_label.setText("Windows Wi-Fi（当前连接如上，扫描需 netsh wlan show networks）")

    def _on_wifi_pick(self, item):
        ssid = item.data(Qt.UserRole)
        if not ssid:
            return
        if IS_LINUX:
            # 图形界面下 nmcli 会弹出密码框
            _run(["nmcli", "dev", "wifi", "connect", ssid], timeout=6000)
            self._refresh_wifi()
        elif IS_WIN:
            _run(["netsh", "wlan", "connect", "name=" + ssid], timeout=6000)
            self._refresh_wifi_windows()

    def _toggle_proxy_fields(self, on):
        for name in self._proxy_ports:
            self._proxy_ports[name].setEnabled(on)
        self.proxy_host.setEnabled(on)

    def _apply_proxy(self):
        if not self.proxy_host.text().strip():
            self.proxy_status.setText("请输入代理服务器地址")
            return
        host = self.proxy_host.text().strip()
        ports = {k: v.text().strip() for k, v in self._proxy_ports.items()}
        if IS_LINUX:
            mode = "none" if not self.proxy_enabled.isChecked() else "manual"
            rc, out = _run(["gsettings", "set", "org.gnome.system.proxy", "mode", mode])
            if rc is not None and not out.strip():
                # GNOME 代理键：HTTP/HTTPS/FTP/SOCKS 各自保存 host+port
                mapping = {"HTTP": "http", "HTTPS": "https", "FTP": "ftp", "SOCKS5": "socks"}
                # 未单独填端口时，全部套用 HTTP 端口
                master = ports.get("HTTP") or "80"
                for label, base in mapping.items():
                    port = ports.get(label) or master
                    _run(["gsettings", "set", "org.gnome.system.proxy", base, f"{host}:{port}"])
                    _run(["gsettings", "set", "org.gnome.system.proxy", base, "host", host])
                    _run(["gsettings", "set", "org.gnome.system.proxy", base, "port", port])
                self.proxy_status.setText(f"已应用（GNOME 代理 {mode}）")
            else:
                self.proxy_status.setText("gsettings 不可用，未应用系统代理")
        elif IS_WIN:
            # 修改注册表需管理员权限，这里仅提示
            self.proxy_status.setText("Windows 系统代理需管理员权限，已跳过（仅本地保存）")

    # ==================================================================
    # 个性化页
    # ==================================================================
    def _build_personalization_page(self):
        page, group, glay = self._page_scaffold("个性化")

        bg_group = QGroupBox("背景")
        blay = QVBoxLayout(bg_group)
        blay.setContentsMargins(10, 16, 10, 10)
        blay.setSpacing(6)
        self.bg_preview = QLabel()
        self.bg_preview.setFixedHeight(90)
        self.bg_preview.setAlignment(Qt.AlignCenter)
        self.bg_preview.setText("(无预览)")
        self.bg_preview.setObjectName("BGPanel")
        self.bg_preview.setScaledContents(False)
        blay.addWidget(self.bg_preview)

        self.bg_path = QLineEdit()
        self.bg_path.setReadOnly(True)
        blay.addLayout(FormRow("图片", self.bg_path))

        brows = QPushButton("选择壁纸…")
        brows.setFixedWidth(120)
        brows.clicked.connect(self._pick_wallpaper)
        blay.addWidget(brows, 0, Qt.AlignLeft)
        glay.addWidget(bg_group)

        color_group = QGroupBox("颜色 / 主题")
        clay = QVBoxLayout(color_group)
        clay.setContentsMargins(10, 16, 10, 10)
        clay.setSpacing(6)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["经典 Windows 98", "深色", "浅色", "紫罗兰"])
        clay.addLayout(FormRow("主题", self.theme_combo))

        self.accent_btn = QPushButton("🎨")
        self.accent_btn.setFixedWidth(40)
        self.accent_btn.setCursor(Qt.PointingHandCursor)
        self.accent_btn.setToolTip("点击选择强调色")
        self.accent_btn.setProperty("accent", QColor(0, 0, 128))
        self.accent_btn.setStyleSheet("background:#000080; color:#ffffff;")
        self.accent_btn.clicked.connect(self._pick_accent)
        clay.addLayout(FormRow("强调色", self.accent_btn))
        glay.addWidget(color_group)

        font_group = QGroupBox("字体")
        flay = QVBoxLayout(font_group)
        flay.setContentsMargins(10, 16, 10, 10)
        flay.setSpacing(6)
        self.font_combo = QComboBox()
        self.font_combo.setEditable(True)
        flay.addLayout(FormRow("字体", self.font_combo))

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 40)
        self.font_size.setValue(12)
        self.font_size.valueChanged.connect(self._apply_font)
        flay.addLayout(FormRow("字号", self.font_size))
        glay.addWidget(font_group)

        apply_btn = QPushButton("应用个性化设置")
        apply_btn.setFixedWidth(160)
        apply_btn.clicked.connect(self._apply_personalization)
        glay.addWidget(apply_btn, 0, Qt.AlignCenter)
        glay.addStretch()
        return page

    def _refresh_personalization(self):
        """预填字体、当前壁纸。"""
        self._load_fonts()
        self._load_current_wallpaper()

    def _load_fonts(self):
        self.font_combo.clear()
        fonts = []
        if IS_LINUX:
            rc, out = _run(["fc-list", ":", "family"])
            seen = set()
            for ln in (out.splitlines() if out else []):
                for fam in ln.split(","):
                    fam = fam.strip()
                    if fam and fam not in seen:
                        seen.add(fam)
                        fonts.append(fam)
        if not fonts:
            fonts = ["Sans Serif", "Serif", "Monospace", "Microsoft YaHei", "SimSun"]
        self.font_combo.addItems(fonts[:120])
        self.font_combo.setCurrentText(QFont().family())

    def _load_current_wallpaper(self):
        # 默认指向桌面应用自带壁纸（与 DesktopWidget 保持一致），仅作初始显示。
        # 也可先探测 DesktopWidget 当前使用的壁纸。
        path = self._probe_host_wallpaper()
        if not path:
            path = str(pathlib.Path(__file__).resolve().parent / "background.jpg")
        self._set_wallpaper_display(path if os.path.isfile(path) else "")

    def _probe_host_wallpaper(self):
        """向上查找宿主 DesktopWidget，若存在则读取其当前壁纸路径。"""
        w = self.parent()
        while w is not None:
            if hasattr(w, "main_widget") and hasattr(w.main_widget, "image_path"):
                p = getattr(w.main_widget, "image_path", "")
                return p if p else ""
            w = w.parent()
        return ""

    def _set_wallpaper_display(self, path: str):
        self.bg_path.setText(path)
        if path and os.path.isfile(path):
            pix = QPixmap(path)
            if not pix.isNull():
                self.bg_preview.setPixmap(pix.scaled(
                    self.bg_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.bg_preview.setText("")
                return
        self.bg_preview.setPixmap(QPixmap())
        self.bg_preview.setText("(无预览)")

    def _pick_wallpaper(self):
        start = "/usr/share/backgrounds" if IS_LINUX else os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self, "选择壁纸", start,
            "图片 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if path:
            self._set_wallpaper_display(path)

    def _pick_accent(self):
        color = QColorDialog.getColor(self.accent_btn.property("accent") or QColor(0, 0, 128),
                                      self, "选择强调色")
        if color.isValid():
            self.accent_btn.setProperty("accent", color)
            self.accent_btn.setStyleSheet(f"background:{color.name()};")
            self.accent_btn.setText("")

    def _apply_font(self, value):
        f = self.font()
        f.setPointSize(value)
        self.setFont(f)

    def _apply_personalization(self):
        """把个性化设置通过信号交给宿主 DesktopWidget 应用（壁纸→main_widget，强调色→TaskBar）。

        独立运行（未连接宿主）时，仅套用字体到本窗口自身。
        """
        # 壁纸：信号发射，由宿主应用到其 self.main_widget
        path = self.bg_path.text().strip()
        if path and os.path.isfile(path):
            self.wallpaperApplyRequested.emit(path)

        # 强调色：信号发射，由宿主应用到任务栏等
        accent = self.accent_btn.property("accent")
        if isinstance(accent, QColor) and accent.isValid():
            self.accentApplyRequested.emit(accent)

        # 字体：应用到设置面板自身（宿主界面字体可由宿主另行处理）
        f = QFont(self.font_combo.currentText() or QFont().family())
        f.setPointSize(self.font_size.value())
        self.setFont(f)
        QMessageBox.information(self, "个性化", "个性化设置已应用。")

    # ==================================================================
    # 应用页
    # ==================================================================
    def _build_apps_page(self):
        page, group, glay = self._page_scaffold("应用")
        lbl = QLabel(
            "· 已安装的应用\n· 默认应用\n· 启动项\n\n"
            "该面板为基本信息展示，可在主桌面中直接启动各内置应用。"
        )
        glay.addWidget(lbl)
        glay.addStretch()
        return page

    def _apply_style(self):
        """Windows 98 经典配色：灰底 + 3D 凸起/凹陷边框（跨平台字体回退）"""
        families = ", ".join(['"Microsoft YaHei"', '"Noto Sans CJK SC"', '"WenQuanYi Micro Hei"',
                              '"DejaVu Sans"', '"SimSun"'])
        self.setStyleSheet(f"""
            QWidget {{
                background: #ffffff;
                color: #000000;
                font-family: {families};
                font-size: 12px;
            }}
            /* 左侧导航：经典凹陷面板 */
            QFrame#Sidebar {{
                background: #ffffff;
                border: 1px solid #ffffff;
            }}
            
            /* 当前激活项：凹陷 + 深蓝文字 */
            QPushButton[active="true"] {{
                border-left: 3px solid #00aaff;
                background: #d4d0c8;
                color: #000080;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }}
            QLabel {{ background: transparent; }}
            /* 表单行标签：右对齐强调 */
            QLabel#FormLabel {{
                background: transparent;
                color: #000080;
                font-weight: bold;
            }}
            /* 等宽信息文本 */
            QLabel#Mono {{
                background: #d4d0c8;
                border: 1px inset #ffffff;
                border-color: #808080 #ffffff #ffffff #808080;
                padding: 4px 6px;
                font-family: {families};
            }}
            /* 壁纸预览面板 */
            QLabel#BGPanel {{
                background: #ffffff;
                color: #ffffff;
                border: 2px inset #ffffff;
                border-color: #808080 #ffffff #ffffff #808080;
            }}
            /* 输入框 / 下拉 / 列表：经典凹陷 */
            QLineEdit, QComboBox, QSpinBox, QListWidget {{
                background: #ffffff;
                color: #000000;
                border: 2px inset #ffffff;
                border-color: #808080 #ffffff #ffffff #808080;
                selection-background-color: #000080;
                selection-color: #ffffff;
            }}
            QListWidget::item:selected {{
                background: #000080;
                color: #ffffff;
            }}
            QComboBox QAbstractItemView {{
                background: #ffffff;
                color: #000000;
                selection-background-color: #000080;
                selection-color: #ffffff;
                border: 2px outset #ffffff;
                border-color: #ffffff #808080 #808080 #ffffff;
            }}
            QCheckBox {{
                background: transparent;
                spacing: 6px;
            }}
            /* 滚动区：透明背景（内容页可见） */
            QScrollArea, QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            /* 经典 Win98 滚动条 */
            QScrollBar:vertical {{
                background: #c0c0c0;
                width: 16px;
                border: 1px solid #808080;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: #c0c0c0;
                border: 2px outset #ffffff;
                border-color: #ffffff #808080 #808080 #ffffff;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{ background: #d4d0c8; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: #c0c0c0;
                border: 2px outset #ffffff;
                border-color: #ffffff #808080 #808080 #ffffff;
                height: 16px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: #c0c0c0;
            }}
            QScrollBar:horizontal {{
                background: #c0c0c0;
                height: 16px;
                border: 1px solid #808080;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: #c0c0c0;
                border: 2px outset #ffffff;
                border-color: #ffffff #808080 #808080 #ffffff;
                min-width: 24px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: #d4d0c8; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                background: #c0c0c0;
                border: 2px outset #ffffff;
                border-color: #ffffff #808080 #808080 #ffffff;
                width: 16px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: #c0c0c0;
            }}
            QGroupBox QGroupBox {{
                margin-top: 12px;
                font-weight: normal;
            }}
        """)


def create_settings_window(parent=None):
    """用 EMdiSubWindow 生成一个 Windows 98 复古风格设置窗口（返回后需调用 show()）。

    返回的窗口挂载 `_settings_content` 属性指向内部 SettingWidget，
    宿主可据此连接 personalize 信号。
    """
    win = EMdiSubWindow(parent, "设置",
                        allow_maxmin_buttons=True, allow_resize=True)
    win.resize(720, 480)
    content = SettingWidget()
    win.addWidget(content)
    win._settings_content = content
    return win


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Windows")
    w = create_settings_window()
    w.show()
    app.exec()
