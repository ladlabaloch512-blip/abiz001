import sys
import os
from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, QCoreApplication
from PyQt6.QtGui import QPixmap, QColor, QFont

class LoadingScreen(QSplashScreen):
    """
    Premium Splash Screen with Progress Bar and Glass-morphism Aesthetics.
    """
    def __init__(self, bg_image_path=None):
        super().__init__()

        # Transparent background for custom styling
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resize(600, 350)
        self.setFixedSize(600, 350)

        # Central widget for the layout
        self.central_widget = QWidget(self)
        self.central_widget.resize(600, 350)
        self.central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(11, 14, 17, 0.95), stop:1 rgba(21, 25, 30, 0.95));
                border-radius: 15px;
                border: 1px solid rgba(0, 229, 255, 0.2);
            }
        """)

        layout = QVBoxLayout(self.central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Title
        self.title_label = QLabel("🚀 SYSTEM INITIALIZATION")
        self.title_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                font-size: 26px;
                font-weight: 900;
                color: #FFFFFF;
                letter-spacing: 2px;
                background: transparent;
                border: none;
            }
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Subtitle
        self.subtitle_label = QLabel("Loading Modules & Verifying Security...")
        self.subtitle_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #A0AABF;
                background: transparent;
                border: none;
            }
        """)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle_label)

        # Status text below subtitle
        self.status_label = QLabel("Starting...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-family: 'Consolas', monospace;
                font-size: 12px;
                color: #00E5FF;
                background: transparent;
                border: none;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #1E1E1E;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C6FF, stop:1 #0072FF);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Bottom padding
        layout.addSpacing(10)

        # Center the splash screen on the primary screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        # Force UI update so it doesn't freeze
        QCoreApplication.processEvents()
