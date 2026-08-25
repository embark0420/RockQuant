"""GPU 加速 HTML 显示模块

提供 GPU 加速的 Web 窗口，支持 HTML 渲染、JS 交互和 Python ↔ JS 双向通信。

用法:
    from pack.libs.module.html import GpuWebWindow, open_gpu_window

    win = GpuWebWindow(title="我的窗口", html="<h1>Hello</h1>")
    win.show()

    # 或使用便捷函数
    open_gpu_window(url="https://example.com")
"""

from pack.libs.html.gpu_window import GpuWebWindow, open_gpu_window

__all__ = ["GpuWebWindow", "open_gpu_window"]
