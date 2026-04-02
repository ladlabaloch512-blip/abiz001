import sys
import customtkinter as ctk
from licensing import verify_license
from ui_main import MainDashboard
from database import DatabaseManager

# ------------------------------------------------------------------------------
# Core Application Entry Point
# 1. Enforces Hardware Activation Lock
# 2. Initializes Thread-Safe DB
# 3. Boots Main Dashboard UI
# ------------------------------------------------------------------------------

def show_activation_error():
    """Displays a simple lock screen if the AES hardware token is missing or invalid."""
    app = ctk.CTk()
    app.title("System Locked")
    app.geometry("500x300")
    app.eval('tk::PlaceWindow . center')

    ctk.set_appearance_mode("dark")

    lbl = ctk.CTkLabel(
        app,
        text="🔒 Activation Required",
        font=("Segoe UI Variable Display", 24, "bold"),
        text_color="#EF4444"
    )
    lbl.pack(pady=(60, 20))

    sub = ctk.CTkLabel(
        app,
        text="Invalid or missing hardware license.\nPlease use the Developer Portal to generate an AES token\nand save it as 'license.key' in the root directory.",
        font=("Segoe UI Variable Display", 14)
    )
    sub.pack()

    btn = ctk.CTkButton(app, text="Exit", command=sys.exit, fg_color="#334155", hover_color="#475569")
    btn.pack(pady=30)

    app.mainloop()

def main():
    # 1. Hardware Security Check
    if not verify_license():
        show_activation_error()
        return

    # 2. Database Initialization
    # Creates SQLite file and schema dynamically if it doesn't exist
    db_manager = DatabaseManager()

    # 3. Boot Core Application
    app = MainDashboard(db=db_manager)
    app.mainloop()

if __name__ == "__main__":
    main()
