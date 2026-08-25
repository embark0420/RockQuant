"""
RockQuant - Simple Test Widget
================================
A minimal example to test the EMdiSubWindow embedding.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class MainWidget(QWidget):
    """Simple test widget that gets embedded into EMdiSubWindow."""

    # Window configuration
    WINDOW_TITLE = "Test App"
    WINDOW_SIZE = (400, 300)
    WINDOW_RESIZABLE = True
    WINDOW_MAXMIN = True

    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Hello, RockQuant!")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4ade80;")
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel("This window is successfully embedded into the Desktop Window Manager.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; color: #94a3b8;")
        layout.addWidget(desc_label)

        layout.addStretch()