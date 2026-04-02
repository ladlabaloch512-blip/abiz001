import customtkinter as ctk
import pyperclip
from PIL import Image
from licensing import generate_license_token

# ------------------------------------------------------------------------------
# Developer Keygen Tool (Tier-1 Windows 11 Fluent Design Edition)
# ------------------------------------------------------------------------------

# --- Fluent Design System Constants ---
APP_BG_COLOR = "#101216"          # Midnight Blue-Gray
CARD_BG_COLOR = "#1C1E26"         # Soft Slate for cards
ACCENT_COLOR = "#3A86FF"          # Cyan Blue
ACCENT_HOVER = "#2A6EDB"          # Darker Cyan Blue for hover
TEXT_COLOR_MAIN = "#FFFFFF"
TEXT_COLOR_MUTED = "#8B95A5"
BORDER_COLOR = "#2A2E39"          # Subtle border for 3D elevation simulation
SUCCESS_COLOR = "#10B981"         # Emerald Green
ERROR_COLOR = "#EF4444"           # Red

FONT_HEADER = ("Segoe UI Variable Display", 26, "bold")
FONT_SUBHEADER = ("Segoe UI Variable Display", 14)
FONT_LABEL = ("Segoe UI Variable Display", 13, "bold")
FONT_INPUT = ("Segoe UI Variable Display", 14)
CORNER_RADIUS = 12

class KeygenApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Developer Activation Portal")
        self.geometry("750x550")
        self.minsize(600, 450) # Set minimum size
        self.resizable(True, True) # Allow resizing
        self.configure(fg_color=APP_BG_COLOR)

        # Center the window on screen
        self.eval('tk::PlaceWindow . center')

        # Grid weight configuration to keep content centered when resized
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.setup_ui()

    def setup_ui(self):
        # --- Main Central Wrapper ---
        # This frame acts as the main content area that stays centered
        self.main_wrapper = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_wrapper.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)

        # Configure wrapper grid
        self.main_wrapper.grid_columnconfigure(0, weight=1)
        self.main_wrapper.grid_rowconfigure(0, weight=0) # Header
        self.main_wrapper.grid_rowconfigure(1, weight=1) # Card

        # --- Header Area ---
        self.header_frame = ctk.CTkFrame(self.main_wrapper, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text="Software Activation",
            font=FONT_HEADER,
            text_color=TEXT_COLOR_MAIN,
            anchor="w"
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_subtitle = ctk.CTkLabel(
            self.header_frame,
            text="Enter hardware details to issue a secure AES offline token.",
            font=FONT_SUBHEADER,
            text_color=TEXT_COLOR_MUTED,
            anchor="w"
        )
        self.lbl_subtitle.pack(anchor="w")

        # --- Central Floating Card (Fluent Style) ---
        self.card = ctk.CTkFrame(
            self.main_wrapper,
            fg_color=CARD_BG_COLOR,
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=BORDER_COLOR
        )
        self.card.grid(row=1, column=0, sticky="nsew")

        # Keep card contents organized
        self.card.grid_columnconfigure(0, weight=1)

        # 1. Hardware UUID Input Section
        self.lbl_uuid = ctk.CTkLabel(
            self.card,
            text="🆔 Client Hardware UUID",
            font=FONT_LABEL,
            text_color=TEXT_COLOR_MAIN
        )
        self.lbl_uuid.grid(row=0, column=0, sticky="w", padx=30, pady=(30, 5))

        self.entry_uuid = ctk.CTkEntry(
            self.card,
            placeholder_text="Enter unique system identifier...",
            height=45,
            font=FONT_INPUT,
            corner_radius=CORNER_RADIUS,
            fg_color=APP_BG_COLOR,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR_MAIN,
            placeholder_text_color=TEXT_COLOR_MUTED
        )
        self.entry_uuid.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))

        # 2. Generate Action Button
        self.btn_generate = ctk.CTkButton(
            self.card,
            text="⚡ Generate Secure Token",
            command=self.generate_token,
            height=50,
            font=("Segoe UI Variable Display", 15, "bold"),
            corner_radius=CORNER_RADIUS,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF"
        )
        self.btn_generate.grid(row=2, column=0, sticky="ew", padx=30, pady=(10, 30))

        # 3. Output Token Section
        self.lbl_output = ctk.CTkLabel(
            self.card,
            text="🔑 Generated AES Token",
            font=FONT_LABEL,
            text_color=TEXT_COLOR_MAIN
        )
        self.lbl_output.grid(row=3, column=0, sticky="w", padx=30, pady=(0, 5))

        self.textbox_token = ctk.CTkTextbox(
            self.card,
            height=90,
            font=("Consolas", 12), # Monospace for tokens
            corner_radius=CORNER_RADIUS,
            fg_color=APP_BG_COLOR,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=ACCENT_COLOR,
            wrap="word"
        )
        self.textbox_token.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 20))
        self.textbox_token.insert("1.0", "Awaiting input generation...")
        self.textbox_token.configure(state="disabled")

        # 4. Footer Actions (Copy Button)
        self.footer_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.footer_frame.grid(row=5, column=0, sticky="ew", padx=30, pady=(0, 30))
        self.footer_frame.grid_columnconfigure(0, weight=1)

        self.btn_copy = ctk.CTkButton(
            self.footer_frame,
            text="📋 Copy to Clipboard",
            command=self.copy_to_clipboard,
            width=200,
            height=40,
            font=FONT_INPUT,
            corner_radius=CORNER_RADIUS,
            fg_color=BORDER_COLOR,
            hover_color="#3A404F",
            text_color=TEXT_COLOR_MAIN
        )
        self.btn_copy.grid(row=0, column=0, sticky="e")

    def generate_token(self):
        hardware_id = self.entry_uuid.get().strip()

        if not hardware_id:
            self.show_error("Please enter a valid Hardware UUID.")
            return

        try:
            token = generate_license_token(hardware_id)

            self.textbox_token.configure(state="normal")
            self.textbox_token.delete("1.0", "end")
            self.textbox_token.insert("1.0", token)
            self.textbox_token.configure(text_color=SUCCESS_COLOR) # Green for success
            self.textbox_token.configure(state="disabled")

        except Exception as e:
            self.show_error(f"Error generating token: {str(e)}")

    def copy_to_clipboard(self):
        token = self.textbox_token.get("1.0", "end").strip()
        if token and not token.startswith("ERROR") and not token.startswith("Awaiting"):
            pyperclip.copy(token)

            # Button feedback animation
            original_text = self.btn_copy.cget("text")
            original_color = self.btn_copy.cget("fg_color")

            self.btn_copy.configure(text="✔️ Copied!", fg_color=SUCCESS_COLOR)
            self.after(2000, lambda: self.btn_copy.configure(text=original_text, fg_color=original_color))

    def show_error(self, message):
        self.textbox_token.configure(state="normal")
        self.textbox_token.delete("1.0", "end")
        self.textbox_token.insert("1.0", f"ERROR: {message}")
        self.textbox_token.configure(text_color=ERROR_COLOR)
        self.textbox_token.configure(state="disabled")

if __name__ == "__main__":
    app = KeygenApp()
    app.mainloop()