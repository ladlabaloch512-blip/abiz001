import sys
import queue
import customtkinter as ctk
from database import DatabaseManager
from automation import AutomationEngine, AutomationTask
from licensing import verify_license

# --- Elite Deep Charcoal Theme Constants ---
APP_BG = "#0B0E11"        # Midnight Deep Charcoal
CARD_BG = "#15191E"       # Dark Obsidian
BORDER_C = "#2D3139"      # Border Gray
ACCENT = "#6366F1"        # Vibrant Indigo
ACCENT_H = "#4F46E5"      # Indigo Hover
SUCCESS = "#10B981"       # Emerald
ERROR = "#EF4444"         # Rose Red
TEXT_M = "#FFFFFF"        # Main Text
TEXT_S = "#9CA3AF"        # Sub/Muted Text

FONT_H1 = ("Segoe UI Variable Display", 28, "bold")
FONT_H2 = ("Segoe UI Variable Display", 18, "bold")
FONT_BODY = ("Segoe UI Variable Display", 14)
FONT_MONO = ("Consolas", 12)
RADIUS = 12

class MainDashboard(ctk.CTk):
    def __init__(self, db: DatabaseManager):
        super().__init__()

        self.db = db
        self.ui_queue = queue.Queue()
        self.engine = AutomationEngine(self.db, self.ui_queue)

        self.title("Enterprise E-Commerce Automation Suite")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=APP_BG)

        # Center Window
        self.eval('tk::PlaceWindow . center')

        # Grid config: 1 row, 2 columns (Sidebar, Main Content)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.build_sidebar()
        self.build_main_content()
        self.build_log_panel()

        # Start Queue Poller
        self.poll_queue()

        # Load initial tab
        self.show_dashboard()

    # -------------------------------------------------------------------------
    # 1. LAYOUT BUILDING
    # -------------------------------------------------------------------------

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0, width=220)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        # Logo / Title
        self.logo_lbl = ctk.CTkLabel(
            self.sidebar, text="⚡ QUANTUM", font=FONT_H1, text_color=TEXT_M
        )
        self.logo_lbl.grid(row=0, column=0, padx=20, pady=(30, 40))

        # Navigation Buttons
        self.nav_btns = {}
        nav_items = [
            ("Dashboard", "🏠", self.show_dashboard),
            ("Accounts", "👥", self.show_accounts),
            ("Broadcaster", "🛒", self.show_broadcaster),
            ("Inbox", "📩", self.show_inbox)
        ]

        for i, (name, icon, cmd) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {name}",
                command=cmd,
                anchor="w",
                fg_color="transparent",
                hover_color=APP_BG,
                text_color=TEXT_S,
                font=FONT_BODY,
                height=45,
                corner_radius=8
            )
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=5)
            self.nav_btns[name] = btn

    def build_main_content(self):
        # Container for the different tab frames
        self.main_container = ctk.CTkFrame(self, fg_color=APP_BG, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=25, pady=(25, 10))
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Initialize Frames
        self.frames = {
            "Dashboard": self.create_dashboard_frame(),
            "Accounts": self.create_accounts_frame(),
            "Broadcaster": self.create_broadcaster_frame(),
            "Inbox": self.create_inbox_frame()
        }

    def build_log_panel(self):
        # Terminal-style retractable log panel at the bottom
        self.log_panel = ctk.CTkFrame(self, height=150, fg_color=CARD_BG, corner_radius=0, border_color=BORDER_C, border_width=1)
        self.log_panel.grid(row=1, column=1, sticky="sew")
        self.log_panel.grid_rowconfigure(1, weight=1)
        self.log_panel.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.log_panel, fg_color="transparent", height=30)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        lbl = ctk.CTkLabel(header, text="📜 Live Event Stream", font=("Segoe UI Variable Display", 12, "bold"), text_color=TEXT_S)
        lbl.pack(side="left")

        self.log_text = ctk.CTkTextbox(
            self.log_panel,
            fg_color=APP_BG,
            text_color=TEXT_M,
            font=FONT_MONO,
            corner_radius=0
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0,2))
        self.log_text.insert("1.0", "[SYSTEM] Engine Initialized. Ready.\n")
        self.log_text.configure(state="disabled")

    # -------------------------------------------------------------------------
    # 2. NAVIGATION & TAB LOGIC
    # -------------------------------------------------------------------------

    def switch_tab(self, tab_name):
        # Reset button colors
        for name, btn in self.nav_btns.items():
            btn.configure(fg_color="transparent", text_color=TEXT_S)
        # Highlight active
        self.nav_btns[tab_name].configure(fg_color=ACCENT, text_color=TEXT_M, hover_color=ACCENT_H)

        # Hide all frames, show target
        for name, frame in self.frames.items():
            frame.grid_forget()
        self.frames[tab_name].grid(row=0, column=0, sticky="nsew")

    def show_dashboard(self): self.switch_tab("Dashboard")
    def show_accounts(self):
        self.switch_tab("Accounts")
        self.refresh_accounts_list()
    def show_broadcaster(self): self.switch_tab("Broadcaster")
    def show_inbox(self): self.switch_tab("Inbox")

    # -------------------------------------------------------------------------
    # 3. FRAME BUILDERS
    # -------------------------------------------------------------------------

    def create_dashboard_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")

        lbl = ctk.CTkLabel(frame, text="System Overview", font=FONT_H1, text_color=TEXT_M)
        lbl.pack(anchor="w", pady=(0, 20))

        # Stat Cards Row
        stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
        stats_frame.pack(fill="x")

        self.lbl_tot_accs = self.create_stat_card(stats_frame, "Total Profiles", "0", 0)
        self.lbl_act_thrds = self.create_stat_card(stats_frame, "Active Threads", "0", 1)
        self.lbl_tasks_run = self.create_stat_card(stats_frame, "Tasks Completed", "0", 2)

        return frame

    def create_stat_card(self, parent, title, value, col):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=RADIUS, border_color=BORDER_C, border_width=1)
        card.grid(row=0, column=col, padx=(0, 15), sticky="ew")
        parent.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(card, text=title, font=FONT_BODY, text_color=TEXT_S).pack(pady=(15, 0), padx=20, anchor="w")
        val_lbl = ctk.CTkLabel(card, text=value, font=FONT_H1, text_color=TEXT_M)
        val_lbl.pack(pady=(0, 15), padx=20, anchor="w")
        return val_lbl

    def create_accounts_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Header
        head = ctk.CTkFrame(frame, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(head, text="👥 Profiles Manager", font=FONT_H2, text_color=TEXT_M).pack(side="left")

        btn_add = ctk.CTkButton(head, text="+ New Profile", command=self.add_dummy_profile, fg_color=ACCENT, hover_color=ACCENT_H, width=120)
        btn_add.pack(side="right")

        # Scrollable List
        self.acc_list = ctk.CTkScrollableFrame(frame, fg_color=CARD_BG, corner_radius=RADIUS, border_color=BORDER_C, border_width=1)
        self.acc_list.grid(row=1, column=0, sticky="nsew")

        return frame

    def create_broadcaster_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="🛒 Marketplace Broadcaster", font=FONT_H2, text_color=TEXT_M).grid(row=0, column=0, sticky="w", pady=(0, 20))

        form_card = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=RADIUS, border_color=BORDER_C, border_width=1)
        form_card.grid(row=1, column=0, sticky="ew", ipady=10)

        # Form Fields
        ctk.CTkLabel(form_card, text="Listing Title", font=FONT_BODY, text_color=TEXT_S).pack(anchor="w", padx=20, pady=(15, 5))
        self.entry_title = ctk.CTkEntry(form_card, placeholder_text="e.g., Vintage Leather Jacket", width=400, fg_color=APP_BG, border_color=BORDER_C)
        self.entry_title.pack(anchor="w", padx=20)

        ctk.CTkLabel(form_card, text="Price / Cost", font=FONT_BODY, text_color=TEXT_S).pack(anchor="w", padx=20, pady=(15, 5))
        self.entry_cost = ctk.CTkEntry(form_card, placeholder_text="e.g., 150", width=400, fg_color=APP_BG, border_color=BORDER_C)
        self.entry_cost.pack(anchor="w", padx=20)

        ctk.CTkLabel(form_card, text="Subject", font=FONT_BODY, text_color=TEXT_S).pack(anchor="w", padx=20, pady=(15, 5))
        self.entry_subject = ctk.CTkEntry(form_card, placeholder_text="e.g., Condition: New", width=400, fg_color=APP_BG, border_color=BORDER_C)
        self.entry_subject.pack(anchor="w", padx=20)

        ctk.CTkLabel(form_card, text="File Paths (Comma Separated)", font=FONT_BODY, text_color=TEXT_S).pack(anchor="w", padx=20, pady=(15, 5))
        self.entry_files = ctk.CTkEntry(form_card, placeholder_text="C:\\image1.png, C:\\image2.png", width=400, fg_color=APP_BG, border_color=BORDER_C)
        self.entry_files.pack(anchor="w", padx=20)

        # Profile Target
        ctk.CTkLabel(form_card, text="Target Profile ID (Leave empty for All)", font=FONT_BODY, text_color=TEXT_S).pack(anchor="w", padx=20, pady=(15, 5))
        self.entry_target = ctk.CTkEntry(form_card, placeholder_text="e.g., 1", width=400, fg_color=APP_BG, border_color=BORDER_C)
        self.entry_target.pack(anchor="w", padx=20)

        # Execute Action
        btn_launch = ctk.CTkButton(
            form_card, text="🚀 Launch Automation Queue",
            command=self.launch_form_automation,
            fg_color=SUCCESS, hover_color="#059669", font=("Segoe UI Variable Display", 14, "bold")
        )
        btn_launch.pack(anchor="w", padx=20, pady=(30, 20))

        return frame

    def create_inbox_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(frame, text="📩 Unified Inbox", font=FONT_H2, text_color=TEXT_M).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Left Pane: Threads
        left_pane = ctk.CTkScrollableFrame(frame, fg_color=CARD_BG, corner_radius=RADIUS, border_color=BORDER_C, border_width=1)
        left_pane.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(left_pane, text="Recent Threads", font=FONT_BODY, text_color=TEXT_S).pack(pady=10)
        # Dummy Threads
        for i in range(1, 6):
            btn = ctk.CTkButton(left_pane, text=f"Customer #{i}", fg_color=APP_BG, hover_color=BORDER_C, text_color=TEXT_M, height=40)
            btn.pack(fill="x", pady=2, padx=5)

        # Right Pane: Active Chat
        right_pane = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=RADIUS, border_color=BORDER_C, border_width=1)
        right_pane.grid(row=1, column=1, sticky="nsew")
        right_pane.grid_rowconfigure(0, weight=1)

        chat_box = ctk.CTkTextbox(right_pane, fg_color=APP_BG, text_color=TEXT_M, font=FONT_BODY, corner_radius=RADIUS)
        chat_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        chat_box.insert("end", "[System] Select a thread to view messages.")
        chat_box.configure(state="disabled")

        input_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.reply_entry = ctk.CTkEntry(input_frame, placeholder_text="Type your reply...", fg_color=APP_BG, border_color=BORDER_C)
        self.reply_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        send_btn = ctk.CTkButton(input_frame, text="Send", width=80, fg_color=ACCENT, hover_color=ACCENT_H, command=self.launch_inbox_reply)
        send_btn.grid(row=0, column=1)

        return frame

    # -------------------------------------------------------------------------
    # 4. LOGIC & AUTOMATION BINDINGS
    # -------------------------------------------------------------------------

    def refresh_accounts_list(self):
        """Clears and repopulates the accounts list based on DB."""
        for widget in self.acc_list.winfo_children():
            widget.destroy()

        profiles = self.db.get_all_profiles()
        self.lbl_tot_accs.configure(text=str(len(profiles)))

        for i, p in enumerate(profiles):
            row = ctk.CTkFrame(self.acc_list, fg_color=APP_BG, corner_radius=8, height=40)
            row.pack(fill="x", pady=2, padx=5)
            row.pack_propagate(False)

            # Simple green dot for visual status
            ctk.CTkLabel(row, text="🟢", text_color=SUCCESS).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"ID: {p['id']} - {p['profile_name']}", font=FONT_BODY, text_color=TEXT_M).pack(side="left")

            btn_check = ctk.CTkButton(
                row, text="Verify Session", width=100, height=28, fg_color=BORDER_C, hover_color="#3A404F",
                command=lambda pid=p['id'], pname=p['profile_name']: self.launch_auth_check(pid, pname)
            )
            btn_check.pack(side="right", padx=10)

    def add_dummy_profile(self):
        """Quickly adds a test profile to the DB."""
        count = len(self.db.get_all_profiles()) + 1
        self.db.add_profile(f"Profile_Alpha_{count}")
        self.refresh_accounts_list()
        self.write_log("System", "Success", f"Created Profile_Alpha_{count}")

    def launch_form_automation(self):
        """Builds tasks for all profiles to execute the generic form."""
        title = self.entry_title.get()
        cost = self.entry_cost.get()
        subject = self.entry_subject.get()
        files = self.entry_files.get()
        target = self.entry_target.get()

        if not title:
            self.write_log("System", "Error", "Form Title cannot be empty.")
            return

        profiles = self.db.get_all_profiles()
        if not profiles:
            self.write_log("System", "Error", "No profiles available. Add one in Accounts Tab.")
            return

        if target:
            try:
                target_id = int(target)
                profiles = [p for p in profiles if p['id'] == target_id]
            except ValueError:
                self.write_log("System", "Error", "Target Profile ID must be a number.")
                return

        tasks = []
        for p in profiles:
            task = AutomationTask(
                profile_id=p['id'],
                profile_name=p['profile_name'],
                task_type="fill_generic_form",
                payload={"title": title, "cost": cost, "subject": subject, "files": files}
            )
            tasks.append(task)

        self.engine.dispatch_tasks(tasks)
        self.write_log("System", "Info", f"Dispatched Form tasks to {len(tasks)} threads.")

    def launch_inbox_reply(self):
        """Dispatches a task to send a reply via the unified inbox."""
        reply_text = self.reply_entry.get()
        if not reply_text:
             self.write_log("System", "Error", "Reply text cannot be empty.")
             return

        profiles = self.db.get_all_profiles()
        if not profiles:
            self.write_log("System", "Error", "No profiles available for Inbox.")
            return

        # For this generic setup, send the reply using the first active profile as a target.
        # In a real scenario, this would be tied to the selected dummy thread.
        p = profiles[0]
        task = AutomationTask(
             profile_id=p['id'],
             profile_name=p['profile_name'],
             task_type="send_inbox_reply",
             payload={"reply": reply_text}
        )
        self.engine.dispatch_tasks([task])
        self.write_log("System", "Info", f"Dispatched Inbox Reply via {p['profile_name']}")

    def launch_auth_check(self, pid, pname):
        """Dispatches a single login check task."""
        task = AutomationTask(pid, pname, "check_login_status", {})
        self.engine.dispatch_tasks([task])
        self.write_log("System", "Info", f"Dispatched Auth Check for {pname}")

    # -------------------------------------------------------------------------
    # 5. QUEUE POLLING & LOGGING
    # -------------------------------------------------------------------------

    def write_log(self, source, status, msg):
        """Writes to the Terminal panel with coloring."""
        # Removed the buggy queue pop which discarded live events.

        color_tag = "normal"
        if status == "Success": color_tag = "success"
        elif status == "Error": color_tag = "error"
        elif status == "Running": color_tag = "running"
        elif status == "Info": color_tag = "info"

        log_str = f"[{source}] [{status}] {msg}\n"

        self.log_text.configure(state="normal")

        # Configure text colors via tags
        self.log_text.tag_config("success", foreground=SUCCESS)
        self.log_text.tag_config("error", foreground=ERROR)
        self.log_text.tag_config("running", foreground=ACCENT)
        self.log_text.tag_config("info", foreground=TEXT_M)
        self.log_text.tag_config("normal", foreground=TEXT_M)

        # Insert text and apply color tag
        self.log_text.insert("end", log_str, color_tag)
        # Scroll to bottom
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def poll_queue(self):
        """Regularly checks the threading queue for messages from the Selenium engine."""
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                self.write_log(msg['profile_name'], msg['status'], msg['message'])
        except queue.Empty:
            pass
        finally:
            self.after(100, self.poll_queue)
