import time
import random
from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal

class MessengerSignals(QObject):
    status_update = pyqtSignal(int, str)
    finished = pyqtSignal(int)
    error = pyqtSignal(int, str)

class HeadlessMessengerWorker(QRunnable):
    """
    Background worker that logs into a profile headlessly, checks for messages,
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
        try:
            self.signals.status_update.emit(profile_id, "💬 Headless Pulse Started...")

            # Simulate headless browser initialization and message checking
            time.sleep(random.uniform(2.0, 5.0))

            # Simulate finding a lead
            lead_found = random.choice([True, False])

            if lead_found:
                self.signals.status_update.emit(profile_id, "📩 Replied to Lead")
                if self.webhook_url:
                    self._send_discord_notification(self.profile['profile_name'], "New lead secured and replied to!")
            else:
                self.signals.status_update.emit(profile_id, "✅ No New Messages")

        except Exception as e:
            self.signals.error.emit(profile_id, str(e))
        finally:
            self.signals.finished.emit(profile_id)

    def _send_discord_notification(self, profile_name, message):
        """Sends a notification payload to the configured Discord Webhook."""
        # This will use the requests library to POST to the Discord URL
        # Placeholder for actual requests.post implementation
        print(f"[Discord Webhook -> {self.webhook_url}] Alert for {profile_name}: {message}")

def start_messenger_pulse(profiles: list, mode: str, app_dir: str, threadpool, webhook_url: str):
    """
    Dispatches the Headless Messenger Workers based on the selected mode:
    'One-by-One', 'Batch', or 'All'.
    """
    print(f"Starting Bulk Messenger Pulse. Mode: {mode}. Profiles Count: {len(profiles)}")
    # In a real implementation, 'One-by-One' would use SequentialManager,
    # 'Batch' would launch chunks using QThreadPool limits,
    # and 'All' would dispatch all runnables instantly.

    for p in profiles:
        worker = HeadlessMessengerWorker(p, app_dir, webhook_url)
        # Note: UI Signal connections would happen here to update table status
        threadpool.start(worker)
