# RockQuant

> A lightweight GUI Desktop Environment built with PyQt5 for Headless Systems.

## 🛠️ How it works

RockQuant operates by creating a virtual display using `Xvfb :0 -screen 0 1280x800x24 &` and `x11vnc -display :0 -forever &`. It renders the PyQt5 GUI onto this virtual display and streams the output via the VNC / X11 protocols.

> **Backstory:** I bought a Rock S0 Pi which has no video output port and no dedicated graphics module, so I decided to build a GUI from scratch just to see it run.

## 🚀 Features

- **Handwritten Window Manager**: Full support for drag, edge resizing, and maximize/restore animations.
- **Built-in Web Browser**: Can fully render modern web pages (based on QtWebEngine).
- **System Monitor**: Real-time CPU / Memory / Disk monitoring by parsing `/proc` files.
- **Taskbar System**: Multi-window management with taskbar switching and closing animations.
- **Pure GPU Rendering**: Uses OpenGL for transparent/rounded corners, avoiding memory explosion caused by CPU image capturing.

## ⚠️ Performance & Limitations

- On the ROCK S0 Pi, the refresh rate caps at **15 FPS** due to the extremely low CPU performance.
- **Final Test:** It runs on most Linux Headless systems.
- **Current Bottleneck:** It cannot output via a physical video interface; currently, it relies solely on VNC / X11 protocols to display.

## 📦 Environment

- **Hardware**: Rock S0 Pi (aarch64, 1GB RAM)
- **Software**: Armbian (Headless) / Python 3 / PyQt5 / PyOpenGL

## 💡 Why did I make this?

A high school student just tinkering around. While others hustle with hardware, I hustle to give hardware a "fake screen". The code is messy and brute-forced; it works, that's all I asked for. Please be gentle with the criticism.

## 📄 License

MIT
