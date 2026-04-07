import time
import random
import requests
from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal
from automation.browser_engine import ProfileLauncher
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Pre-defined CTA templates
CTA_TEMPLATES = [
    "Hi there! Thank you for your interest. Please contact our specialist directly at [PHONE NUMBER] to book your service immediately.",
    "Hello! Our team is ready to help. For the fastest response, give us a quick call at [PHONE NUMBER].",
    "Thanks for reaching out! We are currently running a special. Call [PHONE NUMBER] to claim your spot.",
    "Greetings! To secure your booking right away, our dispatch team is available at [PHONE NUMBER].",
    "Hi! We'd love to assist you. Please dial [PHONE NUMBER] so we can get you scheduled."
]

class MessengerSignals(QObject):
    status_update = pyqtSignal(int, str)
    finished = pyqtSignal(int)
    error = pyqtSignal(int, str)

class VisibleMessengerWorker(QRunnable):
    """
    Background worker that logs into a profile visibly, checks for messages,
    sends a predefined CTA reply to new leads, and triggers a Discord webhook if configured.
    """
    def __init__(self, profile_data: dict, app_dir: str, webhook_url: str = ""):
        super().__init__()
        self.profile = profile_data
        self.app_dir = app_dir
        self.webhook_url = webhook_url
        self.signals = MessengerSignals()

    @pyqtSlot()
    def run(self):
        profile_id = self.profile['id']
        account_id = self.profile['account_id']
        try:
            self.signals.status_update.emit(profile_id, "💬 Loading Messenger...")

            # Initialize ProfileLauncher
            self.launcher = ProfileLauncher(self.profile, self.app_dir)
            driver = self.launcher.launch()

            # Inject session to bypass hardware lock
            self.launcher.inject_portable_session()

            # Navigate directly to Marketplace Inbox
            driver.get("https://www.facebook.com/marketplace/inbox/")
            time.sleep(5)

            # Check if logged in
            if 'login' in driver.current_url.lower():
                self.signals.status_update.emit(profile_id, "❌ Not Logged In")
                return

            self.signals.status_update.emit(profile_id, "🔍 Scanning Inbox...")

            wait = WebDriverWait(driver, 10)
            try:
                # 1. Find the first conversation thread
                threads_xpath = "//div[@role='navigation']//a[contains(@href, '/messages/t/')]"
                threads = driver.find_elements(By.XPATH, threads_xpath)

                if not threads:
                    self.signals.status_update.emit(profile_id, "✅ Inbox Empty")
                    return

                # 2. Check the top thread
                top_thread = threads[0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", top_thread)
                time.sleep(1)

                top_thread.click()
                time.sleep(4)

                # 3. Analyze the chat history
                msg_rows = driver.find_elements(By.XPATH, "//div[@role='row']")
                if msg_rows:
                    last_row = msg_rows[-1]
                    if "You sent" not in last_row.get_attribute("aria-label") and "You replied" not in last_row.get_attribute("aria-label"):
                        self.signals.status_update.emit(profile_id, "✍️ Typing Reply...")

                        # 4. Send CTA
                        reply_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Message' and @role='textbox']")))
                        cta = random.choice(CTA_TEMPLATES)

                        actions = ActionChains(driver)
                        actions.move_to_element(reply_box).click().perform()
                        time.sleep(0.5)

                        for char in cta:
                            actions.send_keys(char).perform()
                            time.sleep(random.uniform(0.02, 0.06))

                        actions.send_keys(Keys.ENTER).perform()
                        time.sleep(2)

                        self.signals.status_update.emit(profile_id, "📩 Replied to Lead")

                        if self.webhook_url:
                            self._send_discord_notification(self.profile['profile_name'], "New lead secured and replied to!")
                    else:
                        self.signals.status_update.emit(profile_id, "✅ No New Leads")
                else:
                    self.signals.status_update.emit(profile_id, "✅ Chat Empty")

            except Exception as dom_err:
                print(f"[{account_id}] Messenger DOM Parse Error: {dom_err}")
                self.signals.status_update.emit(profile_id, "⚠️ UI Parse Error")

        except Exception as e:
            self.signals.error.emit(profile_id, str(e))
        finally:
            if hasattr(self, 'launcher') and self.launcher:
                self.launcher.shutdown()
            self.signals.finished.emit(profile_id)

    def _send_discord_notification(self, profile_name, message):
        """Sends a notification payload to the configured Discord Webhook."""
        if not self.webhook_url: return
        try:
            data = {
                "content": f"🚨 **Lead Alert** 🚨\n**Account:** `{profile_name}`\n**Status:** {message}",
                "username": "FB Autopilot Bot"
            }
            response = requests.post(self.webhook_url, json=data, timeout=5)
            response.raise_for_status()
        except Exception as e:
            print(f"Discord Webhook failed: {e}")

def start_messenger_pulse(profiles: list, mode: str, app_dir: str, threadpool, webhook_url: str, ui_parent=None):
    """
    Dispatches the Visible Messenger Workers based on the selected mode:
    'One-by-One', 'Batch', or 'All'.
    """
    print(f"Starting Bulk Messenger Pulse. Mode: {mode}. Profiles Count: {len(profiles)}")

    if not profiles:
        return

    if mode == "One-by-One":
        from services.task_runner import SequentialManager
        if ui_parent:
            ui_parent.sequential_manager = SequentialManager(profiles, app_dir, threadpool)
            def _create_messenger_worker(p):
                w = VisibleMessengerWorker(p, app_dir, webhook_url)
                if ui_parent:
                    w.signals.status_update.connect(ui_parent.on_worker_status_update)
                return w

            ui_parent.sequential_manager._create_worker = _create_messenger_worker
            ui_parent.sequential_manager.start()

    elif mode == "Batch":
        batch_size = 5
        for i in range(0, len(profiles), batch_size):
            batch = profiles[i:i + batch_size]
            for p in batch:
                worker = VisibleMessengerWorker(p, app_dir, webhook_url)
                if ui_parent:
                    worker.signals.status_update.connect(ui_parent.on_worker_status_update)
                threadpool.start(worker)
            time.sleep(10)

    elif mode == "All":
        for p in profiles:
            worker = VisibleMessengerWorker(p, app_dir, webhook_url)
            if ui_parent:
                worker.signals.status_update.connect(ui_parent.on_worker_status_update)
            threadpool.start(worker)
