"""GPU 加速 HTML 窗口

基于 QWebEngineView 实现，通过环境变量 + Chromium flags + WebEngine Settings
三重确保 GPU 硬件加速渲染。

特性：
- QWebEngineView 基于 Chromium，默认启用 GPU 硬件加速渲染
- 支持加载本地 HTML 文件或直接设置 HTML 字符串
- QWebChannel 支持 Python ↔ JS 双向通信
- 禁用网页右键菜单
- GPU 状态自动检测
"""

from pack.libs.gui.QtPack import *
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
import sys
import os


class GpuWebWindow(QMainWindow):
    """使用 GPU 加速的 HTML 显示窗口"""
    
    def __init__(self, title: str = "GPU Web Window", html: str = "",
                 url: str = "", parent: QWidget = None):
        super().__init__(parent)
        self._ensure_gpu_acceleration()
        self.setWindowTitle(title)
        self.resize(1024, 720)

        # 中央控件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- GPU 加速的 Web 引擎 ----
        self.web_view = QWebEngineView()
        self.web_view.setMinimumSize(400, 300)
        # 显式设置 WebEngine 属性以启用 GPU
        page = self.web_view.page()
        settings = page.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        # 允许 JS 访问本地资源
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        layout.addWidget(self.web_view, 1)

        # ---- Python ↔ JS 双向通道 ----
        self._channel = QWebChannel()
        self._channel.registerObject("pyBridge", self)
        page.setWebChannel(self._channel)

        # ---- 状态栏显示 GPU 信息 ----
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._gpu_label = QLabel("GPU: 检测中...")
        self._status.addPermanentWidget(self._gpu_label)

        # 加载内容
        if url:
            self.load_url(url)
        elif html:
            self.set_html(html)
        else:
            self.set_html(self._default_html())

        # 检测 GPU 状态
        QTimer.singleShot(2000, self._check_gpu_status)

        # 禁用网页右键菜单
        page.action(QWebEnginePage.WebAction.Back).setVisible(False)
        # 注入 JS 禁用右键 + 禁用选中文本右键
        self._disable_context_menu_js = """
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            return false;
        });
        document.addEventListener('selectstart', function(e) {
            return false;
        });
        """
        page.runJavaScript(self._disable_context_menu_js)

    # ==================== 公共 API ====================

    def load_url(self, url: str):
        """加载远程或本地 URL"""
        if url.startswith("http://") or url.startswith("https://"):
            self.web_view.load(QUrl(url))
        else:
            path = os.path.abspath(url)
            self.web_view.load(QUrl.fromLocalFile(path))

    def set_html(self, html: str, base_url: str = ""):
        """直接设置 HTML 内容"""
        if base_url:
            self.web_view.setHtml(html, QUrl(base_url))
        else:
            self.web_view.setHtml(html)
        # setHtml 重新加载页面后会重置 JS，重新注入右键禁用
        QTimer.singleShot(200, lambda: self.web_view.page().runJavaScript(
            self._disable_context_menu_js))

    def run_js(self, code: str, callback=None):
        """执行 JavaScript 代码，可选回调获取返回值"""
        if callback:
            self.web_view.page().runJavaScript(code, callback)
        else:
            self.web_view.page().runJavaScript(code)

    # ==================== GPU 加速 ====================

    @staticmethod
    def _ensure_gpu_acceleration():
        """在 QApplication 创建前/后确保 GPU 加速开启"""
        # 禁用软件渲染回退
        os.environ["QT_QUICK_BACKEND"] = ""          # 不使用 QtQuick 软件渲染
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
            "--enable-gpu-rasterization "
            "--enable-zero-copy "
            "--ignore-gpu-blocklist "
            "--enable-native-gpu-memory-buffers "
            "--enable-accelerated-video-decode "
        )
        # 确保 ANGLE 后端（Windows 上 DX11）
        if sys.platform == "win32":
            if "QT_OPENGL" not in os.environ:
                os.environ["QT_OPENGL"] = "angle"
        # 如果已有 QApplication 实例，设置其属性
        app = QApplication.instance()
        if app:
            app.setAttribute(Qt.ApplicationAttribute.AA_UseOpenGLES, False)

    def _check_gpu_status(self):
        """检测 GPU 加速实际状态"""
        js = """
        (function() {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            if (!gl) return 'WebGL 不可用';
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (!debugInfo) return 'WebGL (无调试信息)';
            const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            return renderer + ' | ' + vendor;
        })();
        """
        self.web_view.page().runJavaScript(js, self._on_gpu_result)

    def _on_gpu_result(self, result):
        if result and "不可用" not in result:
            self._gpu_label.setText(f"🚀 GPU: {result}")
            self._gpu_label.setStyleSheet("color: #00c853;")
        else:
            self._gpu_label.setText("⚠️ GPU 加速未启用（软件渲染）")
            self._gpu_label.setStyleSheet("color: #ff9800;")

    # ==================== 禁用右键菜单 ====================

    def contextMenuEvent(self, event):
        """完全禁用窗口级别右键菜单"""
        event.ignore()

    # ==================== QWebChannel 暴露给 JS 的方法 ====================

    pythonVersionChanged = pyqtSignal()

    @pyqtProperty(str, notify=pythonVersionChanged)
    def pythonVersion(self):
        return sys.version

    @pythonVersion.setter
    def pythonVersion(self, val):
        pass  # 只读，忽略写入

    @pyqtSlot(str)
    def js_log(self, message: str):
        """JS 端调用: pyBridge.js_log('hello')"""
        print(f"[JS] {message}")

    @pyqtSlot(str, result=str)
    def echo(self, text: str) -> str:
        """JS 端调用: pyBridge.echo('hello', (r) => console.log(r))"""
        return f"Python 收到: {text}"

    # ==================== 默认 HTML ====================

    @staticmethod
    def _default_html() -> str:
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GPU 加速窗口</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    background: #1a1a2e;
    color: #eee;
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh; overflow: hidden;
  }
  canvas { display: block; }
  .info {
    position: fixed; top: 16px; left: 16px;
    font-size: 13px; color: #888; pointer-events: none;
  }
</style>
</head>
<body>
<div class="info" id="info">GPU 加速 WebGL 演示</div>
<canvas id="glCanvas"></canvas>

<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
// ---- 连接 Python 后端 ----
var pyBridge = null;
new QWebChannel(qt.webChannelTransport, function(channel) {
    pyBridge = channel.objects.pyBridge;
    pyBridge.js_log("前端已连接 Python 后端");
});

// ---- WebGL GPU 粒子动画 ----
const canvas = document.getElementById('glCanvas');
const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  gl.viewport(0, 0, canvas.width, canvas.height);
}
window.addEventListener('resize', resize);
resize();

// 顶点 & 片元着色器
const vs = gl.createShader(gl.VERTEX_SHADER);
gl.shaderSource(vs, `#version 300 es
  in vec2 a_pos;
  uniform vec2 u_resolution;
  uniform float u_pointSize;
  void main() {
    vec2 zeroToOne = a_pos / u_resolution;
    vec2 clipSpace = zeroToOne * 2.0 - 1.0;
    gl_Position = vec4(clipSpace * vec2(1,-1), 0, 1);
    gl_PointSize = u_pointSize;
  }`);
gl.compileShader(vs);

const fs = gl.createShader(gl.FRAGMENT_SHADER);
gl.shaderSource(fs, `#version 300 es
  precision highp float;
  out vec4 outColor;
  uniform vec4 u_color;
  void main() {
    float d = distance(gl_PointCoord, vec2(0.5));
    if (d > 0.5) discard;
    float alpha = smoothstep(0.5, 0.05, d);
    outColor = vec4(u_color.rgb, u_color.a * alpha);
  }`);
gl.compileShader(fs);

const prog = gl.createProgram();
gl.attachShader(prog, vs);
gl.attachShader(prog, fs);
gl.linkProgram(prog);
gl.useProgram(prog);

const aPos = gl.getAttribLocation(prog, 'a_pos');
const uRes = gl.getUniformLocation(prog, 'u_resolution');
const uPSize = gl.getUniformLocation(prog, 'u_pointSize');
const uColor = gl.getUniformLocation(prog, 'u_color');

gl.enable(gl.BLEND);
gl.blendFunc(gl.SRC_ALPHA, gl.ONE);

// 粒子数据
const N = 200;
const pos = new Float32Array(N * 2);
const vel = new Float32Array(N * 2);
for (let i = 0; i < N; i++) {
  pos[i*2] = Math.random() * canvas.width;
  pos[i*2+1] = Math.random() * canvas.height;
  vel[i*2] = (Math.random() - 0.5) * 2;
  vel[i*2+1] = (Math.random() - 0.5) * 2;
}

const buf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buf);
gl.bufferData(gl.ARRAY_BUFFER, pos, gl.DYNAMIC_DRAW);
gl.enableVertexAttribArray(aPos);
gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

let hue = 0;
function frame() {
  for (let i = 0; i < N; i++) {
    pos[i*2] += vel[i*2];
    pos[i*2+1] += vel[i*2+1];
    if (pos[i*2] < 0 || pos[i*2] > canvas.width)  vel[i*2] *= -1;
    if (pos[i*2+1] < 0 || pos[i*2+1] > canvas.height) vel[i*2+1] *= -1;
  }
  gl.bufferSubData(gl.ARRAY_BUFFER, 0, pos);
  gl.uniform2f(uRes, canvas.width, canvas.height);
  gl.uniform1f(uPSize, 6.0);
  hue = (hue + 0.3) % 360;
  const c = hslToRgb(hue / 360, 0.8, 0.6);
  gl.uniform4f(uColor, c[0], c[1], c[2], 0.7);
  gl.clear(gl.COLOR_BUFFER_BIT);
  gl.drawArrays(gl.POINTS, 0, N);
  requestAnimationFrame(frame);
}

function hslToRgb(h, s, l) {
  let r, g, b;
  if (s === 0) { r = g = b = l; }
  else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1; if (t > 1) t -= 1;
      if (t < 1/6) return p + (q-p)*6*t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q-p)*(2/3-t)*6;
      return p;
    };
    const q = l < 0.5 ? l*(1+s) : l+s-l*s;
    const p = 2*l - q;
    r = hue2rgb(p,q,h+1/3); g = hue2rgb(p,q,h); b = hue2rgb(p,q,h-1/3);
  }
  return [r, g, b];
}

frame();
</script>
</body>
</html>"""


# ==================== 便捷启动 ====================

def open_gpu_window(title: str = "GPU Web Window", html: str = "",
                    url: str = "") -> GpuWebWindow:
    """快速打开一个 GPU 加速的 HTML 窗口（非模态）"""
    window = GpuWebWindow(title=title, html=html, url=url)
    window.show()
    return window


