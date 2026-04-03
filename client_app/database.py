import sqlite3
import os
import sys

# Ensure shared_logic can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared_logic.config import DB_NAME
from shared_logic.utils import get_app_dir

def get_db_connection():
    """
    Establish and return a connection to the SQLite database.
    Creates the database file if it doesn't exist.
    Resolves the DB path relative to the final executable's location.
    """
    base_dir = get_app_dir()
    db_path = os.path.join(base_dir, DB_NAME)

    # Ensure the directory exists if running as an executable
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database schema if it hasn't been created yet.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_name TEXT NOT NULL,
            account_id TEXT NOT NULL UNIQUE,
            account_proxy TEXT,
            status TEXT DEFAULT 'Pending',
            custom_user_agent TEXT,
            cookie_data TEXT,
            last_active TEXT,
            email TEXT,
            password TEXT,
            status_text TEXT DEFAULT 'Pending',
            stealth_ua TEXT,
            canvas_noise TEXT,
            webgl_noise TEXT,
            tz TEXT,
            locale TEXT,
            fingerprint_salt TEXT,
            group_name TEXT DEFAULT 'Default'
        )
    ''')

    # Robust Migration System using PRAGMA
    cursor.execute("PRAGMA table_info(profiles)")
    existing_columns = [row['name'] for row in cursor.fetchall()]

    columns_to_add = {
        'last_active': 'TEXT',
        'email': 'TEXT',
        'password': 'TEXT',
        'status_text': "TEXT DEFAULT 'Pending'",
        'stealth_ua': 'TEXT',
        'canvas_noise': 'TEXT',
        'webgl_noise': 'TEXT',
        'tz': 'TEXT',
        'locale': 'TEXT',
        'fingerprint_salt': 'TEXT',
        'group_name': "TEXT DEFAULT 'Default'"
    }

    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError as e:
                print(f"Migration error for {col_name}: {e}")

    # Update existing User-Agents to strictly match the new v114.0.0.0 anti-detect logic
    cursor.execute("""
        UPDATE profiles
        SET stealth_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        WHERE stealth_ua IS NOT NULL AND stealth_ua != 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    """)

    # Create the groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL UNIQUE
        )
    ''')

    # Indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_account_id ON profiles(account_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON profiles(status);')

    conn.commit()
    conn.close()

# CRUD Methods for Module 2

import random
import string

def generate_stealth_footprint():
    """Generates permanent unique fingerprinting parameters for a new profile."""
    chrome_vers = "114.0.0.0" # Strict alignment with v114 binaries (simplified as requested)
    webkit_vers = "537.36"
    ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{webkit_vers} (KHTML, like Gecko) Chrome/{chrome_vers} Safari/{webkit_vers}"

    tz = random.choice(["America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London"])
    locale = random.choice(["en-US", "en-GB", "en-CA"])

    canvas_noise = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    webgl_noise = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    fingerprint_salt = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    return ua, canvas_noise, webgl_noise, tz, locale, fingerprint_salt

def add_profile(profile_name, account_id, proxy="", custom_user_agent="", email="", password=""):
    conn = get_db_connection()
    cursor = conn.cursor()

    ua, canvas_noise, webgl_noise, tz, locale, fingerprint_salt = generate_stealth_footprint()
    if custom_user_agent:
        ua = custom_user_agent

    try:
        cursor.execute('''
            INSERT INTO profiles (
                profile_name, account_id, account_proxy, custom_user_agent,
                last_active, email, password, status_text,
                stealth_ua, canvas_noise, webgl_noise, tz, locale, fingerprint_salt
            )
            VALUES (?, ?, ?, ?, 'Never', ?, ?, 'Pending', ?, ?, ?, ?, ?, ?)
        ''', (profile_name, account_id, proxy, custom_user_agent, email, password, ua, canvas_noise, webgl_noise, tz, locale, fingerprint_salt))
        conn.commit()
        return True, "Profile added successfully."
    except sqlite3.IntegrityError:
        return False, "Account ID already exists."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        # Failsafe if the table genuinely hasn't been created yet
        return []

def get_next_sequential_id():
    """Finds the highest 'idX' from the profile_name column to ensure unique monotonic naming."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profile_name FROM profiles WHERE profile_name LIKE 'id%'")
    rows = cursor.fetchall()
    conn.close()

    max_id = 0
    for row in rows:
        name = row['profile_name']
        try:
            num = int(name[2:])
            if num > max_id:
                max_id = num
        except ValueError:
            pass

    return max_id + 1

def bulk_insert_profiles(profiles_data):
    """
    Inserts multiple profiles in a single transaction for high performance.
    profiles_data is a list of tuples:
    (profile_name, account_id, account_proxy, custom_user_agent, email, password)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    success_count = 0
    for data in profiles_data:
        profile_name, account_id, proxy, custom_user_agent, email, password = data
        ua, canvas_noise, webgl_noise, tz, locale, fingerprint_salt = generate_stealth_footprint()
        if custom_user_agent:
            ua = custom_user_agent

        try:
            cursor.execute('''
                INSERT INTO profiles (
                    profile_name, account_id, account_proxy, custom_user_agent,
                    last_active, email, password, status_text,
                    stealth_ua, canvas_noise, webgl_noise, tz, locale, fingerprint_salt
                )
                VALUES (?, ?, ?, ?, 'Never', ?, ?, 'Pending', ?, ?, ?, ?, ?, ?)
            ''', (profile_name, account_id, proxy, custom_user_agent, email, password, ua, canvas_noise, webgl_noise, tz, locale, fingerprint_salt))
            success_count += 1
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()
    return success_count

def get_profile_stats():
    """Returns a tuple of (Total, Active, Checkpoint) counts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM profiles")
    total = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM profiles WHERE status_text LIKE '%Active%'")
    active = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM profiles WHERE status_text LIKE '%Checkpoint%'")
    checkpoint = cursor.fetchone()['count']

    conn.close()
    return total, active, checkpoint

def delete_profile(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM profiles WHERE id = ?', (profile_id,))
    conn.commit()
    conn.close()

def update_last_active(profile_id, time_str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE profiles SET last_active = ? WHERE id = ?', (time_str, profile_id))
    conn.commit()
    conn.close()

def update_profile_status(profile_id, status_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE profiles SET status_text = ? WHERE id = ?', (status_text, profile_id))
    conn.commit()
    conn.close()

def update_profile_group(profile_id, group_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE profiles SET group_name = ? WHERE id = ?', (group_name, profile_id))
    conn.commit()
    conn.close()

def update_profile_proxy(profile_id, proxy_str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE profiles SET account_proxy = ? WHERE id = ?', (proxy_str, profile_id))
    conn.commit()
    conn.close()

def get_all_groups():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM groups ORDER BY group_name ASC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []

def add_group(group_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO groups (group_name) VALUES (?)', (group_name,))
        conn.commit()
        return True, "Group added successfully."
    except sqlite3.IntegrityError:
        return False, "Group already exists."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_group(group_id, group_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Optional: Reassign profiles to 'Default' when their group is deleted
    cursor.execute("UPDATE profiles SET group_name = 'Default' WHERE group_name = ?", (group_name,))

    cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Initialize the DB if run as a script directly
    init_db()
    db_path = os.path.join(get_app_dir(), DB_NAME)
    print(f"Database '{DB_NAME}' initialized successfully at {db_path}")
