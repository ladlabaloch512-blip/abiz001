import os
from pathlib import Path

import sys

# --- Core Directory Configurations ---
# Resolve the true base directory whether running from script or PyInstaller standalone
if getattr(sys, 'frozen', False):
    # If compiled, the base dir is where the .exe is located
    BASE_DIR = Path(sys.executable).parent.absolute()
else:
    # If script, the base dir is the directory of this file
    BASE_DIR = Path(__file__).parent.absolute()

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "database.sqlite3"
LOCATORS_PATH = BASE_DIR / "locators.json"
LICENSE_PATH = BASE_DIR / "license.key"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Concurrency & Threading Caps ---
# Caps the number of parallel selenium instances filling web forms to prevent RAM exhaustion.
DEFAULT_MAX_WORKERS = 5

# --- Selenium Driver Settings ---
# Standard driver configuration defaults
HEADLESS_MODE_DEFAULT = False
PAGE_LOAD_TIMEOUT = 60
IMPLICIT_WAIT_TIMEOUT = 10
EXPLICIT_WAIT_TIMEOUT = 20

# --- Human Simulation Delay Logic (Seconds) ---
# Used for locally configured wait periods between standard interactions
MIN_WAIT_DELAY = 1.0
MAX_WAIT_DELAY = 3.5

# --- UI Threading ---
# How often the Main GUI thread should poll the background Queue for logs (ms)
GUI_QUEUE_POLL_RATE_MS = 100
