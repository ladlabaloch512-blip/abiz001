import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMenu, QStackedWidget,
                             QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QThreadPool, pyqtSlot
from ui.widgets import HardwareMonitorWidget
from core import config
from core.database import get_all_profiles, update_profile_status
from services.task_runner import BrowserTaskWorker, SequentialManager, stop_browser, ACTIVE_LAUNCHERS
from services.profile_logic import ProfileService

# ==========================================
# PILLAR 6 & 7: RIBBON UI & DASHBOARD
# ==========================================

class MainWindow(QMainWindow):
    def __init__(self, app_dir: str):
        super().__init__()
        self.app_dir = app_dir
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(200)
        self.sequential_manager = None
        self.profile_service = ProfileService(self, self.app_dir)

        # Integration with Step 1 Branding
        tool_name = config.app_config.get("branding.tool_name", "FB Multi-Account Manager")
        self.setWindowTitle(tool_name)
        self.resize(1200, 800)

        self._init_ui()
        self.load_table_data()

    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._build_sidebar()

        self.content_area = QWidget()
        self.content_area.setObjectName("ContentArea")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_area, 1)

        # Screens
        self.dashboard_screen = QWidget()
        self.settings_screen = QWidget()

        self._build_dashboard()
        self._build_settings()

        self.stacked_widget.addWidget(self.dashboard_screen)
        self.stacked_widget.addWidget(self.settings_screen)

    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        layout = QVBoxLayout(self.sidebar)

        # HW Monitor (Pillar 7)
        self.hw_monitor = HardwareMonitorWidget()
        layout.addWidget(self.hw_monitor)

        layout.addStretch()

        # Navigation
        btn_dash = QPushButton("📊 Dashboard")
        btn_dash.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_msg = QPushButton("💬 Messenger Hub")
        # Placeholder for full messenger hub view, for now it can trigger the bulk dispatch
        btn_msg.clicked.connect(lambda: QMessageBox.information(self, "Hub", "Use the 'Quick Actions -> Messenger Pulse' ribbon to dispatch tasks."))
        btn_set = QPushButton("⚙️ Settings")
        btn_set.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout.addWidget(btn_dash)
        layout.addWidget(btn_msg)
        layout.addWidget(btn_set)

    def _build_dashboard(self):
        layout = QVBoxLayout(self.dashboard_screen)
        layout.setContentsMargins(15, 15, 15, 15)

        # 1. Glass-morphism Dashboard Control Center (VBox)
        ribbon_frame = QFrame()
        ribbon_frame.setObjectName("DashboardRibbon")
        ribbon_layout = QVBoxLayout(ribbon_frame)
        ribbon_layout.setSpacing(10)

        # Header for the ribbon
        ribbon_header = QLabel("Dashboard Control Center")
        ribbon_header.setStyleSheet("font-weight: bold; font-size: 16px; color: #00E5FF; padding-bottom: 5px;")
        ribbon_layout.addWidget(ribbon_header)

        # Inner layout for buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        main_btn_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #0F172A);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px 15px;
                font-weight: bold;
                color: #F8FAFC;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #293850, stop:1 #1E293B);
                border: 1px solid rgba(0, 229, 255, 0.4);
                margin-top: -2px;
                margin-bottom: 2px;
            }
        """

        # 1. 🚀 Quick Actions
        btn_actions = QPushButton("🚀 Actions ▾")
        btn_actions.setStyleSheet(main_btn_style)
        menu_actions = QMenu(btn_actions)
        menu_actions.addAction("🔄 Auto Login (Any Sequence)").triggered.connect(lambda: self._bulk_launch(sequential=True))
        menu_actions.addAction("🚀 Bulk Launch (All-At-Once)").triggered.connect(lambda: self._bulk_launch(sequential=False))
        menu_actions.addAction("🛑 Bulk Stop All").triggered.connect(self._bulk_stop)

        menu_actions.addSeparator()
        # Hooks for Phase 2: Messenger Pulse
        msg_menu = menu_actions.addMenu("💬 Bulk Messenger Pulse")
        msg_menu.addAction("Send One-by-One").triggered.connect(lambda: self._dispatch_messenger_pulse("One-by-One"))
        msg_menu.addAction("Send Batch").triggered.connect(lambda: self._dispatch_messenger_pulse("Batch"))
        msg_menu.addAction("Send All").triggered.connect(lambda: self._dispatch_messenger_pulse("All"))

        btn_actions.setMenu(menu_actions)

        # 2. 📂 Migration Menu
        btn_data = QPushButton("📂 Migration ▾")
        btn_data.setStyleSheet(main_btn_style)
        menu_data = QMenu(btn_data)
        menu_data.addAction("📥 Import via Backup (ZIP)").triggered.connect(self.profile_service.execute_import_backup)
        menu_data.addAction("📤 Export Selected (ZIP)").triggered.connect(lambda: self.profile_service.execute_bulk_export(self._get_selected_ids()))
        menu_data.addAction("📄 TXT Import").triggered.connect(self.profile_service.import_profiles_from_txt)
        menu_data.addSeparator()
        menu_data.addAction("🔗 Connect Existing Profile Folders").triggered.connect(self.profile_service.connect_existing_profiles)
        btn_data.setMenu(menu_data)

        # 3. 🍪 Session Management Menu
        btn_session = QPushButton("🍪 Session ▾")
        btn_session.setStyleSheet(main_btn_style)
        menu_session = QMenu(btn_session)
        menu_session.addAction("📁 Import Cookie Folder").triggered.connect(self.profile_service.import_via_cookies)
        menu_session.addAction("📤 Bulk Export to JSON").triggered.connect(lambda: self.profile_service.execute_bulk_export(self._get_selected_ids(), json_only=True))
        menu_session.addAction("📥 Bulk Import from JSON Archive").triggered.connect(self.profile_service.bulk_import_from_json_archive)
        btn_session.setMenu(menu_session)

        # 4. ⚙️ Tools Menu
        btn_tools = QPushButton("⚙️ Tools ▾")
        btn_tools.setStyleSheet(main_btn_style)
        menu_tools = QMenu(btn_tools)
        menu_tools.addAction("➕ Bulk Empty Create").triggered.connect(self.profile_service.bulk_empty_create)
        menu_tools.addAction("🗑️ Physical Data Wipe").triggered.connect(lambda: self.profile_service.execute_bulk_delete(self._get_selected_ids()))
        menu_tools.addAction("🧹 Clear Junk (Keep Cookies)").triggered.connect(self.profile_service.execute_disk_cleanup)
        menu_tools.addSeparator()
        menu_tools.addAction("👥 Update Group").triggered.connect(lambda: self.profile_service.execute_bulk_group_update(self._get_selected_ids()))
        menu_tools.addAction("➕ Create Group").triggered.connect(self.profile_service.add_new_group)
        menu_tools.addAction("🗑️ Delete Group").triggered.connect(lambda: self.profile_service.delete_selected_group("TBD")) # Fixed later via sidebar
        btn_tools.setMenu(menu_tools)

        ribbon_layout.addWidget(btn_actions)
        ribbon_layout.addWidget(btn_data)
        ribbon_layout.addWidget(btn_session)
        ribbon_layout.addWidget(btn_tools)
        ribbon_layout.addStretch()

        layout.addWidget(ribbon_frame)

        # 2. Modern Account Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)

        # Add Select All Checkbox to Header
        self.select_all_chk = QCheckBox("[x]")
        self.select_all_chk.stateChanged.connect(self._toggle_all_rows)

        self.table.setHorizontalHeaderLabels(["", "Profile Name", "Status", "Group", "Proxy", "Email", "⚙️ Manage"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        # Inject the Select All Checkbox directly over the first header
        layout.addWidget(self.select_all_chk)
        layout.addWidget(self.table)

    def _build_settings(self):
        layout = QVBoxLayout(self.settings_screen)

        title = QLabel("System Settings & Cloud Sync")
        title.setStyleSheet("font-size: 24px; color: white;")
        layout.addWidget(title)

        # Google Sync Framework (Pillar 5)
        sync_frame = QFrame()
        sync_layout = QVBoxLayout(sync_frame)
        sync_lbl = QLabel("Private Google Drive Sync Framework")
        btn_sync = QPushButton("🔐 Link My Google Account")
        btn_sync.setStyleSheet("background-color: #4285F4; color: white; padding: 10px; border-radius: 8px;")

        from services.sync_service import GoogleDriveSyncService
        self.sync_service = GoogleDriveSyncService(self.app_dir)
        btn_sync.clicked.connect(lambda: self.sync_service.authenticate(self))
        sync_layout.addWidget(sync_lbl)
        sync_layout.addWidget(btn_sync)
        layout.addWidget(sync_frame)

        # Discord Webhook Framework
        discord_frame = QFrame()
        discord_layout = QVBoxLayout(discord_frame)
        discord_lbl = QLabel("Discord Webhook (Optional Notifications)")

        discord_input_layout = QHBoxLayout()
        from PyQt6.QtWidgets import QLineEdit
        self.discord_input = QLineEdit()
        self.discord_input.setPlaceholderText("Enter Discord Webhook URL...")
        btn_save_webhook = QPushButton("💾 Save Webhook")
        btn_save_webhook.setStyleSheet("background-color: #5865F2; color: white; border-radius: 8px;")
        btn_save_webhook.clicked.connect(lambda: QMessageBox.information(self, "Saved", "Discord webhook configured for Messenger Pulse."))

        discord_input_layout.addWidget(self.discord_input)
        discord_input_layout.addWidget(btn_save_webhook)
        discord_layout.addWidget(discord_lbl)
        discord_layout.addLayout(discord_input_layout)
        layout.addWidget(discord_frame)

        # Branding
        support_number = config.app_config.get("branding.support_number", "+923490098654")
        lbl_support = QLabel(f"For Support Contact WhatsApp: {support_number}")
        lbl_support.setStyleSheet("color: #9CA3AF; margin-top: 20px;")
        layout.addWidget(lbl_support)

        layout.addStretch()

    def load_table_data(self):
        self.table.setRowCount(0)
        profiles = get_all_profiles(self.app_dir)

        for p in profiles:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox
            chk = QCheckBox()
            chk.setProperty("profile_id", p['id'])
            chk.setProperty("profile_data", p)
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0,0,0,0)
            self.table.setCellWidget(row, 0, chk_widget)

            self.table.setItem(row, 1, QTableWidgetItem(p['profile_name']))
            self.table.setItem(row, 2, QTableWidgetItem(p.get('status', 'Ready')))
            self.table.setItem(row, 3, QTableWidgetItem(p.get('group_name', 'Default')))
            self.table.setItem(row, 4, QTableWidgetItem(p.get('account_proxy', 'None')))
            self.table.setItem(row, 5, QTableWidgetItem(p.get('email', 'None')))

            # Row Manage Button
            btn_manage = QPushButton("⚙️ Manage")
            menu = QMenu(btn_manage)

            menu.addAction("🔑 Auto-Login This ID").triggered.connect(lambda checked, prof=p: self._launch_single(prof, task="Auto-Login"))
            menu.addAction("🚀 Launch Profile (Blank)").triggered.connect(lambda checked, prof=p: self._launch_single(prof, task="Manual"))
            menu.addSeparator()
            menu.addAction("🍪 Export JSON Cookies").triggered.connect(lambda checked, prof=p: self.profile_service.export_single_cookie(prof))
            menu.addAction("📥 Import JSON File").triggered.connect(lambda checked, prof=p: self.profile_service.import_single_cookie(prof))
            menu.addSeparator()
            menu.addAction("🗑️ Delete Data").triggered.connect(lambda checked, pid=p['id']: self.profile_service.execute_bulk_delete([pid]))
            btn_manage.setMenu(menu)

            self.table.setCellWidget(row, 6, btn_manage)

    # --- Routing & Task Sync ---

    def _toggle_all_rows(self, state):
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk:
                    chk.setChecked(state == Qt.CheckState.Checked.value)

    def _get_selected_profiles(self):
        selected = []
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    selected.append(chk.property("profile_data"))
        return selected

    def _get_selected_ids(self):
        return [p['id'] for p in self._get_selected_profiles()]

    def _launch_single(self, profile, task="Auto-Login"):
        worker = BrowserTaskWorker(profile, self.app_dir, task_type=task)
        worker.signals.status_update.connect(self.on_worker_status_update)
        self.threadpool.start(worker)

    def _bulk_launch(self, sequential=False):
        profiles = self._get_selected_profiles()
        if not profiles:
            QMessageBox.warning(self, "No Selection", "Select at least one profile.")
            return

        if sequential:
            self.sequential_manager = SequentialManager(profiles, self.app_dir, self.threadpool)
            self.sequential_manager.queue_completed.connect(lambda: QMessageBox.information(self, "Done", "Sequential queue finished."))

            # Map the inner worker signals to the UI synchronously
            def _create_browser_worker(p):
                w = BrowserTaskWorker(p, self.app_dir)
                w.signals.status_update.connect(self.on_worker_status_update)
                return w

            self.sequential_manager._create_worker = _create_browser_worker
            self.sequential_manager.start()
            QMessageBox.information(self, "Started", "Sequential Launch Started.")
        else:
            for p in profiles:
                self._launch_single(p)

    def _bulk_stop(self):
        for p in self._get_selected_profiles():
            pid = p['id']
            if pid in ACTIVE_LAUNCHERS:
                stop_browser(pid)
                update_profile_status(self.app_dir, pid, "Ready")
                self.on_worker_status_update(pid, "Ready")

    def _dispatch_messenger_pulse(self, mode: str):
        profiles = self._get_selected_profiles()
        if not profiles:
            QMessageBox.warning(self, "No Selection", "Please select at least one account to run the Messenger Pulse.")
            return

        webhook_url = getattr(self, 'discord_input', None)
        url_text = webhook_url.text().strip() if webhook_url else ""

        # In a real implementation we would import start_messenger_pulse and execute it:
        from automation.messenger_pulse import start_messenger_pulse
        start_messenger_pulse(profiles, mode, self.app_dir, self.threadpool, url_text)

        QMessageBox.information(self, "Messenger Pulse Started", f"Messenger dispatched in {mode} mode.\nDiscord Webhook: {'Active' if url_text else 'Inactive'}")

    @pyqtSlot(int, str)
    def on_worker_status_update(self, profile_id, status_str):
        # Find row and update UI synchronously
        for row in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk and chk.property("profile_id") == profile_id:
                    self.table.setItem(row, 2, QTableWidgetItem(status_str))
                    break
