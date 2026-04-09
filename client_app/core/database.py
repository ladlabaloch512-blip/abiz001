import sqlite3
import os
import json

# ==========================================
# PRODUCTION DATABASE SCHEMA (Core Foundation)
# ==========================================
DB_NAME = 'sys_config_v2.db'

def get_db_connection(app_dir: str) -> sqlite3.Connection:
    """Create a database connection ensuring it lives in the root app directory."""
    db_path = os.path.join(app_dir, DB_NAME)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(app_dir: str):
    """
    Initializes the production-level schema.
    Includes Profiles, Groups, and Global_Cache tables.
    """
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()

    # 1. Groups Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profile_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT UNIQUE NOT NULL
    )
    ''')

    # Ensure "Default" group always exists
    cursor.execute("INSERT OR IGNORE INTO profile_groups (group_name) VALUES ('Default')")

    # 2. Profiles Table (Expanded Metadata)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_name TEXT UNIQUE NOT NULL,
        account_id TEXT UNIQUE NOT NULL,
        group_id INTEGER DEFAULT 1,
        account_proxy TEXT,
        custom_user_agent TEXT,
        email TEXT,
        password TEXT,
        last_active TEXT,
        status TEXT DEFAULT 'Ready',
        stealth_data TEXT,
        cookies_blob TEXT,
        FOREIGN KEY(group_id) REFERENCES profile_groups(id)
    )
    ''')

    # 3. Global Cache Table (For remote syncing state, task queues, etc.)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS global_cache (
        key_name TEXT PRIMARY KEY,
        value_data TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # --- Migration block for backwards compatibility if needed ---
    # In a pure refactor, we usually start fresh or migrate existing.
    # For now, we ensure the new schema rules apply.

    conn.commit()
    conn.close()

# --- Profiles CRUD Operations (Immediate Commits) ---

def get_all_profiles(app_dir: str):
    try:
        conn = get_db_connection(app_dir)
        # JOIN with groups table to return the group_name instantly
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, g.group_name
            FROM profiles p
            LEFT JOIN profile_groups g ON p.group_id = g.id
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []

def add_profile(app_dir: str, profile_name: str, account_id: str, group_name: str = "Default",
                proxy: str = "", user_agent: str = "", email: str = "", password: str = "", stealth_data: dict = None):
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    try:
        # Resolve group_id
        cursor.execute("SELECT id FROM profile_groups WHERE group_name = ?", (group_name,))
        grp = cursor.fetchone()
        group_id = grp['id'] if grp else 1

        stealth_str = json.dumps(stealth_data) if stealth_data else "{}"

        cursor.execute('''
            INSERT INTO profiles (profile_name, account_id, group_id, account_proxy, custom_user_agent, email, password, status, stealth_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Ready', ?)
        ''', (profile_name, account_id, group_id, proxy, user_agent, email, password, stealth_str))
        conn.commit()
        return True, "Success"
    except sqlite3.IntegrityError:
        return False, "Profile with that Name or Account ID already exists."
    finally:
        conn.close()

def update_profile_status(app_dir: str, profile_id: int, new_status: str):
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute("UPDATE profiles SET status = ? WHERE id = ?", (new_status, profile_id))
    conn.commit()
    conn.close()

def update_last_active(app_dir: str, profile_id: int, timestamp: str):
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute("UPDATE profiles SET last_active = ? WHERE id = ?", (timestamp, profile_id))
    conn.commit()
    conn.close()

def delete_profile(app_dir: str, profile_id: int):
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()

def get_next_sequential_id(app_dir: str) -> int:
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute("SELECT profile_name FROM profiles")
    rows = cursor.fetchall()
    conn.close()

    max_id = 0
    for r in rows:
        name = r['profile_name']
        if name.startswith('id'):
            try:
                num = int(name[2:])
                if num > max_id:
                    max_id = num
            except ValueError:
                pass
    return max_id + 1

# --- Groups CRUD ---
def get_all_groups(app_dir: str):
    try:
        conn = get_db_connection(app_dir)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profile_groups ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []

def add_group(app_dir: str, group_name: str):
    if not group_name or group_name.lower() == 'default':
        return False
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO profile_groups (group_name) VALUES (?)", (group_name.strip(),))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_group(app_dir: str, group_name: str):
    if not group_name or group_name.lower() == 'default':
        return False
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM profile_groups WHERE group_name = ?", (group_name,))
    grp = cursor.fetchone()
    if grp:
        grp_id = grp['id']
        cursor.execute("UPDATE profiles SET group_id = 1 WHERE group_id = ?", (grp_id,))
        cursor.execute("DELETE FROM profile_groups WHERE id = ?", (grp_id,))
        conn.commit()
    conn.close()
    return True

def update_profile_group(app_dir: str, profile_id: int, group_name: str):
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM profile_groups WHERE group_name = ?", (group_name,))
    grp = cursor.fetchone()
    if grp:
        cursor.execute("UPDATE profiles SET group_id = ? WHERE id = ?", (grp['id'], profile_id))
        conn.commit()
    conn.close()

def update_profile_proxy(app_dir: str, profile_id: int, proxy: str):
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute("UPDATE profiles SET account_proxy = ? WHERE id = ?", (proxy, profile_id))
    conn.commit()
    conn.close()

# --- Global Cache CRUD ---
def set_cache(app_dir: str, key: str, value: str):
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO global_cache (key_name, value_data)
        VALUES (?, ?)
        ON CONFLICT(key_name) DO UPDATE SET value_data=excluded.value_data, last_updated=CURRENT_TIMESTAMP
    ''', (key, value))
    conn.commit()
    conn.close()

def get_cache(app_dir: str, key: str) -> str:
    conn = get_db_connection(app_dir)
    cursor = conn.cursor()
    cursor.execute("SELECT value_data FROM global_cache WHERE key_name = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value_data'] if row else None
