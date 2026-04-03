import os
import shutil
import time
import json
import zipfile
import threading
import random
import re
from datetime import datetime
from PIL import Image
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal
from .database import update_last_active, update_profile_status

# Global registry for active drivers to support right-click actions
ACTIVE_DRIVERS = {}

# --- FB Marketplace XPaths ---
FB_MARKET_URL = "https://www.facebook.com/marketplace/create/item"
FB_MARKET_SELLING_URL = "https://www.facebook.com/marketplace/you/selling"
XPATH_FILE_INPUT = "//input[@type='file' and @accept='image/*,image/heif,image/heic']"
XPATH_TITLE_INPUT = "//label[.//span[text()='Title']]//input"
XPATH_PRICE_INPUT = "//label[.//span[text()='Price']]//input"
XPATH_CONDITION_DROPDOWN = "//label[.//span[text()='Condition']]//div[@role='button']"
XPATH_DESC_INPUT = "//label[.//span[text()='Description']]//textarea"
XPATH_LOCATION_INPUT = "//label[.//span[text()='Location']]//input"
XPATH_NEXT_BTN = "//div[@aria-label='Next' and @role='button']"
XPATH_PUBLISH_BTN = "//div[@aria-label='Publish' and @role='button']"

class StopBrowserWorker(QRunnable):
    """Threaded worker to cleanly close browsers without freezing the UI."""
    def __init__(self, profile_ids):
        super().__init__()
        self.profile_ids = profile_ids

    @pyqtSlot()
    def run(self):
        for profile_id in self.profile_ids:
            driver = ACTIVE_DRIVERS.get(profile_id)
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"Error quitting driver for {profile_id}: {e}")
                finally:
                    if profile_id in ACTIVE_DRIVERS:
                        del ACTIVE_DRIVERS[profile_id]
                    update_profile_status(profile_id, 'Ready')

def stop_all_selected(profile_ids, threadpool=None):
    """Dispatches stopping logic to a background thread to prevent UI freezing."""
    worker = StopBrowserWorker(profile_ids)
    if threadpool:
        threadpool.start(worker)
    else:
        # Fallback if no threadpool provided
        worker.run()

# Custom signals for UI updating from threads
class WorkerSignals(QObject):
    finished = pyqtSignal(int) # profile_id
    error = pyqtSignal(tuple)
    status_update = pyqtSignal(int, str) # profile_id, new_status

class BaseBrowserWorker(QRunnable):
    """Base class providing shared proxy and automation utility functions."""
    def __init__(self):
        super().__init__()

    def force_clean_locks(self, profile_dir):
        """Removes Chromium lock files to prevent 'Target window already closed' and profile-in-use errors."""
        locks = [
            'SingletonLock',
            'lock',
            'Parent.lock'
        ]
        # Check root and Default folder
        dirs_to_check = [profile_dir, os.path.join(profile_dir, "Default")]
        for d in dirs_to_check:
            for lock in locks:
                lock_path = os.path.join(d, lock)
                if os.path.exists(lock_path):
                    try:
                        if os.path.isfile(lock_path) or os.path.islink(lock_path):
                            os.remove(lock_path)
                        elif os.path.isdir(lock_path):
                            shutil.rmtree(lock_path)
                    except Exception as e:
                        print(f"Warning: Could not remove lock file {lock_path}: {e}")

    def inject_stealth_scripts(self, driver, profile):
        """
        Injects a minimalist stealth payload using CDP.
        Bypasses strict anti-bot detection without triggering 'Randomized Noise' flags.
        """

        # Minimalist Stealth Script
        stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {}, loadTimes: function() {}, csiv: function() {}, setup: function() {} };
        """
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": stealth_script
        })

        # CDP Spoofing for Timezone and Locale
        tz = profile.get('tz', 'America/New_York')
        locale = profile.get('locale', 'en-US')

        driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
            "timezoneId": tz
        })

        driver.execute_cdp_cmd("Emulation.setLocaleOverride", {
            "locale": locale
        })

        # User-Agent handling is primarily native via Chrome Options, but we sync it here:
        ua = profile.get('stealth_ua')
        if ua:
            driver.execute_cdp_cmd("Network.setUserAgentOverride", {
                "userAgent": ua,
                "acceptLanguage": locale
            })

    def reliable_type(self, driver, element, text):
        """
        Reliable Typing Engine: Highly accurate character-by-character input.
        Prioritizes sequence integrity and React sync over raw speed to prevent character scrambling.
        """
        try:
            # 1. Clear and Click to ensure absolute focus
            element.clear()
            time.sleep(0.2)
            element.click()
            time.sleep(0.2)

            # 2. Strict Physical Key-Tap Method
            for char in text:
                actions = ActionChains(driver)
                actions.send_keys(char)
                actions.perform()
                time.sleep(random.uniform(0.05, 0.08))

            # 3. React-Event Refresh (Backup Sync)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)

        except Exception as e:
            print(f"Error during reliable_type: {e}")

    def generate_proxy_extension(self, proxy_string, profile_dir):
        """
        Generates a temporary Chrome extension for authenticated proxies (IP:PORT:USER:PASS).
        """
        parts = proxy_string.split(':')
        if len(parts) == 4:
            ip, port, user, password = parts
        else:
            return None # Not an authenticated proxy, or malformed

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (ip, port, user, password)

        # Create extensions dir inside the profile dir
        extension_path = os.path.join(profile_dir, "proxy_ext.zip")

        with zipfile.ZipFile(extension_path, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        return extension_path

class BrowserLauncherWorker(BaseBrowserWorker):
    """
    QRunnable thread instance to launch and maintain a single Chrome browser instance.
    This prevents the PyQt6 UI from freezing when launching multiple profiles.
    """
    def __init__(self, profile_data, task_type="Manual", custom_url=""):
        super().__init__()
        self.profile = profile_data
        self.task_type = task_type
        self.custom_url = custom_url
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        driver = None
        try:
            profile_id = self.profile['id']
            account_id = self.profile['account_id']
            proxy_str = self.profile.get('account_proxy', '').strip()

            # 1. Define Paths
            base_dir = os.path.dirname(os.path.abspath(__file__))

            # Profile Isolation: Unique user-data-dir per ID
            profile_dir = os.path.abspath(os.path.join(base_dir, 'profiles', f'id_{account_id}'))
            os.makedirs(profile_dir, exist_ok=True)

            # Setup Chrome Options
            options = uc.ChromeOptions()

            # 2. Anti-Detect Flags
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            options.add_argument("--force-device-scale-factor=1")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--profile-directory=Default")

            # Explicitly set accept-languages to match proxy footprint
            locale = self.profile.get('locale', 'en-US')
            options.add_argument(f"--accept-lang={locale}")

            # 3. Handle Proxy
            if proxy_str:
                parts = proxy_str.split(':')
                if len(parts) == 2:
                    # Basic IP:PORT
                    options.add_argument(f'--proxy-server=http://{proxy_str}')
                elif len(parts) == 4:
                    # Authenticated Proxy IP:PORT:USER:PASS
                    ext_path = self.generate_proxy_extension(proxy_str, profile_dir)
                    if ext_path:
                        options.add_argument(f'--load-extension={ext_path}')

            # 4. Handle Custom User Agent
            user_agent = self.profile.get('stealth_ua', '').strip()
            if not user_agent:
                user_agent = self.profile.get('custom_user_agent', '').strip()
            if user_agent:
                options.add_argument(f'--user-agent={user_agent}')

            # 5. Launch Browser natively via system Chrome using UC Auto-Patcher
            self.force_clean_locks(profile_dir)

            try:
                driver = uc.Chrome(
                    options=options,
                    no_first_run=True,
                    user_data_dir=profile_dir,
                    version_main=146
                )
            except Exception as uc_err:
                print(f"[{account_id}] Warning: Failed to launch with version_main=146, trying default: {uc_err}")
                driver = uc.Chrome(
                    options=options,
                    no_first_run=True,
                    user_data_dir=profile_dir
                )
            driver.set_page_load_timeout(30)

            # 6. Inject Full Stealth Engine (Canvas, WebGL, CDP overrrides)
            self.inject_stealth_scripts(driver, self.profile)

            # Register Active Driver globally
            ACTIVE_DRIVERS[profile_id] = driver

            self.signals.status_update.emit(profile_id, "🔄 Initializing...")
            update_profile_status(profile_id, "🔄 Initializing...")

            # Navigate based on Task Type
            if self.task_type == "Facebook Login & Home":
                driver.get("https://www.facebook.com")
                # We specifically delete ONLY the anti-bot verification cookies
                # (like 'datr', 'wd') to avoid wiping the entire active login session ('c_user', 'xs').
                try:
                    driver.delete_cookie("wd")
                    driver.delete_cookie("datr")
                except Exception:
                    pass
                driver.refresh()
            elif self.task_type == "Custom URL":
                if not self.custom_url:
                    print(f"[{account_id}] Warning: No Custom URL provided. Defaulting to chrome://newtab/")
                    driver.get("chrome://newtab/")
                else:
                    if not self.custom_url.startswith("http"):
                        self.custom_url = "https://" + self.custom_url
                    driver.get(self.custom_url)
            else:
                # Manual (Blank Tab) - Navigate cleanly to New Tab
                driver.get("chrome://newtab/")

            # Basic cookie injection logic if a json cookie file exists in profile_dir
            cookie_file = os.path.join(profile_dir, 'cookies.json')
            if os.path.exists(cookie_file):
                try:
                    with open(cookie_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                        for cookie in cookies:
                            # Standardize cookie format if necessary
                            if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                                del cookie['sameSite']
                            # Add domain if not strictly present based on url
                            try:
                                driver.add_cookie(cookie)
                            except Exception as e:
                                pass # ignore invalid cookies
                    driver.refresh() # Refresh to apply
                except Exception as e:
                    print(f"Warning: Could not inject cookies from {cookie_file}: {e}")
            else:
                # Fallback to any json
                import glob
                json_files = glob.glob(os.path.join(profile_dir, '*.json'))
                if json_files:
                    cookie_file = json_files[0]
                    try:
                        with open(cookie_file, 'r', encoding='utf-8') as f:
                            cookies = json.load(f)
                            for cookie in cookies:
                                if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                                    del cookie['sameSite']
                                try:
                                    driver.add_cookie(cookie)
                                except Exception:
                                    pass
                        driver.refresh()
                    except Exception as e:
                        print(f"Warning: Could not inject cookies from {cookie_file}: {e}")

            # Update last active in DB
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_last_active(profile_id, now_str)

            # 7. AutoSync Status Background Loop
            # Keep alive and monitor URL to dynamically emit status
            last_status = None
            while True:
                try:
                    if driver.window_handles:
                        driver.switch_to.window(driver.window_handles[0])
                    current_url = driver.current_url.lower()

                    new_status = "🌐 Running"
                    if self.task_type == "Facebook Login & Home":
                        if 'checkpoint' in current_url:
                            new_status = "⚠️ Checkpoint"
                        elif any(x in current_url for x in ['/home', '/feed', '?sk=h_chr']):
                            new_status = "✅ Active (Logged In)"
                        elif 'login' in current_url:
                            new_status = "⏳ Waiting for Login"
                        else:
                            # Intelligent Check: Verify actual DOM elements to confirm session
                            try:
                                # Look for the main Facebook home layout role or navigation
                                if driver.find_elements(By.CSS_SELECTOR, "div[role='navigation'], input[aria-label='Search Facebook'], svg[aria-label='Home']"):
                                    new_status = "✅ Active (Logged In)"
                            except:
                                pass
                    elif self.task_type == "Custom URL":
                        new_status = "✅ Active"
                    elif self.task_type == "Manual (Blank Tab)":
                        new_status = "✅ Active"

                    # Emit signal if status changed
                    if new_status != last_status:
                        last_status = new_status
                        update_profile_status(profile_id, new_status)
                        self.signals.status_update.emit(profile_id, new_status)

                    time.sleep(2)
                except Exception:
                    # Browser closed
                    break

        except Exception as e:
            self.signals.error.emit((str(e),))
        finally:
            if 'profile_id' in locals() and profile_id in ACTIVE_DRIVERS:
                del ACTIVE_DRIVERS[profile_id]
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            self.signals.finished.emit(self.profile['id'])


class MarketplaceTaskWorker(BaseBrowserWorker):
    """
    QRunnable thread instance to launch Chrome, navigate to FB Marketplace, and post a queue of service listings.
    """
    def __init__(self, profile_data, listing_queue):
        super().__init__()
        self.profile = profile_data
        self.listing_queue = listing_queue # Expects a list of dictionaries
        self.signals = WorkerSignals()

    def process_spintax(self, text):
        """Processes spintax like {Urgent|Emergency|24/7} Repairing."""
        pattern = re.compile(r'\{([^{}]*)\}')
        while True:
            match = pattern.search(text)
            if not match:
                break
            options = match.group(1).split('|')
            replacement = random.choice(options)
            text = text[:match.start()] + replacement + text[match.end():]
        return text

    def scrub_image_exif(self, image_paths):
        """Uses PIL to clear EXIF metadata and imperceptibly alter pixels to bypass Duplicate Content flags."""
        scrubbed_paths = []
        for path in image_paths:
            try:
                img = Image.open(path)

                # Strip metadata
                data = list(img.getdata())
                image_without_exif = Image.new(img.mode, img.size)
                image_without_exif.putdata(data)

                # Randomize 1 pixel to definitively alter the image hash
                pixels = image_without_exif.load()
                x, y = random.randint(0, img.size[0]-1), random.randint(0, img.size[1]-1)
                if img.mode == 'RGB':
                    r, g, b = pixels[x, y]
                    pixels[x, y] = (min(r+1, 255), g, b)
                elif img.mode == 'RGBA':
                    r, g, b, a = pixels[x, y]
                    pixels[x, y] = (min(r+1, 255), g, b, a)

                base_dir = os.path.dirname(os.path.abspath(__file__))
                temp_dir = os.path.join(base_dir, 'temp_images')
                os.makedirs(temp_dir, exist_ok=True)

                filename = f"scrubbed_{random.randint(1000, 9999)}_{os.path.basename(path)}"
                temp_path = os.path.join(temp_dir, filename)

                image_without_exif.save(temp_path)
                scrubbed_paths.append(temp_path)
            except Exception as e:
                print(f"Failed to scrub image {path}: {e}")

        return scrubbed_paths

    def human_delay(self, min_s=3.0, max_s=7.0):
        """Randomized sleep interval to bypass bot detection."""
        time.sleep(random.uniform(min_s, max_s))

    def force_fill(self, driver, xpath, text):
        """Scrolls into view, physically clicks, types using ActionChains, and Tabs out."""
        wait = WebDriverWait(driver, 10)
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.5)

            # ActionChains force click and type
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            time.sleep(0.5)

            # Clear if necessary (React might override this, so ctrl+a + backspace is safer)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
            time.sleep(0.5)

            for char in text:
                actions.send_keys(char).perform()
                time.sleep(random.uniform(0.03, 0.08))

            # Tab out to force React state sync
            actions.send_keys(Keys.TAB).perform()

        except Exception as e:
            print(f"Error force_filling {xpath}: {e}")

    def select_condition(self, driver, condition_text):
        """Scrolls to the Condition dropdown, clicks it, and selects the matching option."""
        wait = WebDriverWait(driver, 10)
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, XPATH_CONDITION_DROPDOWN)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.5)
            element.click()
            time.sleep(1.0) # Wait for the Facebook popup menu to render

            # The dropdown options render in a listbox attached to the body, usually identifiable by text
            option_xpath = f"//div[@role='option']//span[contains(text(), '{condition_text}')]"
            option = wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
            option.click()
            time.sleep(0.5)
        except Exception as e:
            print(f"Error selecting condition '{condition_text}': {e}")

    @pyqtSlot()
    def run(self):
        driver = None
        try:
            profile_id = self.profile['id']
            account_id = self.profile['account_id']
            base_dir = os.path.dirname(os.path.abspath(__file__))

            # Paths
            profile_dir = os.path.abspath(os.path.join(base_dir, 'profiles', f'id_{account_id}'))
            os.makedirs(profile_dir, exist_ok=True)

            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            options.add_argument("--force-device-scale-factor=1")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--profile-directory=Default")

            # Explicitly set accept-languages to match proxy footprint
            locale = self.profile.get('locale', 'en-US')
            options.add_argument(f"--accept-lang={locale}")

            user_agent = self.profile.get('custom_user_agent', '').strip()
            if user_agent:
                options.add_argument(f'--user-agent={user_agent}')

            # Handle Proxy via Base class
            proxy_str = self.profile.get('account_proxy', '').strip()
            if proxy_str:
                parts = proxy_str.split(':')
                if len(parts) == 2:
                    options.add_argument(f'--proxy-server=http://{proxy_str}')
                elif len(parts) == 4:
                    ext_path = self.generate_proxy_extension(proxy_str, profile_dir)
                    if ext_path:
                        options.add_argument(f'--load-extension={ext_path}')

            self.force_clean_locks(profile_dir)

            try:
                driver = uc.Chrome(
                    options=options,
                    no_first_run=True,
                    user_data_dir=profile_dir,
                    version_main=146
                )
            except Exception as uc_err:
                print(f"[{account_id}] Warning: Failed to launch with version_main=146, trying default: {uc_err}")
                driver = uc.Chrome(
                    options=options,
                    no_first_run=True,
                    user_data_dir=profile_dir
                )
            driver.set_page_load_timeout(30)
            self.inject_stealth_scripts(driver, self.profile)

            ACTIVE_DRIVERS[profile_id] = driver
            self.signals.status_update.emit(profile_id, "🔄 Processing Queue...")
            update_profile_status(profile_id, "🔄 Processing Queue...")

            for idx, listing_data in enumerate(self.listing_queue):
                print(f"[{account_id}] Post {idx+1}/{len(self.listing_queue)}: Navigating to FB Marketplace Create Item...")
                driver.get(FB_MARKET_URL)
                self.human_delay(5.0, 10.0)

                # Check for login walls
                if 'login' in driver.current_url.lower():
                    print(f"[{account_id}] Account not logged in. Aborting queue.")
                    self.signals.status_update.emit(profile_id, "❌ Not Logged In")
                    update_profile_status(profile_id, "❌ Not Logged In")
                    break

                # Process Spintax for this specific post
                final_title = self.process_spintax(listing_data['title'])
                final_desc = self.process_spintax(listing_data['description'])
                final_price = listing_data['price']
                final_location = listing_data.get('location', '')
                final_condition = listing_data.get('condition', '')

                # Prepare Images
                scrubbed_images = self.scrub_image_exif(listing_data['images'])

                if scrubbed_images:
                    image_paths_str = "\n".join(scrubbed_images)
                    print(f"[{account_id}] Uploading scrubbed images...")
                    try:
                        driver.find_element(By.XPATH, XPATH_FILE_INPUT).send_keys(image_paths_str)
                        # Explicitly wait for images to process (crucial fix for getting stuck)
                        print(f"[{account_id}] Waiting 10 seconds for images to upload and render...")
                        time.sleep(10.0)
                    except Exception as e:
                        print(f"[{account_id}] Warning: Could not upload images: {e}")

                print(f"[{account_id}] Entering Title: {final_title}")
                self.force_fill(driver, XPATH_TITLE_INPUT, final_title)

                print(f"[{account_id}] Entering Price: {final_price}")
                self.force_fill(driver, XPATH_PRICE_INPUT, final_price)

                if final_condition:
                    print(f"[{account_id}] Selecting Condition: {final_condition}")
                    self.select_condition(driver, final_condition)

                if final_location:
                    print(f"[{account_id}] Entering Location: {final_location}")
                    self.force_fill(driver, XPATH_LOCATION_INPUT, final_location)
                    # Wait for autocomplete, push ARROW_DOWN to grab the first suggestion and hit ENTER
                    time.sleep(2.0)
                    try:
                        actions = ActionChains(driver)
                        actions.send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).perform()
                        time.sleep(1.0)
                    except:
                        pass

                print(f"[{account_id}] Entering Description...")
                self.force_fill(driver, XPATH_DESC_INPUT, final_desc)

                print(f"[{account_id}] Navigating Next & Publishing...")
                try:
                    # Click Next
                    wait = WebDriverWait(driver, 5)
                    next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_NEXT_BTN)))
                    driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                    time.sleep(1.0)
                    next_btn.click()
                    self.human_delay(3.0, 5.0)

                    # Click Publish
                    publish_btn = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_PUBLISH_BTN)))
                    driver.execute_script("arguments[0].scrollIntoView();", publish_btn)
                    time.sleep(1.0)
                    publish_btn.click()

                    # Wait for publish to finish redirecting
                    time.sleep(10.0)

                    success_msg = f"✅ Posted - {final_title[:15]}..."
                    self.signals.status_update.emit(profile_id, success_msg)
                    update_profile_status(profile_id, success_msg)
                    print(f"[{account_id}] Successfully Published: {final_title}")

                except Exception as e:
                    print(f"[{account_id}] Warning: Could not complete publish sequence: {e}")

                # Delay between multiple posts
                if idx < len(self.listing_queue) - 1:
                    print(f"[{account_id}] Waiting before next post in queue...")
                    self.human_delay(15.0, 30.0)

            # Update last active in DB
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_last_active(profile_id, now_str)

        except Exception as e:
            self.signals.error.emit((str(e),))
        finally:
            if 'profile_id' in locals() and profile_id in ACTIVE_DRIVERS:
                del ACTIVE_DRIVERS[profile_id]
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            self.signals.finished.emit(self.profile['id'])


class CookieExportWorker(BaseBrowserWorker):
    """
    QRunnable thread to launch Chrome headless, steal the session cookies, and save them to a user-defined location.
    """
    def __init__(self, profile_data, save_path):
        super().__init__()
        self.profile = profile_data
        self.save_path = save_path
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        driver = None
        try:
            account_id = self.profile['account_id']
            base_dir = os.path.dirname(os.path.abspath(__file__))
            profile_dir = os.path.abspath(os.path.join(base_dir, 'profiles', f'id_{account_id}'))

            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            options.add_argument("--force-device-scale-factor=1")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--profile-directory=Default")
            # Make it headless for silent extraction
            options.add_argument("--headless=new")

            locale = self.profile.get('locale', 'en-US')
            options.add_argument(f"--accept-lang={locale}")

            user_agent = self.profile.get('custom_user_agent', '').strip()
            if user_agent:
                options.add_argument(f'--user-agent={user_agent}')

            self.force_clean_locks(profile_dir)

            try:
                driver = uc.Chrome(
                    options=options,
                    no_first_run=True,
                    user_data_dir=profile_dir,
                    version_main=146
                )
            except Exception as uc_err:
                print(f"[{account_id}] Warning: Failed to launch with version_main=146, trying default: {uc_err}")
                driver = uc.Chrome(
                    options=options,
                    no_first_run=True,
                    user_data_dir=profile_dir
                )
            driver.set_page_load_timeout(30)
            self.inject_stealth_scripts(driver, self.profile)

            self.signals.status_update.emit(self.profile['id'], "🔄 Extracting Session...")

            driver.get("https://www.facebook.com")
            time.sleep(3) # Wait for page and cookies to load

            cookies = driver.get_cookies()
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=4)

            print(f"[{account_id}] Successfully extracted fresh cookies to {self.save_path}")

        except Exception as e:
            self.signals.error.emit((str(e),))
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            self.signals.finished.emit(self.profile['id'])


class AccountMonitorWorker(BaseBrowserWorker):
    """
    QRunnable thread instance to auto-login to FB, check status, and update the DB.
    """
    def __init__(self, profile_data):
        super().__init__()
        self.profile = profile_data
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        driver = None
        try:
            profile_id = self.profile['id']
            account_id = self.profile['account_id']
            email = self.profile.get('email', '').strip()
            password = self.profile.get('password', '').strip()

            base_dir = os.path.dirname(os.path.abspath(__file__))
            profile_dir = os.path.abspath(os.path.join(base_dir, 'profiles', f'id_{account_id}'))

            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            options.add_argument("--force-device-scale-factor=1")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--profile-directory=Default")

            # Explicitly set accept-languages to match proxy footprint
            locale = self.profile.get('locale', 'en-US')
            options.add_argument(f"--accept-lang={locale}")

            user_agent = self.profile.get('custom_user_agent', '').strip()
            if user_agent:
                options.add_argument(f'--user-agent={user_agent}')

            proxy_str = self.profile.get('account_proxy', '').strip()
            if proxy_str:
                parts = proxy_str.split(':')
                if len(parts) == 2:
                    options.add_argument(f'--proxy-server=http://{proxy_str}')
                elif len(parts) == 4:
                    ext_path = self.generate_proxy_extension(proxy_str, profile_dir)
                    if ext_path:
                        options.add_argument(f'--load-extension={ext_path}')

            self.force_clean_locks(profile_dir)

            try:
                driver = uc.Chrome(
                    options=options,
                    no_first_run=True,
                    user_data_dir=profile_dir,
                    version_main=146
                )
            except Exception as uc_err:
                print(f"[{account_id}] Warning: Failed to launch with version_main=146, trying default: {uc_err}")
                driver = uc.Chrome(
                    options=options,
                    no_first_run=True,
                    user_data_dir=profile_dir
                )
            driver.set_page_load_timeout(30)
            self.inject_stealth_scripts(driver, self.profile)

            ACTIVE_DRIVERS[profile_id] = driver

            driver.get("https://www.facebook.com")
            # Clear specific anti-bot tracking cookies before attempting login/status check
            try:
                driver.delete_cookie("wd")
                driver.delete_cookie("datr")
            except Exception:
                pass
            driver.refresh()

            time.sleep(5) # Let the page load initially

            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()

            # 1. Determine if already logged in by checking if email input exists
            try:
                # Use precise XPath as requested
                EMAIL_XPATH = "//input[@name='email']"
                wait = WebDriverWait(driver, 10)
                email_input = wait.until(EC.element_to_be_clickable((By.XPATH, EMAIL_XPATH)))
                needs_login = True
            except:
                needs_login = False

            if needs_login:
                if not email or not password:
                    update_profile_status(self.profile['id'], 'Missing Credentials')
                    return

                print(f"[{account_id}] Logging in...")
                try:
                    self.reliable_type(driver, email_input, email)
                    time.sleep(1.0) # 1-second verification pause to ensure email is correctly rendered

                    PASS_XPATH = "//input[@name='pass']"
                    wait = WebDriverWait(driver, 10)
                    pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, PASS_XPATH)))
                    self.reliable_type(driver, pass_input, password)
                    time.sleep(1.0) # Wait 1s before click as requested

                    # Focus Guard: Re-focus password before clicking to mimic user leaving the field
                    driver.execute_script("arguments[0].focus();", pass_input)
                    time.sleep(0.2)

                    LOGIN_BTN_XPATH = "//div[@aria-label='Log in' or @role='button'][@focusable='true']"
                    try:
                        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, LOGIN_BTN_XPATH)))
                        login_btn.click()
                    except Exception:
                        print(f"[{account_id}] Could not click div button, attempting secondary fallback RETURN on password field.")
                        try:
                            pass_input.send_keys(Keys.RETURN)
                        except Exception as inner_e:
                            print(f"[{account_id}] Secondary fallback also failed: {inner_e}")

                    time.sleep(15) # Wait for login redirect and possible 2FA/Save Info screens
                    current_url = driver.current_url.lower()
                    page_source = driver.page_source.lower()
                except Exception as e:
                    print(f"[{account_id}] Login interaction failed: {e}")
                    update_profile_status(self.profile['id'], 'Login UI Error')
                    return

            # 2. Evaluate Status
            status_text = "Unknown"

            if 'checkpoint' in current_url or 'locked' in page_source or 'suspicious activity' in page_source:
                status_text = '⚠️ Checkpoint'
            elif 'login/device-based' in current_url or 'incorrect password' in page_source or 'find your account' in page_source:
                status_text = '❌ Invalid'
            elif 'save-device' in current_url or 'save info' in page_source or 'login approval' in page_source or 'two-factor' in page_source:
                status_text = '⚠️ Needs Approval / Save Info'
            elif any(x in current_url for x in ['/home', '/feed', '?sk=h_chr', 'facebook.com/?sk=']):
                status_text = '✅ Active'
            elif current_url.strip('/') == 'https://www.facebook.com' and 'login' not in page_source:
                status_text = '✅ Active'
            else:
                # Intelligent DOM Check fallback
                try:
                    if driver.find_elements(By.CSS_SELECTOR, "div[role='navigation'], input[aria-label='Search Facebook'], svg[aria-label='Home']"):
                        status_text = '✅ Active'
                    else:
                        status_text = 'Unknown State'
                except:
                    status_text = 'Unknown State'

            print(f"[{account_id}] Final status determined: {status_text}")
            update_profile_status(self.profile['id'], status_text)

            # Update last active
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_last_active(self.profile['id'], now_str)

            if status_text in ['⚠️ Checkpoint', '❌ Invalid', '⚠️ Needs Approval / Save Info', 'Unknown State']:
                print(f"[{account_id}] Leaving browser open for 60 seconds for manual debug.")
                time.sleep(60)

        except Exception as e:
            self.signals.error.emit((str(e),))
        finally:
            if 'profile_id' in locals() and profile_id in ACTIVE_DRIVERS:
                del ACTIVE_DRIVERS[profile_id]
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            self.signals.finished.emit(self.profile['id'])
