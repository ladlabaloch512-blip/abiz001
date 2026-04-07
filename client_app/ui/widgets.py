import psutil
import webbrowser
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QHBoxLayout, QApplication, QMainWindow
from PyQt6.QtCore import QTimer, Qt

class HardwareMonitorWidget(QFrame):
    """
    Real-time sidebar widget using psutil to track CPU load, RAM usage,
    and provide dynamic launch recommendations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HardwareMonitor")
        self.setStyleSheet("""
            QFrame#HardwareMonitor {
                background-color: #15191E;
                border-radius: 10px;
                border: 1px solid #2D3139;
            }
            QLabel {
                color: #A0AABF;
                font-size: 13px;
                padding: 2px;
            }
            QLabel#Title {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                padding-bottom: 5px;
            }
            QLabel#Highlight {
                color: #6366F1;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("System Monitor")
        title.setObjectName("Title")
        layout.addWidget(title)

        self.lbl_cpu = QLabel("CPU Load: 0%")
        self.lbl_ram_used = QLabel("App RAM: 0 MB")
        self.lbl_ram_free = QLabel("Free RAM: 0 GB")
        self.lbl_recommendation = QLabel("Stable Launch Limit: 0")
        self.lbl_recommendation.setObjectName("Highlight")

        layout.addWidget(self.lbl_cpu)
        layout.addWidget(self.lbl_ram_used)
        layout.addWidget(self.lbl_ram_free)
        layout.addWidget(self.lbl_recommendation)

        # Setup Timer for updates (every 2 seconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)
        self.update_stats()

    def update_stats(self):
        try:
            # CPU
            cpu_usage = psutil.cpu_percent(interval=None)
            self.lbl_cpu.setText(f"CPU Load: {cpu_usage}%")

            # RAM
            mem = psutil.virtual_memory()
            free_ram_gb = mem.available / (1024 ** 3)

            # App/Chromium RAM Estimation
            chrome_ram_mb = 0
            for proc in psutil.process_iter(['name', 'memory_info']):
                try:
                    name = proc.info['name'].lower() if proc.info['name'] else ''
                    if 'chrome' in name or 'chromium' in name or 'chromedriver' in name:
                        chrome_ram_mb += proc.info['memory_info'].rss / (1024 ** 2)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            self.lbl_ram_used.setText(f"App RAM: {int(chrome_ram_mb)} MB")
            self.lbl_ram_free.setText(f"Free RAM: {free_ram_gb:.1f} GB")

            # 600MB per browser heuristic
            safe_limit = int((mem.available / (1024 ** 2)) / 600)
            self.lbl_recommendation.setText(f"Stable Launch Limit: {safe_limit}")

        except Exception as e:
            print(f"HW Monitor Error: {e}")

class LockedScreen(QMainWindow):
    """
    Industrial-Grade 'Locked Screen' Redesign.
    Displays when a user does not have a valid license.
    """
    def __init__(self, hw_uuid: str, whatsapp_link: str):
        super().__init__()
        self.hw_uuid = hw_uuid
        self.whatsapp_link = whatsapp_link
        self.setWindowTitle("System Locked - License Required")
        self.resize(850, 550)
        self.setFixedSize(850, 550) # Prevent resizing to maintain card look

        # Deep gradient background (#121212 to #1e1e1e)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #121212, stop:1 #1e1e1e);
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#HeaderTitle {
                font-size: 28px;
                font-weight: 900;
                color: #FFFFFF;
                letter-spacing: 1px;
            }
            QLabel#SubHeader {
                font-size: 15px;
                color: #FFFFFF;
            }
            QFrame#GlassCard {
                background-color: rgba(20, 20, 20, 0.9);
                border-radius: 16px;
                border: 1px solid rgba(0, 229, 255, 0.3); /* Neon Blue edge */
            }
            QLabel#GlowingUUID {
                background-color: #0A0A0A;
                color: #00E5FF; /* Neon Blue */
                font-family: 'Consolas', monospace;
                font-size: 22px;
                font-weight: bold;
                padding: 18px;
                border-radius: 10px;
                border: 2px solid #00E5FF;
            }
            QPushButton#CopyBtn {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 10px;
                padding: 14px 20px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#CopyBtn:hover {
                background-color: #2D2D2D;
                border: 1px solid #00E5FF;
                color: #00E5FF;
                margin-top: -2px;
                margin-bottom: 2px;
            }
            QPushButton#WhatsAppBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C6FF, stop:1 #0072FF); /* High-Gloss Cyan/Blue Gradient */
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 14px 24px;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 0.5px;
            }
            QPushButton#WhatsAppBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E5FF, stop:1 #0099FF);
                margin-top: -2px;
                margin-bottom: 2px;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Center the card in the main window
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # The Glass Card
        card = QFrame()
        card.setObjectName("GlassCard")
        card.setFixedSize(650, 380)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(25)

        # Header
        title = QLabel("🔒 HARDWARE LOCK ACTIVATED")
        title.setObjectName("HeaderTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        sub = QLabel("This software is secured to this specific device. To proceed, please purchase an activation key and register your Hardware Device ID below.")
        sub.setObjectName("SubHeader")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        card_layout.addWidget(sub)

        # Glowing UUID Display
        uuid_lbl = QLabel(self.hw_uuid)
        uuid_lbl.setObjectName("GlowingUUID")
        uuid_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        uuid_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        card_layout.addWidget(uuid_lbl)

        # Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.btn_copy = QPushButton("📋 Copy Device ID")
        self.btn_copy.setObjectName("CopyBtn")
        self.btn_copy.clicked.connect(self._copy_uuid)

        self.btn_buy = QPushButton("🛍️ Purchase Activation Key")
        self.btn_buy.setObjectName("WhatsAppBtn")
        self.btn_buy.clicked.connect(self._open_whatsapp)

        btn_layout.addWidget(self.btn_copy)
        btn_layout.addWidget(self.btn_buy)

        card_layout.addLayout(btn_layout)

        main_layout.addWidget(card)

    def _copy_uuid(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.hw_uuid)

        # Visual feedback: Change text temporarily and show checkmark
        original_text = self.btn_copy.text()
        self.btn_copy.setText("✅ Copied!")
        self.btn_copy.setStyleSheet("""
            QPushButton#CopyBtn {
                background-color: #2D2D2D;
                border: 1px solid #00E5FF;
                color: #00E5FF;
            }
        """)

        # Reset after 2 seconds
        QTimer.singleShot(2000, lambda: self._reset_copy_btn(original_text))

    def _reset_copy_btn(self, original_text):
        self.btn_copy.setText(original_text)
        self.btn_copy.setStyleSheet("") # Revert to default stylesheet

    def _open_whatsapp(self):
        if self.whatsapp_link:
            webbrowser.open(self.whatsapp_link)
