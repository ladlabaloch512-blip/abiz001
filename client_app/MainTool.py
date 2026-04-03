import sys
import os
import webbrowser
import uuid

# Add parent directory to path so we can import shared_logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
                             QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QFormLayout, QMessageBox, QCheckBox,
                             QTextEdit, QFileDialog, QListWidget, QListWidgetItem,
                             QComboBox, QMenu, QInputDialog, QGraphicsOpacityEffect)
import shutil
import zipfile
import json
from PyQt6.QtCore import Qt, QThreadPool, pyqtSlot, QRunnable, QObject, pyqtSignal, QPropertyAnimation, QTimer
from shared_logic.security import verify_license, get_hardware_uuid
from shared_logic.config import BUY_LINK
import requests # For "What is my IP" check if needed or just redirect
import psutil

import requests # For proxy health check

# Import Module 2, 3 and Multi-Account Engine Logic
from client_app.database import init_db, get_all_profiles, add_profile, delete_profile, get_next_sequential_id, get_profile_stats, bulk_insert_profiles, update_profile_group, update_profile_proxy, get_all_groups, add_group, delete_group
from client_app.automation_logic import BrowserLauncherWorker, MarketplaceTaskWorker, AccountMonitorWorker, ACTIVE_DRIVERS, stop_all_selected

class ProxyCheckSignals(QObject):
    result = pyqtSignal(int, bool) # row_idx, is_alive

class ProxyCheckWorker(QRunnable):
    def __init__(self, row_idx, proxy_str):
        super().__init__()
        self.row_idx = row_idx
        self.proxy_str = proxy_str
        self.signals = ProxyCheckSignals()

    @pyqtSlot()
    def run(self):
        try:
            proxies = None
            if self.proxy_str:
                # Format: IP:PORT:USER:PASS -> http://USER:PASS@IP:PORT
                parts = self.proxy_str.split(':')
                if len(parts) == 4:
                    proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                    proxies = {"http": proxy_url, "https": proxy_url}
                elif len(parts) == 2:
                    proxy_url = f"http://{parts[0]}:{parts[1]}"
                    proxies = {"http": proxy_url, "https": proxy_url}

            if proxies:
                response = requests.get("https://api.ipify.org", proxies=proxies, timeout=5)
                is_alive = response.status_code == 200
            else:
                # Direct IP is always considered alive for UI purposes
                is_alive = True
        except Exception:
            is_alive = False

        self.signals.result.emit(self.row_idx, is_alive)

class AddProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Profile")
        self.setFixedSize(400, 250)

        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. John Doe - Plumbing")

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("Optional (IP:PORT or IP:PORT:USER:PASS)")

        self.ua_input = QLineEdit()
        self.ua_input.setPlaceholderText("Optional Custom User-Agent")

        layout.addRow("Profile Name:", self.name_input)
        layout.addRow("Proxy:", self.proxy_input)
        layout.addRow("User-Agent:", self.ua_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Profile")
        self.save_btn.setObjectName("PrimaryAction")
        self.save_btn.setStyleSheet("background-color: #6366F1; color: white; border-radius: 5px; padding: 10px;")
        self.save_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #4B5563; color: white; border-radius: 5px; padding: 10px;")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'proxy': self.proxy_input.text().strip(),
            'ua': self.ua_input.text().strip()
        }

class MainClientApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Ensure database schema is migrated/initialized before launching the UI
        init_db()

        self.threadpool = QThreadPool()
        # Allow up to 500 simultaneous browser launches to leverage high-end hardware for 100+ accounts
        self.threadpool.setMaxThreadCount(500)
        print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        self.load_stylesheet()
        self.init_ui()
        self.check_license_on_startup()

    def load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(__file__), 'styles.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r') as f:
                self.setStyleSheet(f.read())

    def init_ui(self):
        self.setWindowTitle('FB Multi-Account Manager - Client Tool')
        self.resize(1100, 750)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setup_sidebar()

        self.content_area = QWidget()
        self.content_area.setObjectName("ContentArea")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 30)

        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)

        self.main_layout.addWidget(self.sidebar_widget)
        self.main_layout.addWidget(self.content_area, 1)

        # Initialize Screens
        self.locked_screen = QWidget()
        self.account_manager_screen = QWidget()
        self.bulk_listing_screen = QWidget()
        self.lead_router_screen = QWidget()
        self.settings_screen = QWidget()

        self.stacked_widget.addWidget(self.locked_screen)
        self.stacked_widget.addWidget(self.account_manager_screen)
        self.stacked_widget.addWidget(self.bulk_listing_screen)
        self.stacked_widget.addWidget(self.lead_router_screen)
        self.stacked_widget.addWidget(self.settings_screen)

        # Build standard placeholder for Settings
        ph_layout = QVBoxLayout(self.settings_screen)
        ph_label = QLabel("Settings Module under construction in later steps...")
        ph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_label.setStyleSheet("font-size: 24px; color: #A0AABF;")
        ph_layout.addWidget(ph_label)

    def setup_sidebar(self):
        self.sidebar_widget = QFrame()
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setFixedWidth(250)

        layout = QVBoxLayout(self.sidebar_widget)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(5)

        logo_label = QLabel("FB AutoPilot\nPRO")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(logo_label)

        self.nav_buttons = []

        nav_items = [
            ("👤 Account Manager", lambda: self.stacked_widget.setCurrentWidget(self.account_manager_screen)),
            ("💬 Lead Router", lambda: self.stacked_widget.setCurrentWidget(self.lead_router_screen)),
            ("📦 Bulk Listing Tool", lambda: self.stacked_widget.setCurrentWidget(self.bulk_listing_screen)),
            ("⚙️ Settings", lambda: self.stacked_widget.setCurrentWidget(self.settings_screen))
        ]

        for text, callback in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(self.nav_button_clicked)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # Hardware Monitor Widget
        self.hw_monitor = QFrame()
        self.hw_monitor.setStyleSheet("background-color: #1E232B; border-radius: 8px; border: 1px solid #2D3139; padding: 10px;")
        hw_layout = QVBoxLayout(self.hw_monitor)

        hw_title = QLabel("Hardware Monitor")
        hw_title.setStyleSheet("font-weight: bold; color: #A0AABF;")
        hw_layout.addWidget(hw_title)

        self.hw_stats_label = QLabel("CPU: --%\nRAM: --/-- GB")
        self.hw_stats_label.setStyleSheet("color: white; font-size: 12px;")
        hw_layout.addWidget(self.hw_stats_label)

        self.ai_rec_label = QLabel("Max Profiles: --")
        self.ai_rec_label.setStyleSheet("color: #10B981; font-weight: bold; font-size: 12px; margin-top: 5px;")
        hw_layout.addWidget(self.ai_rec_label)

        layout.addWidget(self.hw_monitor)

        # Update Timer for Hardware Monitor
        self.hw_timer = QTimer(self)
        self.hw_timer.timeout.connect(self.update_hardware_stats)
        self.hw_timer.start(2000) # Update every 2 seconds
        self.update_hardware_stats() # Initial call

        self.sidebar_widget.hide()

    def update_hardware_stats(self):
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            total_ram_gb = mem.total / (1024 ** 3)
            free_ram_gb = mem.available / (1024 ** 3)

            # Estimate RAM used specifically by Chromium instances
            chrome_ram_mb = 0
            for proc in psutil.process_iter(['name', 'memory_info']):
                try:
                    # Looking for chrome.exe or chromedriver
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        chrome_ram_mb += proc.info['memory_info'].rss / (1024 ** 2)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            chrome_ram_gb = chrome_ram_mb / 1024

            # Simple calculation: 600MB (~0.6GB) per Chromium profile
            max_profiles = int((mem.available / (1024 ** 2)) / 600)

            self.hw_stats_label.setText(f"CPU Load: {cpu_usage}%\nChrome Mem: {chrome_ram_gb:.1f} GB\nFree Mem: {free_ram_gb:.1f}/{total_ram_gb:.1f} GB")

            active_count = len(ACTIVE_DRIVERS)
            self.ai_rec_label.setText(f"Active Browsers: {active_count}\nMax Recommended: {max_profiles}")
        except Exception as e:
            self.hw_stats_label.setText("Hardware data unavailable")

    def nav_button_clicked(self):
        sender = self.sender()
        for btn in self.nav_buttons:
            if btn != sender:
                btn.setChecked(False)
        sender.setChecked(True)

    def check_license_on_startup(self):
        license_path = os.path.join(os.path.dirname(__file__), 'license.dat')

        is_valid, message = verify_license(license_path)
        if is_valid:
            self.sidebar_widget.show()
            if self.nav_buttons:
                self.nav_buttons[0].setChecked(True)
            self.build_account_manager()
            self.build_bulk_listing()
            self.build_lead_router()
            self.stacked_widget.setCurrentWidget(self.account_manager_screen)
        else:
            self.sidebar_widget.hide()
            self.build_locked_screen(message)
            self.stacked_widget.setCurrentWidget(self.locked_screen)

    def build_locked_screen(self, error_message):
        layout = QVBoxLayout(self.locked_screen)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedSize(500, 400)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        title_label = QLabel("Access Restricted")
        title_label.setObjectName("HeaderTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #EF4444;")

        status_label = QLabel(f"Status: {error_message}")
        status_label.setObjectName("SubHeader")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_label = QLabel("To activate this software, please send your Hardware UUID\nto the developer to generate a valid license.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #A0AABF; margin-top: 10px; margin-bottom: 10px;")

        uuid_box = QLineEdit()
        uuid_box.setText(get_hardware_uuid())
        uuid_box.setReadOnly(True)
        uuid_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buy_button = QPushButton("📲 Buy License via WhatsApp")
        buy_button.setObjectName("WhatsAppBtn")
        buy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        buy_button.clicked.connect(self.open_buy_link)

        card_layout.addWidget(title_label)
        card_layout.addWidget(status_label)
        card_layout.addWidget(info_label)
        card_layout.addWidget(uuid_box)
        card_layout.addStretch()
        card_layout.addWidget(buy_button)

        layout.addWidget(card)

    def build_account_manager(self):
        # Clear existing layout if rebuilding
        if self.account_manager_screen.layout():
            QWidget().setLayout(self.account_manager_screen.layout())

        main_layout = QHBoxLayout(self.account_manager_screen)

        # 1. Profile Grouping System (The Sidebar)
        group_panel = QFrame()
        group_panel.setObjectName("Card")
        group_panel.setFixedWidth(200)
        group_layout = QVBoxLayout(group_panel)

        group_title = QLabel("Groups")
        group_title.setObjectName("HeaderTitle")
        group_layout.addWidget(group_title)

        self.group_list_widget = QListWidget()
        self.group_list_widget.setStyleSheet("background-color: #1E232B; color: white; border: none; border-radius: 6px;")
        self.group_list_widget.itemClicked.connect(self.on_group_selected)
        group_layout.addWidget(self.group_list_widget)

        group_btn_layout = QHBoxLayout()
        add_group_btn = QPushButton("+ New Group")
        add_group_btn.setStyleSheet("background-color: #6366F1; color: white; padding: 5px; border-radius: 4px;")
        add_group_btn.clicked.connect(self.add_new_group)

        del_group_btn = QPushButton("🗑️")
        del_group_btn.setStyleSheet("background-color: #EF4444; color: white; padding: 5px; border-radius: 4px;")
        del_group_btn.clicked.connect(self.delete_selected_group)

        group_btn_layout.addWidget(add_group_btn)
        group_btn_layout.addWidget(del_group_btn)
        group_layout.addLayout(group_btn_layout)

        main_layout.addWidget(group_panel)

        # 2. Main Account Table Area
        right_panel = QWidget()
        layout = QVBoxLayout(right_panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Account Manager")
        title_label.setObjectName("HeaderTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # The Elite 4-Menu Ribbon
        toolbar_panel = QFrame()
        toolbar_panel.setStyleSheet("background-color: #1E232B; border-radius: 8px; border: 1px solid #2D3139;")
        toolbar_layout = QHBoxLayout(toolbar_panel)
        toolbar_layout.setContentsMargins(10, 10, 10, 10)
        toolbar_layout.setSpacing(15)

        # 1. Bulk Actions Menu
        bulk_ops_btn = QPushButton("🚀 Bulk Actions ▾")
        bulk_ops_btn.setProperty("class", "LaunchBtn")
        bulk_ops_menu = QMenu(bulk_ops_btn)

        act_launch_fb = bulk_ops_menu.addAction("🚀 Launch FB Home")
        act_launch_fb.triggered.connect(lambda: self.launch_selected_profiles("Facebook Login & Home"))

        act_launch_man = bulk_ops_menu.addAction("🕸️ Launch Manual (Blank Tab)")
        act_launch_man.triggered.connect(lambda: self.launch_selected_profiles("Manual (Blank Tab)"))

        act_launch_custom = bulk_ops_menu.addAction("🔗 Custom URL")
        act_launch_custom.triggered.connect(lambda: self.launch_selected_profiles("Custom URL"))

        bulk_ops_menu.addSeparator()

        act_login = bulk_ops_menu.addAction("🔑 Auto-Login Session")
        act_login.triggered.connect(self.check_selected_profiles_status)

        act_stop = bulk_ops_menu.addAction("🛑 Bulk Stop Selected")
        act_stop.triggered.connect(self.stop_selected_profiles)

        bulk_ops_btn.setMenu(bulk_ops_menu)
        toolbar_layout.addWidget(bulk_ops_btn)

        # 2. Import/Export Menu
        io_btn = QPushButton("📂 Import / Export ▾")
        io_btn.setProperty("class", "PrimaryAction")
        io_menu = QMenu(io_btn)

        act_imp_txt = io_menu.addAction("📄 TXT Import")
        act_imp_txt.triggered.connect(self.import_profiles_from_txt)

        act_imp_cook_fldr = io_menu.addAction("📁 Folder Cookie Import")
        act_imp_cook_fldr.triggered.connect(self.import_via_cookies)

        io_menu.addSeparator()

        act_export = io_menu.addAction("📤 Backup Profiles (Export ZIP)")
        act_export.triggered.connect(self.execute_bulk_export)

        act_import_backup = io_menu.addAction("📥 Restore Backup (Import ZIP)")
        act_import_backup.triggered.connect(self.execute_import_backup)

        io_btn.setMenu(io_menu)
        toolbar_layout.addWidget(io_btn)

        # 3. Settings & Wipe Menu
        maint_btn = QPushButton("⚙️ Settings & Wipe ▾")
        maint_btn.setProperty("class", "SecondaryAction")
        maint_menu = QMenu(maint_btn)

        act_add_prof = maint_menu.addAction("➕ Add Single Profile")
        act_add_prof.triggered.connect(self.open_add_profile_dialog)

        act_bulk_create = maint_menu.addAction("🔢 Bulk Empty Create")
        act_bulk_create.triggered.connect(self.bulk_empty_create)

        maint_menu.addSeparator()

        act_upd_proxy = maint_menu.addAction("🔄 Proxy Update")
        act_upd_proxy.triggered.connect(self.execute_bulk_proxy_update)

        act_wipe_cache = maint_menu.addAction("🧹 Clear Cache")
        act_wipe_cache.triggered.connect(self.execute_disk_cleanup)

        maint_menu.addSeparator()

        act_del = maint_menu.addAction("🗑️ Bulk Delete (Physical Wipe)")
        act_del.triggered.connect(self.execute_bulk_delete)

        maint_btn.setMenu(maint_menu)
        toolbar_layout.addWidget(maint_btn)

        # 4. Groups Control Menu
        groups_btn = QPushButton("👥 Groups Control ▾")
        groups_btn.setProperty("class", "SecondaryAction")
        groups_menu = QMenu(groups_btn)

        act_add_grp = groups_menu.addAction("➕ Create Group")
        act_add_grp.triggered.connect(self.add_new_group)

        act_del_grp = groups_menu.addAction("🗑️ Delete Group")
        act_del_grp.triggered.connect(self.delete_selected_group)

        groups_menu.addSeparator()

        act_move_grp = groups_menu.addAction("📂 Move IDs to Group")
        act_move_grp.triggered.connect(self.execute_bulk_group_update)

        groups_btn.setMenu(groups_menu)
        toolbar_layout.addWidget(groups_btn)

        toolbar_layout.addStretch()

        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.setStyleSheet("color: white; padding: 5px 10px; font-weight: bold;")
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_table_accounts)
        toolbar_layout.addWidget(self.select_all_checkbox)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Profiles...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.filter_table)
        toolbar_layout.addWidget(self.search_input)

        layout.addWidget(toolbar_panel)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "Profile Name", "Proxy", "Last Active", "Status", "⚙️ Manage"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Checkbox col
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Profile Name Stretch
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Proxy Stretch
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Manage col

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)

        layout.addWidget(self.table)

        # Bottom Bar Tracker (Stats Label)
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E2E8F0; padding: 5px;")
        layout.addWidget(self.stats_label)

        main_layout.addWidget(right_panel, 1)

        self.load_groups_into_sidebar()
        self.load_profiles_into_table()

    def load_groups_into_sidebar(self):
        self.group_list_widget.clear()

        all_item = QListWidgetItem("All Groups")
        all_item.setData(Qt.ItemDataRole.UserRole, "All Groups")
        self.group_list_widget.addItem(all_item)

        default_item = QListWidgetItem("Default")
        default_item.setData(Qt.ItemDataRole.UserRole, "Default")
        self.group_list_widget.addItem(default_item)

        groups = get_all_groups()
        for g in groups:
            if g['group_name'] != "Default":
                item = QListWidgetItem(g['group_name'])
                item.setData(Qt.ItemDataRole.UserRole, g['id'])
                self.group_list_widget.addItem(item)

        self.group_list_widget.setCurrentRow(0)

    def add_new_group(self):
        name, ok = QInputDialog.getText(self, "New Group", "Enter Group Name:")
        if ok and name.strip():
            success, msg = add_group(name.strip())
            if success:
                self.load_groups_into_sidebar()
            else:
                QMessageBox.warning(self, "Error", msg)

    def delete_selected_group(self):
        curr_item = self.group_list_widget.currentItem()
        if not curr_item:
            return

        group_name = curr_item.text()
        if group_name in ["All Groups", "Default"]:
            QMessageBox.warning(self, "Invalid Selection", "Cannot delete default groups.")
            return

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete the group '{group_name}'?\nProfiles in this group will be moved to 'Default'.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            group_id = curr_item.data(Qt.ItemDataRole.UserRole)
            delete_group(group_id, group_name)
            self.load_groups_into_sidebar()
            self.load_profiles_into_table()

    def on_group_selected(self, item):
        self.load_profiles_into_table()

    def update_stats_label(self):
        total, active, checkpoint = get_profile_stats()
        running = len(ACTIVE_DRIVERS)
        selected = 0
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected += 1

        self.stats_label.setText(f"Selected: {selected}  |  Running: {running}  |  Total: {total}  (Active: {active}, Checkpoint: {checkpoint})")

    def load_profiles_into_table(self):
        self.table.setRowCount(0)
        profiles = get_all_profiles()

        curr_group_item = self.group_list_widget.currentItem()
        current_group = "All Groups"
        if curr_group_item:
            current_group = curr_group_item.text()

        self.update_stats_label()

        delay = 0
        for row_idx, profile in enumerate(profiles):
            self.table.insertRow(row_idx)

            # Filtering Logic
            is_hidden = False
            group_name = profile.get('group_name', 'Default') or 'Default'
            if current_group != "All Groups" and current_group != group_name:
                is_hidden = True

            search_query = self.search_input.text().strip().lower()
            if search_query:
                name_match = search_query in profile.get('profile_name', '').lower()
                status_match = search_query in profile.get('status_text', '').lower()
                if not (name_match or status_match):
                    is_hidden = True

            self.table.setRowHidden(row_idx, is_hidden)

            # Checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0,0,0,0)
            checkbox = QCheckBox()
            checkbox.setProperty("profile_id", profile['id'])
            checkbox.stateChanged.connect(self.update_stats_label) # Update selected count live
            chk_layout.addWidget(checkbox)
            self.table.setCellWidget(row_idx, 0, chk_widget)

            # Text Fields
            self.table.setItem(row_idx, 1, QTableWidgetItem(profile['profile_name']))

            proxy_str = profile.get('account_proxy', '')
            proxy_display = proxy_str if proxy_str else "Direct IP"
            proxy_item = QTableWidgetItem(f"⏳ {proxy_display}")
            self.table.setItem(row_idx, 2, proxy_item)

            if proxy_str:
                proxy_worker = ProxyCheckWorker(row_idx, proxy_str)
                proxy_worker.signals.result.connect(self.on_proxy_check_result)
                self.threadpool.start(proxy_worker)
            else:
                self.on_proxy_check_result(row_idx, True)

            self.table.setItem(row_idx, 3, QTableWidgetItem(profile.get('last_active', 'Never')))

            status_text = profile.get('status_text', 'Pending')
            status_item = QTableWidgetItem(status_text)
            if 'Active' in status_text:
                status_item.setForeground(Qt.GlobalColor.green)
            elif 'Starting' in status_text or 'Initializing' in status_text:
                status_item.setText("🔄 Initializing...")
                status_item.setForeground(Qt.GlobalColor.cyan)
            elif 'Checkpoint' in status_text:
                status_item.setForeground(Qt.GlobalColor.yellow)
            elif 'Invalid' in status_text or 'Error' in status_text:
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.white)

            self.table.setItem(row_idx, 4, status_item)

            # Manage Button Menu
            manage_btn = QPushButton("⚙️ Manage")
            manage_btn.setStyleSheet("background-color: #374151; color: white; border-radius: 6px; padding: 5px 10px; font-weight: bold;")

            manage_menu = QMenu(manage_btn)
            manage_menu.setStyleSheet("""
                QMenu { background-color: #1E232B; color: white; border: 1px solid #2D3139; border-radius: 6px; }
                QMenu::item { padding: 8px 20px; }
                QMenu::item:selected { background-color: #374151; }
            """)

            # Logic binds
            act_launch_fb = manage_menu.addAction("🚀 Launch Browser (FB Home)")
            act_launch_fb.triggered.connect(lambda checked, p=profile: self.launch_single_profile(p, "Facebook Login & Home", ""))

            act_launch_man = manage_menu.addAction("🕸️ Launch Manual (Blank Page)")
            act_launch_man.triggered.connect(lambda checked, p=profile: self.launch_single_profile(p, "Manual (Blank Tab)", ""))

            act_login = manage_menu.addAction("🔑 Auto-Login Session")
            act_login.triggered.connect(lambda checked, p=profile: self.check_single_profile_status(p))

            manage_menu.addSeparator()

            act_export_cookie = manage_menu.addAction("🍪 Export Session")
            act_export_cookie.triggered.connect(lambda checked, p=profile: self.export_single_cookie(p))

            act_import_cookie = manage_menu.addAction("📂 Import Session")
            act_import_cookie.triggered.connect(lambda checked, p=profile: self.manage_single_cookie(p))

            act_proxy = manage_menu.addAction("🔄 Rotate Proxy")
            act_proxy.triggered.connect(lambda checked, pid=profile['id']: self.manage_single_proxy(pid))

            act_group = manage_menu.addAction("📂 Change Group")
            act_group.triggered.connect(lambda checked, pid=profile['id']: self.manage_single_group(pid))

            manage_menu.addSeparator()

            act_stop = manage_menu.addAction("🛑 Stop Profile")
            if profile['id'] in ACTIVE_DRIVERS:
                act_stop.triggered.connect(lambda checked, pid=profile['id']: self.stop_single_profile(pid))
            else:
                act_stop.setEnabled(False)

            act_del = manage_menu.addAction("🗑️ Delete Permanently")
            act_del.triggered.connect(lambda checked, pid=profile['id']: self.delete_profile_handler(pid))

            manage_btn.setMenu(manage_menu)

            # Simple fade-in animation wrapper for the row elements
            opacity_effect = QGraphicsOpacityEffect(self.table)
            manage_btn.setGraphicsEffect(opacity_effect)

            anim = QPropertyAnimation(opacity_effect, b"opacity", self.table)
            anim.setDuration(300)
            anim.setStartValue(0)
            anim.setEndValue(1)
            # Use QTimer to stagger the fade in
            QTimer.singleShot(delay, anim.start)
            delay += 20 # 20ms stagger per row

            self.table.setCellWidget(row_idx, 5, manage_btn)


    @pyqtSlot(int, bool)
    def on_proxy_check_result(self, row_idx, is_alive):
        item = self.table.item(row_idx, 2)
        if item:
            text = item.text().replace("⏳ ", "") # Strip the hourglass
            if is_alive:
                item.setText(f"🟢 {text}")
            else:
                item.setText(f"🔴 {text}")

    def filter_table(self):
        self.load_profiles_into_table()

    def open_context_menu(self, position):
        menu = QMenu()

        # New Group & Proxy Management Features
        group_action = menu.addAction("📁 Move Selected to Group")
        proxy_action = menu.addAction("🛡️ Update Proxies")
        delete_all_action = menu.addAction("❌ Delete Selected Profiles")
        menu.addSeparator()

        # Existing running tools
        ip_action = menu.addAction("🌐 Auto-Fill 'What is my IP' (Running only)")
        cache_action = menu.addAction("🧹 Bulk Cache Clear (Running only)")
        screenshot_action = menu.addAction("📸 Quick Screenshot (Running only)")
        menu.addSeparator()
        disk_clean_action = menu.addAction("🗑️ Clear Temp Files (Disk Optimization)")

        action = menu.exec(self.table.mapToGlobal(position))

        if action == group_action:
            self.execute_bulk_group_update()
        elif action == proxy_action:
            self.execute_bulk_proxy_update()
        elif action == delete_all_action:
            self.execute_bulk_delete()
        elif action == ip_action:
            self.execute_right_click_action("ip")
        elif action == cache_action:
            self.execute_right_click_action("cache")
        elif action == screenshot_action:
            self.execute_right_click_action("screenshot")
        elif action == disk_clean_action:
            self.execute_disk_cleanup()

    def execute_bulk_group_update(self):
        groups = get_all_groups()
        group_names = ["Default"] + [g['group_name'] for g in groups if g['group_name'] != "Default"]

        new_group, ok = QInputDialog.getItem(self, "Move to Group", "Select target group:", group_names, 0, False)
        if ok and new_group:
            updated = 0
            for row in range(self.table.rowCount()):
                chk_widget = self.table.cellWidget(row, 0)
                if chk_widget:
                    checkbox = chk_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        profile_id = checkbox.property("profile_id")
                        update_profile_group(profile_id, new_group)
                        updated += 1
            if updated > 0:
                self.load_profiles_into_table()
                QMessageBox.information(self, "Group Updated", f"Moved {updated} profiles to group: {new_group}")

    def execute_bulk_export(self):
        selected_ids = []
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_ids.append(checkbox.property("profile_id"))

        if not selected_ids:
            QMessageBox.warning(self, "Selection Error", "Please select at least one profile to export.")
            return

        options = QFileDialog.Option.ShowDirsOnly
        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Destination Folder", "", options=options)
        if not export_dir:
            return

        profiles = get_all_profiles()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'sys_config.db')
        profiles_base = os.path.join(base_dir, 'profiles')

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"FB_Profiles_Export_{timestamp}.zip"
        zip_path = os.path.join(export_dir, zip_filename)

        exported_count = 0
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. Include Database for Global Sync
                if os.path.exists(db_path):
                    zipf.write(db_path, 'sys_config.db')

                # 2. Iterate and Compress Selected Profile Directories + Generate specific metadata
                for p in profiles:
                    if p['id'] in selected_ids:
                        target_folder = os.path.join(profiles_base, f"id_{p['account_id']}")
                        if os.path.exists(target_folder):
                            exported_count += 1

                            # Write physical folder
                            for root, dirs, files in os.walk(target_folder):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, base_dir)
                                    zipf.write(file_path, arcname)

                            # Inject isolated metadata.json into the profile's archive directory
                            meta_str = json.dumps(p, indent=4)
                            zipf.writestr(f"profiles/id_{p['account_id']}/metadata.json", meta_str)

            QMessageBox.information(self, "Export Complete", f"Successfully exported {exported_count} profiles to:\n{zip_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export profiles:\n{e}")

    def execute_import_backup(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Backup ZIP File", "", "ZIP Files (*.zip)", options=options)

        if not file_path:
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        profiles_base = os.path.join(base_dir, 'profiles')

        imported_count = 0
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # Iterate through members to identify distinct profiles using metadata.json
                for member in zipf.namelist():
                    if member.endswith('metadata.json'):
                        # Read the metadata
                        with zipf.open(member) as f:
                            meta_data = json.loads(f.read().decode('utf-8'))

                        old_acc_id = meta_data.get('account_id')
                        if not old_acc_id:
                            continue

                        # Generate new ID mapping
                        new_acc_id = str(uuid.uuid4())[:8]
                        next_seq = get_next_sequential_id()
                        new_profile_name = f"id{next_seq}"

                        # Add to DB
                        success, _ = add_profile(new_profile_name, new_acc_id,
                                               meta_data.get('account_proxy', ''),
                                               meta_data.get('custom_user_agent', ''),
                                               meta_data.get('email', ''),
                                               meta_data.get('password', ''))
                        if success:
                            imported_count += 1
                            target_dir = os.path.join(profiles_base, f"id_{new_acc_id}")
                            os.makedirs(target_dir, exist_ok=True)

                            # Extract specific profile contents from ZIP, remapping paths
                            # Normalise slashes to forward slashes to match zipfile format
                            old_prefix = f"profiles/id_{old_acc_id}/".replace('\\', '/')
                            for sub_member in zipf.namelist():
                                sub_member_norm = sub_member.replace('\\', '/')
                                if sub_member_norm.startswith(old_prefix) and not sub_member_norm.endswith('metadata.json'):
                                    rel_path = sub_member_norm[len(old_prefix):]
                                    if rel_path:
                                        out_path = os.path.join(target_dir, os.path.normpath(rel_path))
                                        os.makedirs(os.path.dirname(out_path), exist_ok=True)
                                        if not sub_member_norm.endswith('/'): # Not a directory marker
                                            with zipf.open(sub_member) as source, open(out_path, "wb") as target:
                                                shutil.copyfileobj(source, target)

            self.load_profiles_into_table()
            self.populate_account_picker()
            QMessageBox.information(self, "Restore Complete", f"Successfully restored {imported_count} profiles from backup.")
        except Exception as e:
            QMessageBox.critical(self, "Restore Error", f"Failed to restore profiles:\n{e}")

    def execute_bulk_proxy_update(self):
        new_proxy, ok = QInputDialog.getText(self, "Update Proxy", "Enter new Proxy (IP:PORT or IP:PORT:USER:PASS):")
        if ok:
            updated = 0
            for row in range(self.table.rowCount()):
                chk_widget = self.table.cellWidget(row, 0)
                if chk_widget:
                    checkbox = chk_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        profile_id = checkbox.property("profile_id")
                        update_profile_proxy(profile_id, new_proxy.strip())
                        updated += 1
            if updated > 0:
                self.load_profiles_into_table()
                QMessageBox.information(self, "Proxy Updated", f"Updated proxies for {updated} profiles.")

    def stop_single_profile(self, profile_id):
        stop_all_selected([profile_id], self.threadpool)
        self.load_profiles_into_table()

    def stop_selected_profiles(self):
        ids_to_stop = []
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    ids_to_stop.append(checkbox.property("profile_id"))
        if ids_to_stop:
            stop_all_selected(ids_to_stop, self.threadpool)
            self.load_profiles_into_table()
            QMessageBox.information(self, "Stopped", f"Successfully sent stop signal to {len(ids_to_stop)} browsers.")

    def execute_bulk_delete(self):
        selected_ids = []
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_ids.append(checkbox.property("profile_id"))

        if not selected_ids:
            return

        for profile_id in selected_ids:
            if profile_id in ACTIVE_DRIVERS:
                QMessageBox.warning(self, "Deletion Aborted", "One or more selected profiles are currently running.\nPlease Stop the browsers before attempting to delete them to avoid file lock errors.")
                return

        reply = QMessageBox.question(self, 'Confirm Hard Delete',
                                     'Are you sure you want to PERMANENTLY delete all selected profiles?\nThis will completely wipe their folders from your storage.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            deleted = 0
            base_dir = os.path.dirname(os.path.abspath(__file__))
            profiles = get_all_profiles()

            for profile_id in selected_ids:
                acc_id = None
                for p in profiles:
                    if p['id'] == profile_id:
                        acc_id = p['account_id']
                        break

                delete_profile(profile_id)
                deleted += 1

                if acc_id:
                    profile_dir = os.path.join(base_dir, 'profiles', f"id_{acc_id}")
                    if os.path.exists(profile_dir):
                        try:
                            shutil.rmtree(profile_dir)
                        except Exception as e:
                            print(f"Failed to delete directory {profile_dir}: {e}")

            if deleted > 0:
                self.load_profiles_into_table()
                self.populate_account_picker()
                QMessageBox.information(self, "Hard Delete Complete", f"Permanently deleted {deleted} profiles and wiped their storage folders.")

    def execute_disk_cleanup(self):
        profiles = get_all_profiles()
        cleaned = 0
        base_dir = os.path.dirname(os.path.abspath(__file__))

        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    profile_id = checkbox.property("profile_id")
                    if profile_id in ACTIVE_DRIVERS:
                        # Skip running drivers to avoid file lock crashes
                        continue

                    for p in profiles:
                        if p['id'] == profile_id:
                            profile_dir = os.path.join(base_dir, 'profiles', f"id_{p['account_id']}")
                            # Specifically target the Default cache folders to optimize disk usage
                            cache_paths = [
                                os.path.join(profile_dir, "Default", "Cache"),
                                os.path.join(profile_dir, "Default", "Code Cache"),
                                os.path.join(profile_dir, "Default", "DawnCache"),
                                os.path.join(profile_dir, "Default", "GPUCache")
                            ]
                            for path in cache_paths:
                                if os.path.exists(path):
                                    try:
                                        shutil.rmtree(path)
                                        cleaned += 1
                                    except Exception as e:
                                        print(f"[{profile_id}] Could not delete {path}: {e}")
                            break
        QMessageBox.information(self, "Disk Optimization", f"Cleared temp files across {cleaned} cache directories.")

    def execute_right_click_action(self, action_type):
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    profile_id = checkbox.property("profile_id")
                    driver = ACTIVE_DRIVERS.get(profile_id)
                    if driver:
                        try:
                            if action_type == "ip":
                                # Open a new tab or navigate to what is my IP
                                driver.get("https://api.ipify.org?format=json")
                            elif action_type == "cache":
                                # Clear cache but keep cookies using CDP
                                driver.execute_cdp_cmd("Network.clearBrowserCache", {})
                                print(f"[{profile_id}] Cache cleared via CDP.")
                            elif action_type == "screenshot":
                                os.makedirs("screenshots", exist_ok=True)
                                path = f"screenshots/proof_{profile_id}_{uuid.uuid4().hex[:5]}.png"
                                driver.save_screenshot(path)
                                print(f"[{profile_id}] Screenshot saved to {path}")
                        except Exception as e:
                            print(f"[{profile_id}] Action {action_type} failed: {e}")

        if action_type == "cache":
             QMessageBox.information(self, "Cache Cleared", "Bulk cache clear executed for selected active profiles via CDP.")
        elif action_type == "screenshot":
             QMessageBox.information(self, "Screenshots Saved", "Screenshots saved to ./screenshots/ folder.")

    # Removed obsolete on_task_type_changed

    def toggle_all_table_accounts(self, state):
        target_state = Qt.CheckState(state)
        for row in range(self.table.rowCount()):
            # Only toggle visible rows (filtered rows)
            if not self.table.isRowHidden(row):
                chk_widget = self.table.cellWidget(row, 0)
                if chk_widget:
                    checkbox = chk_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setCheckState(target_state)

    def import_profiles_from_txt(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Accounts Text File", "", "Text Files (*.txt)", options=options)

        if not file_path:
            return

        next_id = get_next_sequential_id()
        profiles_to_insert = []

        base_dir = os.path.dirname(os.path.abspath(__file__))
        profiles_base = os.path.join(base_dir, 'profiles')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split('|')
                    if len(parts) >= 2:
                        email = parts[0]
                        password = parts[1]
                        proxy = parts[2] if len(parts) > 2 else ""

                        # Sequential Naming
                        profile_name = f"id{next_id}"
                        next_id += 1

                        acc_id = str(uuid.uuid4())[:8]

                        # (profile_name, account_id, account_proxy, custom_user_agent, email, password)
                        profiles_to_insert.append((profile_name, acc_id, proxy, "", email, password))

                        # Create folder automatically on hard drive
                        target_dir = os.path.join(profiles_base, f'id_{acc_id}')
                        os.makedirs(target_dir, exist_ok=True)

            imported = bulk_insert_profiles(profiles_to_insert)

            self.load_profiles_into_table()
            self.populate_account_picker()
            QMessageBox.information(self, "Import Complete", f"Successfully imported {imported} accounts.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to read file:\n{e}")

    def bulk_empty_create(self):
        count, ok = QInputDialog.getInt(self, "Bulk Create Empty Profiles", "Enter number of profiles to create:", 50, 1, 1000)
        if ok and count > 0:
            next_id = get_next_sequential_id()
            profiles_to_insert = []

            base_dir = os.path.dirname(os.path.abspath(__file__))
            profiles_base = os.path.join(base_dir, 'profiles')

            for i in range(count):
                profile_name = f"id{next_id}"
                next_id += 1
                acc_id = str(uuid.uuid4())[:8]

                # (profile_name, account_id, account_proxy, custom_user_agent, email, password)
                profiles_to_insert.append((profile_name, acc_id, "", "", "", ""))

                # Create the folder on the hard drive
                target_dir = os.path.join(profiles_base, f'id_{acc_id}')
                os.makedirs(target_dir, exist_ok=True)

            imported = bulk_insert_profiles(profiles_to_insert)

            self.load_profiles_into_table()
            self.populate_account_picker()
            QMessageBox.information(self, "Success", f"Created {imported} empty sequential profiles.")

    def import_cookie_file(self):
        # Determine the selected profile
        selected_profile_id = None
        selected_acc_id = None
        selected_count = 0

        profiles = get_all_profiles()
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    profile_id = checkbox.property("profile_id")
                    selected_profile_id = profile_id
                    selected_count += 1

        if selected_count != 1:
            QMessageBox.warning(self, "Selection Error", "Please select exactly one profile to import a single cookie file.")
            return

        for p in profiles:
            if p['id'] == selected_profile_id:
                selected_acc_id = p['account_id']
                break

        if not selected_acc_id:
            return

        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Single JSON Cookie", "", "JSON Files (*.json)", options=options)

        if not file_path:
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        profiles_base = os.path.join(base_dir, 'profiles')

        file_name = os.path.basename(file_path)
        target_dir = os.path.join(profiles_base, f'id_{selected_acc_id}')
        os.makedirs(target_dir, exist_ok=True)
        dst_path = os.path.join(target_dir, file_name)
        try:
            shutil.copy(file_path, dst_path)
            QMessageBox.information(self, "Cookie Imported", f"Successfully imported {file_name} to the selected profile.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to copy cookie:\n{e}")

    def import_via_cookies(self):
        options = QFileDialog.Option.ShowDirsOnly
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder containing JSON Cookies", "", options=options)

        if not folder_path:
            return

        imported = 0
        next_id = get_next_sequential_id()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        profiles_base = os.path.join(base_dir, 'profiles')

        for file_name in os.listdir(folder_path):
            if file_name.endswith('.json'):
                profile_name = f"id{next_id}"
                next_id += 1
                acc_id = str(uuid.uuid4())[:8]

                success, _ = add_profile(profile_name, acc_id)
                if success:
                    imported += 1
                    target_dir = os.path.join(profiles_base, f'id_{acc_id}')
                    os.makedirs(target_dir, exist_ok=True)

                    src_path = os.path.join(folder_path, file_name)
                    dst_path = os.path.join(target_dir, 'cookies.json')
                    try:
                        shutil.copy(src_path, dst_path)
                    except Exception as e:
                        print(f"Warning: Failed to copy cookie {file_name}: {e}")

        self.load_profiles_into_table()
        self.populate_account_picker()
        QMessageBox.information(self, "Cookies Imported", f"Successfully generated {imported} profiles from folder.")

    def open_add_profile_dialog(self):
        dialog = AddProfileDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "Error", "Profile Name is required.")
                return

            # Generate a unique account ID
            acc_id = str(uuid.uuid4())[:8]

            success, msg = add_profile(data['name'], acc_id, data['proxy'], data['ua'])
            if success:
                self.load_profiles_into_table()
            else:
                QMessageBox.critical(self, "Database Error", msg)

    def delete_profile_handler(self, profile_id):
        if profile_id in ACTIVE_DRIVERS:
            QMessageBox.warning(self, "Deletion Aborted", "This profile is currently running.\nPlease Stop the browser before attempting to delete it to avoid file lock errors.")
            return

        reply = QMessageBox.question(self, 'Confirm Hard Delete',
                                     'Are you sure you want to PERMANENTLY delete this profile?\nThis will completely wipe its folder from your storage.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            profiles = get_all_profiles()
            acc_id = None
            for p in profiles:
                if p['id'] == profile_id:
                    acc_id = p['account_id']
                    break

            delete_profile(profile_id)

            if acc_id:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                profile_dir = os.path.join(base_dir, 'profiles', f"id_{acc_id}")
                if os.path.exists(profile_dir):
                    try:
                        shutil.rmtree(profile_dir)
                    except Exception as e:
                        print(f"Failed to delete directory {profile_dir}: {e}")

            self.load_profiles_into_table()

    def launch_single_profile(self, profile_data, task_type="Facebook Login & Home", custom_url=""):
        print(f"Launching profile {profile_data['profile_name']} on background thread...")
        worker = BrowserLauncherWorker(profile_data, task_type, custom_url)
        worker.signals.finished.connect(self.on_browser_closed)
        worker.signals.error.connect(self.on_browser_error)
        worker.signals.status_update.connect(self.on_status_update)
        self.threadpool.start(worker)
        # Update UI instantly to show 'Running' Guard
        self.load_profiles_into_table()

    def check_single_profile_status(self, profile_data):
        print(f"Auto-Login/Checking status for {profile_data['profile_name']} on background thread...")
        worker = AccountMonitorWorker(profile_data)
        worker.signals.finished.connect(self.on_browser_closed)
        worker.signals.error.connect(self.on_browser_error)
        worker.signals.status_update.connect(self.on_status_update)
        self.threadpool.start(worker)
        self.load_profiles_into_table()

    def check_selected_profiles_status(self):
        profiles = get_all_profiles()
        launched = 0
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    profile_id = checkbox.property("profile_id")
                    for p in profiles:
                        if p['id'] == profile_id:
                            self.check_single_profile_status(p)
                            launched += 1
                            break
        if launched > 0:
            QMessageBox.information(self, "Status Check Started", f"Queued {launched} accounts for Auto-Login & Status Check.\nThe table will update automatically.")
        else:
            QMessageBox.warning(self, "No Selection", "Please select at least one account.")

    def launch_selected_profiles(self, task_type):
        custom_url = ""
        if task_type == "Custom URL":
            url, ok = QInputDialog.getText(self, "Custom URL", "Enter URL to launch:")
            if ok and url.strip():
                custom_url = url.strip()
            else:
                return

        profiles = get_all_profiles()
        profiles_to_launch = []

        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    profile_id = checkbox.property("profile_id")
                    if profile_id in ACTIVE_DRIVERS:
                        continue
                    for p in profiles:
                        if p['id'] == profile_id:
                            profiles_to_launch.append(p)
                            break

        if not profiles_to_launch:
             QMessageBox.warning(self, "Validation Error", "No valid stopped profiles were selected.")
             return

        for p in profiles_to_launch:
            # We spin off the worker directly without triggering a full UI refresh on every loop
            print(f"Dispatching profile {p['profile_name']}...")
            worker = BrowserLauncherWorker(p, task_type, custom_url)
            worker.signals.finished.connect(self.on_browser_closed)
            worker.signals.error.connect(self.on_browser_error)
            worker.signals.status_update.connect(self.on_status_update)
            self.threadpool.start(worker)

        self.load_profiles_into_table() # Refresh UI just once at the end
        QMessageBox.information(self, "Launched", f"Successfully dispatched {len(profiles_to_launch)} profiles asynchronously.")

    def launch_single_profile(self, profile_data, task_type="Facebook Login & Home", custom_url=""):
        print(f"Launching profile {profile_data['profile_name']} on background thread...")
        worker = BrowserLauncherWorker(profile_data, task_type, custom_url)
        worker.signals.finished.connect(self.on_browser_closed)
        worker.signals.error.connect(self.on_browser_error)
        worker.signals.status_update.connect(self.on_status_update)
        self.threadpool.start(worker)
        # Update UI instantly to show 'Running' Guard
        self.load_profiles_into_table()

    @pyqtSlot(int, str)
    def on_status_update(self, profile_id, new_status):
        # Dynamically updates the table when the background thread emits a status change
        self.update_stats_label()
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.property("profile_id") == profile_id:
                    status_item = QTableWidgetItem(new_status)
                    if 'Active' in new_status:
                        status_item.setForeground(Qt.GlobalColor.green)
                    elif 'Starting' in new_status or 'Initializing' in new_status:
                        status_item.setText("🔄 Initializing...")
                        status_item.setForeground(Qt.GlobalColor.cyan)
                    elif 'Checkpoint' in new_status:
                        status_item.setForeground(Qt.GlobalColor.yellow)
                    elif 'Invalid' in new_status or 'Error' in new_status:
                        status_item.setForeground(Qt.GlobalColor.red)
                    else:
                        status_item.setForeground(Qt.GlobalColor.white)
                    self.table.setItem(row, 4, status_item)
                    break

    def on_browser_closed(self, profile_id):
        print(f"Browser closed for profile ID {profile_id}. Refreshing table.")
        self.update_stats_label()
        # Only fetch the updated profile to avoid resetting the entire table and unchecking boxes
        profiles = get_all_profiles()
        updated_profile = next((p for p in profiles if p['id'] == profile_id), None)

        if updated_profile:
            for row in range(self.table.rowCount()):
                chk_widget = self.table.cellWidget(row, 0)
                if chk_widget:
                    checkbox = chk_widget.findChild(QCheckBox)
                    if checkbox and checkbox.property("profile_id") == profile_id:
                        # Update Last Active
                        self.table.setItem(row, 3, QTableWidgetItem(updated_profile.get('last_active', 'Never')))

                        # Update Status
                        status_text = updated_profile.get('status_text', 'Pending')
                        status_item = QTableWidgetItem(status_text)
                        if 'Active' in status_text:
                            status_item.setForeground(Qt.GlobalColor.green)
                        elif 'Checkpoint' in status_text:
                            status_item.setForeground(Qt.GlobalColor.yellow)
                        elif 'Invalid' in status_text or 'Error' in status_text:
                            status_item.setForeground(Qt.GlobalColor.red)
                        else:
                            status_item.setForeground(Qt.GlobalColor.white)
                        self.table.setItem(row, 4, status_item)
                        break

    def build_lead_router(self):
        layout = QHBoxLayout(self.lead_router_screen)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Active Profiles/Chats List
        left_panel = QFrame()
        left_panel.setFixedWidth(250)
        left_panel.setObjectName("Card")
        left_layout = QVBoxLayout(left_panel)

        title_label = QLabel("Active Inbox")
        title_label.setObjectName("HeaderTitle")
        left_layout.addWidget(title_label)

        self.inbox_list = QListWidget()
        self.inbox_list.setStyleSheet("background-color: #1E232B; color: white; border: none; border-radius: 6px;")
        # Placeholder items
        self.inbox_list.addItem("id1 - New Message!")
        self.inbox_list.addItem("id2 - Active")
        self.inbox_list.addItem("id5 - Pending")

        left_layout.addWidget(self.inbox_list)

        # Right side: Chat Area & Controls
        right_panel = QFrame()
        right_panel.setObjectName("Card")
        right_layout = QVBoxLayout(right_panel)

        # Header Controls
        chat_header = QHBoxLayout()
        chat_title = QLabel("Chat History")
        chat_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        chat_header.addWidget(chat_title)

        chat_header.addStretch()

        self.auto_responder_toggle = QCheckBox("Enable Auto-Responder")
        self.auto_responder_toggle.setStyleSheet("color: white; font-weight: bold;")
        chat_header.addWidget(self.auto_responder_toggle)

        right_layout.addLayout(chat_header)

        # Chat History Window
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #1E232B; color: white; border: 1px solid #2D3139; border-radius: 6px;")
        self.chat_history.setText("System: Waiting for active chat selection...\n\nUser Profile: id1\nLead: Is this still available?\nBot (Auto): Please contact our specialist at 555-0199 to book your service now!")
        right_layout.addWidget(self.chat_history)

        # Manual Reply Area
        reply_layout = QHBoxLayout()
        self.reply_input = QLineEdit()
        self.reply_input.setPlaceholderText("Type a manual reply...")
        self.reply_input.setStyleSheet("background-color: #1E232B; color: white; border: 1px solid #2D3139; border-radius: 6px; padding: 10px;")

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("background-color: #6366F1; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold;")

        reply_layout.addWidget(self.reply_input)
        reply_layout.addWidget(send_btn)

        right_layout.addLayout(reply_layout)

        layout.addWidget(left_panel)
        layout.addWidget(right_panel, 1)

    def build_bulk_listing(self):
        layout = QHBoxLayout(self.bulk_listing_screen)

        # Left Panel: Post Form
        left_panel = QFrame()
        left_panel.setObjectName("Card")
        left_layout = QVBoxLayout(left_panel)

        title_label = QLabel("Marketplace Service Listing Form")
        title_label.setObjectName("HeaderTitle")
        left_layout.addWidget(title_label)

        form_layout = QFormLayout()

        self.listing_title = QLineEdit()
        self.listing_title.setPlaceholderText("e.g., {Urgent|Emergency} Repair...")

        self.listing_price = QLineEdit()
        self.listing_price.setPlaceholderText("0")

        self.listing_category = QLineEdit()
        self.listing_category.setPlaceholderText("e.g., Tools & Home Improvement")

        self.listing_location = QLineEdit()
        self.listing_location.setPlaceholderText("e.g., Houston, TX")

        self.listing_tags = QLineEdit()
        self.listing_tags.setPlaceholderText("e.g., plumber, repair, pipes")

        self.listing_desc = QTextEdit()
        self.listing_desc.setPlaceholderText("Description with {Spintax|Variations} support...")
        self.listing_desc.setStyleSheet("background-color: #1E232B; color: white; border: 1px solid #2D3139; border-radius: 6px;")

        form_layout.addRow("Title:", self.listing_title)
        form_layout.addRow("Price:", self.listing_price)
        form_layout.addRow("Category:", self.listing_category)
        form_layout.addRow("Location:", self.listing_location)
        form_layout.addRow("Tags:", self.listing_tags)
        form_layout.addRow("Description:", self.listing_desc)

        left_layout.addLayout(form_layout)

        # Images Attachment
        img_layout = QHBoxLayout()
        img_label = QLabel("Images:")
        self.img_btn = QPushButton("Select Photos")
        self.img_btn.setStyleSheet("background-color: #4B5563; color: white; padding: 5px; border-radius: 4px;")
        self.img_btn.clicked.connect(self.select_images)
        img_layout.addWidget(img_label)
        img_layout.addWidget(self.img_btn)
        img_layout.addStretch()
        left_layout.addLayout(img_layout)

        self.img_list = QListWidget()
        self.img_list.setMaximumHeight(80)
        self.img_list.setStyleSheet("background-color: #1E232B; color: white; border: 1px solid #2D3139; border-radius: 6px;")
        self.image_paths = []
        left_layout.addWidget(self.img_list)

        layout.addWidget(left_panel, 2)

        # Right Panel: Account Picker
        right_panel = QFrame()
        right_panel.setObjectName("Card")
        right_layout = QVBoxLayout(right_panel)

        acc_title = QLabel("Select Accounts for Bulk Post")
        acc_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(acc_title)

        select_all_btn = QPushButton("Check / Uncheck All")
        select_all_btn.setStyleSheet("background-color: #4B5563; color: white; padding: 5px; border-radius: 4px;")
        select_all_btn.clicked.connect(self.toggle_all_accounts)
        right_layout.addWidget(select_all_btn)

        self.acc_list_widget = QListWidget()
        self.acc_list_widget.setStyleSheet("background-color: #1E232B; color: white; border: 1px solid #2D3139; border-radius: 6px;")
        self.populate_account_picker()
        right_layout.addWidget(self.acc_list_widget)

        self.start_bulk_btn = QPushButton("🚀 Start Bulk Listing")
        self.start_bulk_btn.setObjectName("PrimaryAction")
        self.start_bulk_btn.clicked.connect(self.start_bulk_listing_task)
        right_layout.addWidget(self.start_bulk_btn)

        layout.addWidget(right_panel, 1)

    def select_images(self):
        options = QFileDialog.Option.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.webp)", options=options)
        if files:
            self.image_paths.extend(files)
            for f in files:
                self.img_list.addItem(os.path.basename(f))

    def populate_account_picker(self):
        self.acc_list_widget.clear()
        profiles = get_all_profiles()
        for p in profiles:
            item = QListWidgetItem(p['profile_name'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, p['id'])
            self.acc_list_widget.addItem(item)

    def toggle_all_accounts(self):
        for i in range(self.acc_list_widget.count()):
            item = self.acc_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setCheckState(Qt.CheckState.Checked)

    def start_bulk_listing_task(self):
        # Validate Form
        title = self.listing_title.text().strip()
        desc = self.listing_desc.toPlainText().strip()
        if not title or not desc:
            QMessageBox.warning(self, "Validation Error", "Title and Description are required.")
            return

        selected_profile_ids = []
        for i in range(self.acc_list_widget.count()):
            item = self.acc_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_profile_ids.append(item.data(Qt.ItemDataRole.UserRole))

        if not selected_profile_ids:
            QMessageBox.warning(self, "Validation Error", "Please select at least one account to post to.")
            return

        listing_data = {
            'title': title,
            'price': self.listing_price.text().strip() or "0",
            'category': self.listing_category.text().strip(),
            'location': self.listing_location.text().strip(),
            'tags': self.listing_tags.text().strip(),
            'description': desc,
            'images': self.image_paths
        }

        profiles = get_all_profiles()
        launched = 0
        for p in profiles:
            if p['id'] in selected_profile_ids:
                worker = MarketplaceTaskWorker(p, listing_data)
                worker.signals.error.connect(self.on_browser_error)
                self.threadpool.start(worker)
                launched += 1

        QMessageBox.information(self, "Task Started", f"Successfully queued {launched} accounts for bulk listing.")

    def manage_single_proxy(self, profile_id):
        new_proxy, ok = QInputDialog.getText(self, "Update Proxy", "Enter new Proxy (IP:PORT or IP:PORT:USER:PASS):")
        if ok:
            update_profile_proxy(profile_id, new_proxy.strip())
            self.load_profiles_into_table()
            QMessageBox.information(self, "Proxy Updated", "Proxy updated successfully.")

    def manage_single_group(self, profile_id):
        groups = get_all_groups()
        group_names = ["Default"] + [g['group_name'] for g in groups if g['group_name'] != "Default"]

        new_group, ok = QInputDialog.getItem(self, "Move to Group", "Select target group:", group_names, 0, False)
        if ok and new_group:
            update_profile_group(profile_id, new_group)
            self.load_profiles_into_table()
            QMessageBox.information(self, "Group Updated", f"Moved profile to group: {new_group}")

    def export_single_cookie(self, profile_data):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cookie_path = os.path.join(base_dir, 'profiles', f"id_{profile_data['account_id']}", "cookies.json")

        if not os.path.exists(cookie_path):
            QMessageBox.warning(self, "Export Error", "No 'cookies.json' found for this profile. Launch it first to generate one.")
            return

        options = QFileDialog.Option.DontUseNativeDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Session Cookie", f"{profile_data['profile_name']}_cookies.json", "JSON Files (*.json)", options=options)

        if save_path:
            try:
                shutil.copy(cookie_path, save_path)
                QMessageBox.information(self, "Export Complete", "Successfully exported the session cookie.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export cookie:\n{e}")

    def manage_single_cookie(self, profile_data):
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Single JSON Cookie", "", "JSON Files (*.json)", options=options)

        if not file_path:
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(base_dir, 'profiles', f"id_{profile_data['account_id']}")
        os.makedirs(target_dir, exist_ok=True)

        dst_path = os.path.join(target_dir, 'cookies.json')
        try:
            shutil.copy(file_path, dst_path)
            QMessageBox.information(self, "Cookie Imported", "Successfully injected the selected session into this profile.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to copy cookie:\n{e}")

    def on_browser_error(self, err_tuple):
        err = err_tuple[0]
        QMessageBox.critical(self, "Browser Error", f"Failed to launch Chrome:\n{str(err)}")

    def open_buy_link(self):
        webbrowser.open(BUY_LINK)

if __name__ == '__main__':
    if not os.environ.get('DISPLAY'):
        print("Warning: Running without X server display. GUI will not be visible.")

    app = QApplication(sys.argv)
    ex = MainClientApp()
    ex.show()
    sys.exit(app.exec())
