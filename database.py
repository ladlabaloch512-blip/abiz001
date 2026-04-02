import sqlite3
import json
import threading
from typing import List, Dict, Any, Optional
from config import DB_PATH

# ------------------------------------------------------------------------------
# Database Management (Thread-Safe SQLite3)
# Handles Profiles, Session Cookies (JSON arrays), and Work Logs.
# ------------------------------------------------------------------------------

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH
        # Using a threading lock to ensure thread-safe writes/reads across worker threads
        self.lock = threading.Lock()
        self.init_db()

    def get_connection(self):
        """Returns a new SQLite connection. Must be called within the active thread."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        """Creates the necessary tables if they do not exist dynamically."""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Profiles Table: Stores general config and raw JSON cookies
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_name TEXT UNIQUE NOT NULL,
                    driver_config_name TEXT DEFAULT 'default',
                    proxy_url TEXT DEFAULT '',
                    cookies_json TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Work Logs Table: Stores historical execution data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER,
                    task_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (profile_id) REFERENCES profiles(id)
                )
            ''')

            conn.commit()
            conn.close()

    # --- Profile & Cookie Management ---

    def add_profile(self, profile_name: str, driver_config: str = "default", proxy_url: str = "", cookies: List[Dict] = None) -> bool:
        """Inserts a new profile. Cookies should be a list of dictionaries."""
        cookies_str = json.dumps(cookies) if cookies else "[]"
        with self.lock:
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO profiles (profile_name, driver_config_name, proxy_url, cookies_json)
                    VALUES (?, ?, ?, ?)
                ''', (profile_name, driver_config, proxy_url, cookies_str))
                conn.commit()
                conn.close()
                return True
            except sqlite3.IntegrityError:
                # Profile name already exists
                return False

    def update_profile_cookies(self, profile_id: int, cookies: List[Dict]) -> bool:
        """Updates the raw JSON cookie array for a specific profile."""
        cookies_str = json.dumps(cookies)
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE profiles SET cookies_json = ? WHERE id = ?
            ''', (cookies_str, profile_id))
            conn.commit()
            conn.close()
            return True

    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Returns all profiles as a list of dictionaries for the UI list."""
        with self.lock:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM profiles ORDER BY id ASC')
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

    def get_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a specific profile."""
        with self.lock:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

    # --- Logging Management ---

    def add_log(self, profile_id: int, task_name: str, status: str, details: str = ""):
        """Inserts a new execution log entry."""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO work_logs (profile_id, task_name, status, details)
                VALUES (?, ?, ?, ?)
            ''', (profile_id, task_name, status, details))
            conn.commit()
            conn.close()

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches recent logs, joining with the profile name for UI display."""
        with self.lock:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.id, p.profile_name, l.task_name, l.status, l.details, l.timestamp
                FROM work_logs l
                LEFT JOIN profiles p ON l.profile_id = p.id
                ORDER BY l.timestamp DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
