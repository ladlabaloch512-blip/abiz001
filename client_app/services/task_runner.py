from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal, QThreadPool
import time
from core.database import update_profile_status
from automation.browser_engine import ProfileLauncher

# ==========================================
# PILLAR 5: MANAGEMENT & SYNC (TASK RUNNERS)
# ==========================================

# Global registry of active ProfileLauncher instances
ACTIVE_LAUNCHERS = {}

class WorkerSignals(QObject):
    finished = pyqtSignal(int)          # profile_id
    error = pyqtSignal(int, str)        # profile_id, error_msg
    status_update = pyqtSignal(int, str) # profile_id, status_string

class BrowserTaskWorker(QRunnable):
    """
    Background worker that launches the browser engine and maintains the
    Smart Interaction Sequence and URL Monitoring without freezing the UI.
    """
    def __init__(self, profile_data: dict, app_dir: str, task_type: str = "Auto-Login"):
        super().__init__()
        self.profile = profile_data
        self.app_dir = app_dir
        self.task_type = task_type
        self.signals = WorkerSignals()
        self.launcher = None

    def navigate_with_status_sync(self, driver, profile_id):
        """Monitors current URL and syncs status to DB (Pillar 5)."""
        last_status = None
        final_url_detected = ""

        while True:
            try:
                if driver.window_handles:
                    driver.switch_to.window(driver.window_handles[0])

                current_url = driver.current_url.lower()
                final_url_detected = current_url
                new_status = "🌐 Running"

                if 'checkpoint' in current_url:
                    new_status = "⚠️ Checkpoint"
                elif any(x in current_url for x in ['/home', '/feed', '?sk=h_chr']):
                    new_status = "✅ Active (Logged In)"
                elif 'login' in current_url:
                    new_status = "⏳ Waiting for Login"

                if new_status != last_status:
                    last_status = new_status
                    update_profile_status(self.app_dir, profile_id, new_status)
                    self.signals.status_update.emit(profile_id, new_status)

                time.sleep(2)
            except Exception:
                # Browser closed manually or crashed
                break

        return final_url_detected

    @pyqtSlot()
    def run(self):
        profile_id = self.profile['id']
        try:
            self.signals.status_update.emit(profile_id, "🔄 Initializing...")
            update_profile_status(self.app_dir, profile_id, "🔄 Initializing...")

            self.launcher = ProfileLauncher(self.profile, self.app_dir)
            ACTIVE_LAUNCHERS[profile_id] = self.launcher

            driver = self.launcher.launch()

            # Machine-Portability Injection
            self.launcher.inject_portable_session()

            if self.task_type == "Auto-Login":
                driver.get("https://www.facebook.com")
                # Blocking loop until closed
                final_url = self.navigate_with_status_sync(driver, profile_id)

                # Assign final state
                final_state = "Ready"
                if 'checkpoint' in final_url:
                    final_state = "⚠️ Checkpoint"
                elif any(x in final_url for x in ['/home', '/feed', '?sk=h_chr']):
                    final_state = "✅ Active"

                update_profile_status(self.app_dir, profile_id, final_state)
                self.signals.status_update.emit(profile_id, final_state)

        except Exception as e:
            err = str(e)
            print(f"[{self.profile.get('account_id')}] Error: {err}")
            self.signals.error.emit(profile_id, err)
            update_profile_status(self.app_dir, profile_id, "❌ Error")
            self.signals.status_update.emit(profile_id, "❌ Error")
        finally:
            if profile_id in ACTIVE_LAUNCHERS:
                del ACTIVE_LAUNCHERS[profile_id]
            if self.launcher:
                self.launcher.shutdown()
            self.signals.finished.emit(profile_id)

class SequentialManager(QObject):
    """
    Handles the 1-by-1 Launch Queue.
    Listens for the finished signal of the active worker before spinning off the next.
    """
    queue_completed = pyqtSignal()

    def __init__(self, profiles: list, app_dir: str, threadpool: QThreadPool):
        super().__init__()
        self.queue = profiles
        self.app_dir = app_dir
        self.threadpool = threadpool
        self.current_worker = None

    def start(self):
        self._launch_next()

    def _launch_next(self):
        if not self.queue:
            self.queue_completed.emit()
            return

        profile = self.queue.pop(0)

        if hasattr(self, '_create_worker') and self._create_worker:
            self.current_worker = self._create_worker(profile)
        else:
            self.current_worker = BrowserTaskWorker(profile, self.app_dir)

        # Hook up the sequential completion chain
        self.current_worker.signals.finished.connect(self._on_worker_finished)

        self.threadpool.start(self.current_worker)

    @pyqtSlot(int)
    def _on_worker_finished(self, profile_id):
        # Triggered when previous profile fully closes and cleans up RAM
        self._launch_next()

def stop_browser(profile_id: int):
    """Safely triggers the Zombie Killer on an active launcher."""
    launcher = ACTIVE_LAUNCHERS.get(profile_id)
    if launcher:
        # shutdown() calls driver.quit(), extract_session(), and hard_kill_zombies()
        launcher.shutdown()
        del ACTIVE_LAUNCHERS[profile_id]
