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
                             QComboBox, QMenu, QInputDialog)
import shutil
from PyQt6.QtCore import Qt, QThreadPool, pyqtSlot, QRunnable, QObject, pyqtSignal
from shared_logic.security import verify_license, get_hardware_uuid
from shared_logic.config import BUY_LINK
import requests # For "What is my IP" check if needed or just redirect

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
        self.sidebar_widget.hide()

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

        # Header (Top Actions)
        header_layout = QHBoxLayout()
        title_label = QLabel("Account Manager")
        title_label.setObjectName("HeaderTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        add_btn = QPushButton("+ Add Profile")
        add_btn.setObjectName("PrimaryAction")
        add_btn.setStyleSheet("background-color: #6366F1; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        add_btn.clicked.connect(self.open_add_profile_dialog)
        header_layout.addWidget(add_btn)

        import_btn = QPushButton("📂 Import from TXT")
        import_btn.setStyleSheet("background-color: #4B5563; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        import_btn.clicked.connect(self.import_profiles_from_txt)
        header_layout.addWidget(import_btn)

        self.task_selector = QComboBox()
        self.task_selector.addItems(["Facebook Login & Home", "Custom URL", "Manual (Blank Tab)"])
        self.task_selector.currentTextChanged.connect(self.on_task_type_changed)
        header_layout.addWidget(QLabel("Goal:"))
        header_layout.addWidget(self.task_selector)

        self.custom_url_input = QLineEdit()
        self.custom_url_input.setPlaceholderText("https://...")
        self.custom_url_input.hide() # Hidden by default
        header_layout.addWidget(self.custom_url_input)

        status_btn = QPushButton("🔄 Auto-Login Status Check")
        status_btn.setStyleSheet("background-color: #F59E0B; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        status_btn.clicked.connect(self.check_selected_profiles_status)
        header_layout.addWidget(status_btn)

        layout.addLayout(header_layout)

        # Bulk Controls Toolbar
        bulk_toolbar = QFrame()
        bulk_toolbar.setStyleSheet("background-color: #1E232B; border-radius: 6px; padding: 5px;")
        bulk_layout = QHBoxLayout(bulk_toolbar)
        bulk_layout.setContentsMargins(5, 5, 5, 5)

        bulk_launch_btn = QPushButton("🚀 Bulk Launch")
        bulk_launch_btn.setStyleSheet("background-color: #10B981; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
        bulk_launch_btn.clicked.connect(self.launch_selected_profiles)
        bulk_layout.addWidget(bulk_launch_btn)

        bulk_stop_btn = QPushButton("🛑 Bulk Stop")
        bulk_stop_btn.setStyleSheet("background-color: #EF4444; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
        bulk_stop_btn.clicked.connect(self.stop_selected_profiles)
        bulk_layout.addWidget(bulk_stop_btn)

        bulk_delete_btn = QPushButton("🗑️ Bulk Delete")
        bulk_delete_btn.setStyleSheet("background-color: #EF4444; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
        bulk_delete_btn.clicked.connect(self.execute_bulk_delete)
        bulk_layout.addWidget(bulk_delete_btn)

        move_group_btn = QPushButton("📂 Move to Group")
        move_group_btn.setStyleSheet("background-color: #4B5563; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
        move_group_btn.clicked.connect(self.execute_bulk_group_update)
        bulk_layout.addWidget(move_group_btn)

        bulk_proxy_btn = QPushButton("🔄 Bulk Proxy Update")
        bulk_proxy_btn.setStyleSheet("background-color: #4B5563; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
        bulk_proxy_btn.clicked.connect(self.execute_bulk_proxy_update)
        bulk_layout.addWidget(bulk_proxy_btn)

        bulk_layout.addStretch()

        # Additional Builders (Cookies, Empty Creation)
        bulk_create_btn = QPushButton("➕ Bulk Empty Create")
        bulk_create_btn.setStyleSheet("background-color: #374151; color: white; padding: 6px; border-radius: 4px;")
        bulk_create_btn.clicked.connect(self.bulk_empty_create)
        bulk_layout.addWidget(bulk_create_btn)

        cookie_file_btn = QPushButton("🍪 Import Cookie File")
        cookie_file_btn.setStyleSheet("background-color: #374151; color: white; padding: 6px; border-radius: 4px;")
        cookie_file_btn.clicked.connect(self.import_cookie_file)
        bulk_layout.addWidget(cookie_file_btn)

        cookie_folder_btn = QPushButton("📁 Import Cookies via Folder")
        cookie_folder_btn.setStyleSheet("background-color: #374151; color: white; padding: 6px; border-radius: 4px;")
        cookie_folder_btn.clicked.connect(self.import_via_cookies)
        bulk_layout.addWidget(cookie_folder_btn)

        layout.addWidget(bulk_toolbar)

        # Table Controls: Search, Select All
        table_controls_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.setStyleSheet("color: white; padding: 5px 10px; font-weight: bold;")
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_table_accounts)
        table_controls_layout.addWidget(self.select_all_checkbox)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Name or Status...")
        self.search_input.setStyleSheet("background-color: #1E232B; color: white; padding: 5px; border-radius: 4px; border: 1px solid #4B5563;")
        self.search_input.textChanged.connect(self.filter_table)
        table_controls_layout.addWidget(self.search_input)

        layout.addLayout(table_controls_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["", "Profile Name", "Proxy", "Last Active", "Status", "Action", "Delete"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Checkbox col
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Launch col
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Delete col

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

        for profile in profiles:
            # Filtering Logic
            group_name = profile.get('group_name', 'Default') or 'Default'
            if current_group != "All Groups" and current_group != group_name:
                continue

            search_query = self.search_input.text().strip().lower()
            if search_query:
                name_match = search_query in profile.get('profile_name', '').lower()
                status_match = search_query in profile.get('status_text', '').lower()
                if not (name_match or status_match):
                    continue

            # Insert at the next available visual row
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

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
            elif 'Checkpoint' in status_text:
                status_item.setForeground(Qt.GlobalColor.yellow)
            elif 'Invalid' in status_text or 'Error' in status_text:
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.white)

            self.table.setItem(row_idx, 4, status_item)

            # Launch Button / Running Guard
            if profile['id'] in ACTIVE_DRIVERS:
                launch_btn = QPushButton("🔴 Stop")
                launch_btn.setStyleSheet("background-color: #EF4444; color: white; border-radius: 4px; padding: 5px; font-weight: bold;")
                launch_btn.clicked.connect(lambda checked, pid=profile['id']: self.stop_single_profile(pid))
            else:
                launch_btn = QPushButton("🚀 Launch")
                launch_btn.setProperty("class", "LaunchBtn")
                launch_btn.setStyleSheet("background-color: #10B981; color: white; border-radius: 4px; padding: 5px; font-weight: bold;")
                launch_btn.clicked.connect(lambda checked, p=profile: self.launch_single_profile(p, "Facebook Login & Home", ""))
            self.table.setCellWidget(row_idx, 5, launch_btn)

            # Delete Button
            del_btn = QPushButton("🗑️")
            del_btn.setProperty("class", "DangerAction")
            del_btn.setStyleSheet("background-color: #EF4444; color: white; border-radius: 4px; padding: 5px;")
            del_btn.clicked.connect(lambda checked, pid=profile['id']: self.delete_profile_handler(pid))
            self.table.setCellWidget(row_idx, 6, del_btn)


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
        reply = QMessageBox.question(self, 'Confirm Delete',
                                     'Are you sure you want to completely delete all selected profiles? Data and local folders will be lost permanently.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            deleted = 0
            base_dir = os.path.dirname(os.path.abspath(__file__))
            profiles = get_all_profiles()

            ids_to_stop = []

            for row in range(self.table.rowCount()):
                chk_widget = self.table.cellWidget(row, 0)
                if chk_widget:
                    checkbox = chk_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        profile_id = checkbox.property("profile_id")
                        ids_to_stop.append(profile_id)

                        # Find Account ID to delete folder
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

            # Stop any running instances that were deleted
            if ids_to_stop:
                 stop_all_selected(ids_to_stop, self.threadpool)

            if deleted > 0:
                self.load_profiles_into_table()
                self.populate_account_picker()
                QMessageBox.information(self, "Profiles Deleted", f"Permanently deleted {deleted} profiles and their folders.")

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

    def on_task_type_changed(self, text):
        if text == "Custom URL":
            self.custom_url_input.show()
        else:
            self.custom_url_input.hide()

    def toggle_all_table_accounts(self, state):
        target_state = Qt.CheckState(state)
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setCheckState(target_state)

    def import_profiles_from_txt(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Accounts Text File", "", "Text Files (*.txt)", options=options)

        if file_path:
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

        if file_path:
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

        if folder_path:
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
        reply = QMessageBox.question(self, 'Confirm Delete',
                                     'Are you sure you want to delete this profile? Data and local folder will be lost permanently.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            stop_all_selected([profile_id], self.threadpool)
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
                            worker = AccountMonitorWorker(p)
                            worker.signals.finished.connect(self.on_browser_closed)
                            worker.signals.error.connect(self.on_browser_error)
                            self.threadpool.start(worker)
                            launched += 1
                            break
        if launched > 0:
            self.load_profiles_into_table() # Trigger Running Guard UI updates immediately
            QMessageBox.information(self, "Status Check Started", f"Queued {launched} accounts for Auto-Login & Status Check.\nThe table will update automatically.")
        else:
            QMessageBox.warning(self, "No Selection", "Please select at least one account.")

    def launch_selected_profiles(self):
        task_type = self.task_selector.currentText()
        custom_url = self.custom_url_input.text().strip()

        if task_type == "Custom URL" and not custom_url:
            QMessageBox.warning(self, "Validation Error", "Please enter a Custom URL.")
            return

        profiles = get_all_profiles() # Fetch once for efficiency
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                checkbox = chk_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    profile_id = checkbox.property("profile_id")
                    for p in profiles:
                        if p['id'] == profile_id:
                            self.launch_single_profile(p, task_type, custom_url)
                            break

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
