import os
import json
import requests
from typing import Dict, Any

# ==========================================
# PILLAR 1: ZERO-HARDCODE REMOTE CONFIG
# ==========================================

# The singular hardcoded variable: The Remote URL
# Using the specific Google Docs direct download link as requested.
REMOTE_CONFIG_URL = "https://docs.google.com/uc?export=download&id=1mmf_SjR2dRWTEm-t4RQIHarblZWi0AhW"

class RemoteConfigManager:
    """
    Fetches and manages all dynamic XPaths, Branding, and the Kill-Switch.
    Caches the config locally to ensure offline usability if the remote server is down.
    """

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RemoteConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, cache_dir: str):
        if not hasattr(self, 'initialized'):
            self.cache_dir = cache_dir
            self.cache_file = os.path.join(cache_dir, "remote_config_cache.json")
            self.load_defaults()
            self.fetch_remote_config()
            self.initialized = True

    def load_defaults(self):
        """Generic fallback config in case remote fetching fails on first launch."""
        self._config = {
            "branding": {
                "tool_name": "FB Multi-Account Manager",
                "support_number": "+923490098654",
                "whatsapp_link": "https://wa.me/923490098654"
            },
            "selectors": {
                "login": {
                    "email": "//input[@name='email']",
                    "password": "//input[@name='pass']",
                    "login_btn": "//div[@aria-label='Log in' or @role='button'][@focusable='true']"
                },
                "marketplace": {
                    "title": "//label[.//span[text()='Title']]//input",
                    "price": "//label[.//span[text()='Price']]//input",
                    "condition_dropdown": "//div[@aria-label='Condition']",
                    "location": "//label[.//span[text()='Location']]//input",
                    "description": "//label[.//span[text()='Description']]//textarea",
                    "file_input": "//input[@type='file']",
                    "next_btn": "//div[@aria-label='Next' and @role='button']",
                    "publish_btn": "//div[@aria-label='Publish' and @role='button']"
                }
            },
            "banned_uuids": []
        }

    def fetch_remote_config(self):
        """Attempts to download the latest config. Falls back to local cache if unavailable."""
        try:
            # Short timeout to avoid hanging the app startup
            response = requests.get(REMOTE_CONFIG_URL, timeout=5)
            if response.status_code == 200:
                remote_data = response.json()
                self._config.update(remote_data)

                # Update local cache
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=4)
                print("Remote Config successfully fetched and cached.")
            else:
                self._load_from_local_cache()
        except Exception as e:
            print(f"Failed to fetch remote config: {e}. Falling back to cache.")
            self._load_from_local_cache()

    def _load_from_local_cache(self):
        """Loads from the cached JSON if the remote server is inaccessible."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    self._config.update(cached_data)
                print("Loaded config from local cache.")
            except Exception as e:
                print(f"Failed to read local cache: {e}. Using defaults.")

    def get(self, key_path: str, default=None) -> Any:
        """
        Safely retrieves nested keys. Example: get('selectors.marketplace.title')
        """
        keys = key_path.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def is_uuid_banned(self, current_uuid: str) -> bool:
        """The Revoker: Checks if the system UUID is in the banned list."""
        banned_list = self.get("banned_uuids", [])
        return current_uuid.strip() in banned_list

# Global accessor to be initialized by main.py
app_config = None

def init_config(app_dir: str) -> RemoteConfigManager:
    global app_config
    app_config = RemoteConfigManager(app_dir)
    return app_config
