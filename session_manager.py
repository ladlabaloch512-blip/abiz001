import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from typing import Dict, Any, List

# ------------------------------------------------------------------------------
# Session Manager
# Maps User profiles (from Database) to Standard ChromeOptions()
# Handles Headless modes, Window Sizes, User-Agents, and Cookie Injection.
# ------------------------------------------------------------------------------

class SessionManager:
    def __init__(self, headless_override: bool = False):
        self.headless_override = headless_override

    def create_driver_for_profile(self, profile_data: Dict[str, Any]) -> webdriver.Chrome:
        """
        Instantiates a standard Selenium Chrome WebDriver based on profile configurations.
        """
        options = Options()

        # 1. Base Configurations
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")

        # 2. Window Size based on simulated device/config
        config_name = profile_data.get('driver_config_name', 'default').lower()
        if 'mobile' in config_name:
            options.add_argument("--window-size=375,812") # iPhone X dimensions
            options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1")
        else:
            options.add_argument("--window-size=1280,800") # Standard desktop
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # 3. Headless Argument
        if self.headless_override:
            options.add_argument("--headless")

        # 4. Proxy Configuration
        proxy_url = profile_data.get('proxy_url', '')
        if proxy_url:
             options.add_argument(f'--proxy-server={proxy_url}')

        # Instantiate Driver
        # Using standard selenium initialization (requires chromedriver in PATH or selenium manager will auto-fetch)
        driver = webdriver.Chrome(options=options)

        # Implicit waits for basic finding
        driver.implicitly_wait(10)

        # 5. Inject Cookies
        cookies_json = profile_data.get('cookies_json', '[]')
        self._inject_cookies(driver, cookies_json)

        return driver

    def _inject_cookies(self, driver: webdriver.Chrome, cookies_json_str: str):
        """
        Parses JSON cookies and adds them to the driver session securely.
        Selenium requires the browser to be on the domain the cookie belongs to before adding it.
        """
        try:
            cookies: List[Dict] = json.loads(cookies_json_str)
            if not cookies:
                return

            # Group cookies by domain to visit them before injection
            domain_groups = {}
            for cookie in cookies:
                domain = cookie.get('domain', '')
                # Clean leading dot for URL construction
                if domain.startswith('.'):
                    domain = domain[1:]
                if not domain:
                    continue

                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(cookie)

            # Navigate to each domain briefly to set its cookies
            for domain, domain_cookies in domain_groups.items():
                try:
                    driver.get(f"https://{domain}")
                    for cookie in domain_cookies:
                        # Selenium accepts standard dicts, ensure keys match what selenium expects
                        safe_cookie = {
                            'name': cookie.get('name'),
                            'value': cookie.get('value'),
                            'domain': cookie.get('domain'),
                            'path': cookie.get('path', '/')
                        }
                        # Only add if name and value exist
                        if safe_cookie['name'] and safe_cookie['value']:
                            driver.add_cookie(safe_cookie)
                except Exception as e:
                    print(f"Failed to inject cookies for domain {domain}: {e}")

        except json.JSONDecodeError:
            print("Invalid cookie JSON format in database.")

    def extract_and_save_cookies(self, driver: webdriver.Chrome, db_manager: Any, profile_id: int):
        """
        Extracts the current session cookies from the browser and saves them back to the database.
        Call this after a successful login task.
        """
        try:
            current_cookies = driver.get_cookies()
            db_manager.update_profile_cookies(profile_id, current_cookies)
        except Exception as e:
            print(f"Failed to extract cookies: {e}")
