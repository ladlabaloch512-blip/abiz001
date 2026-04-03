import sys
import os
from datetime import datetime

# Add parent directory to path so we can import shared_logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from shared_logic.security import generate_license_data

# Keygen Modern Stylesheet
KEYGEN_QSS = """
QWidget {
    background-color: #2D3139;
    color: #FFFFFF;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
QLabel {
    font-size: 13px;
    font-weight: bold;
    color: #A0AABF;
}
QLineEdit, QDateEdit {
    background-color: #15191E;
    border: 1px solid #4B5563;
    border-radius: 5px;
    padding: 8px;
    color: #FFFFFF;
    font-size: 14px;
}
QLineEdit:focus, QDateEdit:focus {
    border: 1px solid #6366F1;
}
QPushButton {
    background-color: #6366F1;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 10px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #4F46E5;
}
QPushButton:pressed {
    background-color: #4338CA;
}
"""

class KeyGenApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Developer Admin Tool - Keygen')
        self.resize(550, 300)
        self.setStyleSheet(KEYGEN_QSS)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("Client License Generator")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; color: #FFFFFF; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # UUID Input
        uuid_label = QLabel("Client Hardware UUID:")
        self.uuid_input = QLineEdit()
        self.uuid_input.setPlaceholderText("Enter Client UUID here...")
        layout.addWidget(uuid_label)
        layout.addWidget(self.uuid_input)

        # Expiry Date Input
        date_label = QLabel("License Expiry Date:")
        self.expiry_date_edit = QDateEdit()
        # Set default expiry to 1 month from now
        self.expiry_date_edit.setDate(QDate.currentDate().addMonths(1))
        self.expiry_date_edit.setCalendarPopup(True)
        self.expiry_date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(date_label)
        layout.addWidget(self.expiry_date_edit)

        layout.addStretch()

        # Generate Button
        self.generate_btn = QPushButton("Generate & Save License")
        self.generate_btn.clicked.connect(self.generate_license)
        self.generate_btn.setMinimumHeight(45)
        layout.addWidget(self.generate_btn)

        self.setLayout(layout)

    def generate_license(self):
        client_uuid = self.uuid_input.text().strip()
        if not client_uuid:
            QMessageBox.warning(self, "Error", "Please enter a valid Client UUID.")
            return

        expiry_date_str = self.expiry_date_edit.date().toString("yyyy-MM-dd")

        # Open Save As dialog
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(self, "Save License File", "license.dat", "Data Files (*.dat)", options=options)

        if file_path:
            try:
                encrypted_data = generate_license_data(client_uuid, expiry_date_str)
                with open(file_path, 'wb') as f:
                    f.write(encrypted_data)
                QMessageBox.information(self, "Success", f"License generated! Expiry: {expiry_date_str}\nSaved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate license file:\n{e}")

if __name__ == '__main__':
    if not os.environ.get('DISPLAY'):
        print("Warning: Running without X server display. GUI will not be visible.")

    app = QApplication(sys.argv)
    ex = KeyGenApp()
    ex.show()
    sys.exit(app.exec())
