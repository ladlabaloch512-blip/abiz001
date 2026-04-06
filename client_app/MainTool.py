import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox

# Fix for undetected_chromedriver import error (ModuleNotFoundError: No module named 'distutils')
import setuptools

# Add parent directory to sys.path so we can import shared_logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared_logic.utils import get_app_dir
from core.config import init_config
from core.database import init_db
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # 1. Base Resolution
    app_dir = get_app_dir()

    # 2. Remote Config (Pillar 1)
    config_manager = init_config(app_dir)

    # Kill-Switch (The Revoker) Check
    from core.security import get_hardware_uuid, verify_license
    hw_uuid = get_hardware_uuid()

    if config_manager.is_uuid_banned(hw_uuid):
        QMessageBox.critical(None, "Banned", "This system has been permanently banned from accessing the software.")
        sys.exit(1)

    # 3. Load Stylesheet Early for Beautiful Dialogs
    qss_path = os.path.join(app_dir, 'styles.qss')
    if os.path.exists(qss_path):
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    else:
        # Fallback dark theme injected directly if file is missing
        app.setStyleSheet("QMainWindow { background-color: #0B0E11; } QMessageBox { background-color: #15191E; color: white; }")

    # 4. License Check & Industrial Locked Screen
    license_path = os.path.join(app_dir, 'license.dat')
    if not verify_license(hw_uuid, license_path):
        from ui.widgets import LockedScreen
        locked_window = LockedScreen(hw_uuid, config_manager.get('branding.whatsapp_link', ''))
        locked_window.show()
        sys.exit(app.exec())

    # 5. Database Setup (Pillar 1/2)
    try:
        init_db(app_dir)
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"Fatal DB Error: {e}")
        sys.exit(1)

    # 6. UI Launch
    window = MainWindow(app_dir)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
