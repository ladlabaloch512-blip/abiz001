import json
import time
import random
import traceback
import queue
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import (
    DEFAULT_MAX_WORKERS,
    LOCATORS_PATH,
    MIN_WAIT_DELAY,
    MAX_WAIT_DELAY,
    PAGE_LOAD_TIMEOUT,
    EXPLICIT_WAIT_TIMEOUT
)
from session_manager import SessionManager
from database import DatabaseManager

# ------------------------------------------------------------------------------
# Automation Executor
# Thread-safe Task Dispatcher utilizing ThreadPoolExecutor.
# Relies heavily on Queue for non-blocking UI Log updates.
# ------------------------------------------------------------------------------

class AutomationTask:
    """Represents a single automation job for a specific profile."""
    def __init__(self, profile_id: int, profile_name: str, task_type: str, payload: Dict[str, Any]):
        self.profile_id = profile_id
        self.profile_name = profile_name
        self.task_type = task_type
        self.payload = payload

class AutomationEngine:
    def __init__(self, db_manager: DatabaseManager, ui_queue: queue.Queue):
        self.db = db_manager
        self.ui_queue = ui_queue

        # Load Locators dynamically
        self.locators = self._load_locators()

        # Initialize ThreadPool
        self.executor = ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS)
        self.session_manager = SessionManager(headless_override=False) # Can be toggled via settings UI later

        # Active futures to allow cancellation tracking if needed later
        self.active_futures = []

    def _load_locators(self) -> Dict[str, Any]:
        """Loads element locators from the dynamic JSON config."""
        try:
            with open(LOCATORS_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            self._log_to_ui(0, "System", "Error", f"Failed to load locators.json: {str(e)}")
            return {}

    def _log_to_ui(self, profile_id: int, profile_name: str, status: str, message: str):
        """Pushes a log dictionary to the Queue for the main GUI thread to consume."""
        log_entry = {
            "profile_id": profile_id,
            "profile_name": profile_name,
            "status": status,
            "message": message,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.ui_queue.put(log_entry)

        # Also persist to database
        if profile_id > 0:
            self.db.add_log(profile_id, "Generic Automation", status, message)

    def _human_delay(self):
        """Simulates human typing/reading wait periods."""
        delay = random.uniform(MIN_WAIT_DELAY, MAX_WAIT_DELAY)
        time.sleep(delay)

    def dispatch_tasks(self, tasks: List[AutomationTask]):
        """Submits a list of tasks to the executor pool."""
        self._log_to_ui(0, "System", "Info", f"Dispatching {len(tasks)} tasks to ThreadPool.")
        for task in tasks:
            future = self.executor.submit(self._worker_execute, task)
            self.active_futures.append(future)

    def _worker_execute(self, task: AutomationTask):
        """
        The core thread worker function.
        Instantiates Selenium, performs the generic task, and reports via Queue.
        """
        self._log_to_ui(task.profile_id, task.profile_name, "Running", f"Starting task: {task.task_type}")

        # 1. Fetch Profile Data within the thread
        profile_data = self.db.get_profile(task.profile_id)
        if not profile_data:
            self._log_to_ui(task.profile_id, task.profile_name, "Error", "Profile data not found in DB.")
            return

        driver = None
        try:
            # 2. Initialize Driver
            self._log_to_ui(task.profile_id, task.profile_name, "Running", "Initializing Chrome Session...")
            driver = self.session_manager.create_driver_for_profile(profile_data)
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

            # 3. Route to Specific Task Logic
            if task.task_type == "fill_generic_form":
                self._task_fill_generic_form(driver, task)
            elif task.task_type == "check_login_status":
                self._task_check_login(driver, task)
            elif task.task_type == "send_inbox_reply":
                self._task_send_inbox_reply(driver, task)
            else:
                self._log_to_ui(task.profile_id, task.profile_name, "Error", f"Unknown task type: {task.task_type}")

            # 4. Extract and update cookies post-task to maintain session freshness
            self.session_manager.extract_and_save_cookies(driver, self.db, task.profile_id)

            self._log_to_ui(task.profile_id, task.profile_name, "Success", f"Task {task.task_type} completed successfully.")

        except Exception as e:
            error_trace = traceback.format_exc()
            self._log_to_ui(task.profile_id, task.profile_name, "Error", f"Exception during execution: {str(e)}")
            print(f"[{task.profile_name}] Detailed Error:\n{error_trace}")

        finally:
            # 5. Ensure safe cleanup
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                self._log_to_ui(task.profile_id, task.profile_name, "Done", "Chrome Session closed.")


    # --- Task Implementations using dynamic Locators ---

    def _task_fill_generic_form(self, driver, task: AutomationTask):
        """Example task: Navigates to a form URL and fills it using payload data."""
        target_url = self.locators.get("generic_form", {}).get("form_url", "https://example.com")
        self._log_to_ui(task.profile_id, task.profile_name, "Running", f"Navigating to {target_url}")

        driver.get(target_url)
        self._human_delay()

        # Extract locators
        locs = self.locators.get("generic_form", {})
        wait = WebDriverWait(driver, EXPLICIT_WAIT_TIMEOUT)

        # Fill Title
        if "title" in task.payload and "title_input_xpath" in locs:
            self._log_to_ui(task.profile_id, task.profile_name, "Running", "Entering Title...")
            el_title = wait.until(EC.presence_of_element_located((By.XPATH, locs["title_input_xpath"])))
            el_title.clear()
            # Simulate typing
            for char in task.payload["title"]:
                el_title.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            self._human_delay()

        # Fill Cost
        if "cost" in task.payload and "cost_input_xpath" in locs:
            self._log_to_ui(task.profile_id, task.profile_name, "Running", "Entering Cost...")
            el_cost = wait.until(EC.presence_of_element_located((By.XPATH, locs["cost_input_xpath"])))
            el_cost.clear()
            el_cost.send_keys(task.payload["cost"])
            self._human_delay()

        # Click Submit
        if "submit_button_xpath" in locs:
            self._log_to_ui(task.profile_id, task.profile_name, "Running", "Clicking Submit...")
            el_submit = wait.until(EC.element_to_be_clickable((By.XPATH, locs["submit_button_xpath"])))
            el_submit.click()
            self._human_delay()

    def _task_send_inbox_reply(self, driver, task: AutomationTask):
        """Example task: Navigates to inbox and sends a reply."""
        target_url = self.locators.get("base_target_url", "https://example.com") + "/inbox"
        self._log_to_ui(task.profile_id, task.profile_name, "Running", f"Navigating to {target_url} for reply.")
        driver.get(target_url)
        self._human_delay()

        locs = self.locators.get("notifications", {})
        wait = WebDriverWait(driver, EXPLICIT_WAIT_TIMEOUT)

        if "reply" in task.payload and "reply_textbox_xpath" in locs:
            self._log_to_ui(task.profile_id, task.profile_name, "Running", "Typing reply...")
            el_reply = wait.until(EC.presence_of_element_located((By.XPATH, locs["reply_textbox_xpath"])))
            el_reply.clear()
            for char in task.payload["reply"]:
                el_reply.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            self._human_delay()

        if "send_reply_button_xpath" in locs:
            self._log_to_ui(task.profile_id, task.profile_name, "Running", "Clicking Send...")
            el_send = wait.until(EC.element_to_be_clickable((By.XPATH, locs["send_reply_button_xpath"])))
            el_send.click()
            self._human_delay()

    def _task_check_login(self, driver, task: AutomationTask):
        """Example task: Checks if the current session cookies provide a valid login state."""
        target_url = self.locators.get("base_target_url", "https://example.com")
        self._log_to_ui(task.profile_id, task.profile_name, "Running", f"Navigating to {target_url} for auth check.")
        driver.get(target_url)
        self._human_delay()

        # Basic check for an element that only exists when logged in
        check_xpath = self.locators.get("auth", {}).get("success_check_xpath")
        if check_xpath:
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, check_xpath)))
                self._log_to_ui(task.profile_id, task.profile_name, "Success", "Session is Valid (Logged In).")
            except Exception:
                self._log_to_ui(task.profile_id, task.profile_name, "Error", "Session Invalid (Not Logged In).")
