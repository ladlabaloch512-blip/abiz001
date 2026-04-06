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
        self.resize(800, 500)
        self.setFixedSize(800, 500) # Prevent resizing to maintain card look

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
        card.setFixedSize(600, 350)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(20)

        # Header
        title = QLabel("🔒 SYSTEM LOCKED")
        title.setObjectName("HeaderTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        sub = QLabel("No valid license detected. To use this software, please purchase an active license and register your Device ID.")
        sub.setObjectName("SubHeader")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        card_layout.addWidget(sub)

        # Glowing UUID Display
        uuid_lbl = QLabel(self.hw_uuid)
        uuid_lbl.setObjectName("GlowingUUID")
        uuid_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(uuid_lbl)

        # Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        btn_copy = QPushButton("📋 Copy Device ID")
        btn_copy.setObjectName("CopyBtn")
        btn_copy.clicked.connect(self._copy_uuid)

        btn_buy = QPushButton("🛍️ Purchase Active License")
        btn_buy.setObjectName("WhatsAppBtn")
        btn_buy.clicked.connect(self._open_whatsapp)

        btn_layout.addWidget(btn_copy)
        btn_layout.addWidget(btn_buy)

        card_layout.addLayout(btn_layout)

        main_layout.addWidget(card)

    def _copy_uuid(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.hw_uuid)
        # Visual feedback could be added here (e.g. changing button text temporarily)

    def _open_whatsapp(self):
        if self.whatsapp_link:
            webbrowser.open(self.whatsapp_link)
