import os
import json
import time
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# PILLAR 2 & 3: BROWSER ENGINE & ZOMBIE KILLER
# ==========================================

class ProfileLauncher:
    """
    Handles secure initialization, stealth CDP injection, session injection,
    and zombie-killing shutdown for a single Chrome instance.
    """

    def __init__(self, profile_data: dict, app_dir: str):
        self.profile = profile_data
        self.app_dir = app_dir
        self.account_id = profile_data.get('account_id')
        self.profile_dir = os.path.join(self.app_dir, 'profiles', f'id_{self.account_id}')
        self.session_file = os.path.join(self.profile_dir, "portable_session.json")
        self.driver = None

    def launch(self) -> uc.Chrome:
        """Initializes the UC Browser with Anti-Detect and RAM Management flags."""
        os.makedirs(self.profile_dir, exist_ok=True)

        # 1. Clean Chromium Locks to prevent Profile-In-Use errors
        self._force_clean_locks()

        # 2. Configure Flags
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--profile-directory=Default")

        # RAM & Resource Optimization (Pillar 3)
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('--js-flags="--max-old-space-size=512"')

        # Stealth & Proxies
        user_agent = self.profile.get('custom_user_agent', '').strip()
        if user_agent:
            options.add_argument(f'--user-agent={user_agent}')

        proxy_str = self.profile.get('account_proxy', '').strip()
        if proxy_str:
            parts = proxy_str.split(':')
            if len(parts) == 2:
                options.add_argument(f'--proxy-server=http://{proxy_str}')
            # Note: Auth proxies require extension generation, omitted here for brevity but should be added

        # 3. UC Constructor Fix: Using webdriver_manager directly due to auto-update errors.
        # This solves the `__init__() got an unexpected keyword argument 'path'` error in the newest lib versions.
        from webdriver_manager.chrome import ChromeDriverManager
        try:
            driver_path = ChromeDriverManager().install()

            self.driver = uc.Chrome(
                options=options,
                no_first_run=True,
                user_data_dir=self.profile_dir,
                driver_executable_path=driver_path
            )
        except Exception as e:
            print(f"[{self.account_id}] Warning: webdriver_manager fail. Trying fallback: {e}")
            self.driver = uc.Chrome(
                options=options,
                no_first_run=True,
                user_data_dir=self.profile_dir,
                version_main=146 # Fallback standard
            )

        self.driver.set_page_load_timeout(30)
        self._inject_stealth_scripts()
        return self.driver

    def _inject_stealth_scripts(self):
        """Spoofs Navigator Property and Webdriver variables via CDP."""
        if not self.driver: return

        stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {}, loadTimes: function() {}, csiv: function() {}, setup: function() {} };
        """
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": stealth_script
        })

    def inject_portable_session(self):
        """
        Physical Migration Fix: Injects plain-text cookies to bypass machine-encryption.
        Must be called AFTER launch() but BEFORE actual tasks.
        """
        if not self.driver or not os.path.exists(self.session_file):
            return False

        print(f"[{self.account_id}] Portable session found. Injecting...")
        self.driver.get("https://www.facebook.com")
        time.sleep(2)

        self.driver.delete_all_cookies() # Clear encrypted junk

        with open(self.session_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
            for cookie in cookies:
                try:
                    if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                        del cookie['sameSite']
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    # Retry without domain if strict
                    if 'domain' in cookie:
                        del cookie['domain']
                        try:
                            self.driver.add_cookie(cookie)
                        except: pass

        self.driver.refresh()
        time.sleep(3)
        print(f"[{self.account_id}] Session injected successfully.")
        return True

    def extract_portable_session(self):
        """Saves live cookies to portable_session.json. Called right before shutdown."""
        if not self.driver: return
        try:
            cookies = self.driver.get_cookies()
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=4)
            print(f"[{self.account_id}] Exported portable session.")
        except Exception as e:
            print(f"[{self.account_id}] Failed to export session: {e}")

    def shutdown(self):
        """
        The Zero-Resource Background Killer (Pillar 3).
        Quits the driver, extracts session, and uses psutil to forcefully terminate zombies.
        """
        if self.driver:
            self.extract_portable_session()
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

        self._hard_kill_zombies()
        self._clear_temp_cache()

    def _hard_kill_zombies(self):
        """Uses psutil to find and kill all processes linked to this specific profile directory."""
        import psutil
        abs_profile_dir = os.path.abspath(self.profile_dir)
        killed_count = 0

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name'].lower() if proc.info['name'] else ''
                if 'chrome' in name or 'chromium' in name or 'chromedriver' in name:
                    cmdline = proc.info.get('cmdline')
                    if cmdline and any(abs_profile_dir in arg for arg in cmdline if arg):
                        proc.kill()
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if killed_count > 0:
            print(f"[{self.account_id}] Zombie Killer: Terminated {killed_count} background processes.")

    def _clear_temp_cache(self):
        """Wipes Cache and Temp files to save disk space, strictly keeping Cookies."""
        target_folders = [
            os.path.join(self.profile_dir, "Default", "Cache"),
            os.path.join(self.profile_dir, "Default", "System Cache"),
            os.path.join(self.profile_dir, "Default", "Code Cache"),
            os.path.join(self.profile_dir, "Default", "GPUCache"),
            os.path.join(self.profile_dir, "Crash Reports"),
            os.path.join(self.profile_dir, "ShaderCache"),
            os.path.join(self.profile_dir, "Shader Cache")
        ]
        for folder in target_folders:
            if os.path.exists(folder):
                try: shutil.rmtree(folder)
                except: pass

    def _force_clean_locks(self):
        """Removes locks that cause UC to crash on launch."""
        locks = ['SingletonLock', 'lock', 'Parent.lock']
        dirs = [self.profile_dir, os.path.join(self.profile_dir, "Default")]
        for d in dirs:
            for lock in locks:
                p = os.path.join(d, lock)
                if os.path.exists(p):
                    try:
                        if os.path.isdir(p): shutil.rmtree(p)
                        else: os.remove(p)
                    except: pass
