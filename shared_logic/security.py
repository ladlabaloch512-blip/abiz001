import subprocess
import os
import json
from datetime import datetime
from cryptography.fernet import Fernet
from shared_logic.config import SECRET_KEY

def get_hardware_uuid():
    """
    Fetches the hardware UUID.
    Uses 'wmic csproduct get uuid' on Windows.
    On Linux (for testing purposes), falls back to reading /etc/machine-id.
    """
    try:
        if os.name == 'nt':
            # Windows
            output = subprocess.check_output('wmic csproduct get uuid', shell=True).decode()
            # Parse the output to get just the UUID string
            lines = output.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
        else:
            # Linux fallback
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
    except Exception as e:
        print(f"Error fetching UUID: {e}")
        return "UNKNOWN_UUID"

def generate_license_data(uuid_str, expiry_date_str):
    """
    Generates encrypted license data for the given UUID and Expiry Date.
    Also stores an issue_date to prevent basic back-dating.
    expiry_date_str should be in 'YYYY-MM-DD' format.
    """
    issue_date_str = datetime.now().strftime('%Y-%m-%d')

    payload = {
        'uuid': uuid_str,
        'issue_date': issue_date_str,
        'expiry_date': expiry_date_str
    }

    payload_json = json.dumps(payload)

    f = Fernet(SECRET_KEY)
    # Ensure JSON string is a bytes object for encryption
    encrypted_data = f.encrypt(payload_json.encode('utf-8'))
    return encrypted_data

def verify_license(license_file_path):
    """
    Reads the license file, decrypts it, and checks:
    1. If the hardware UUID matches.
    2. If the current system date is <= the Expiry Date.
    3. Anti-back-dating check: If the current system date is >= the Issue Date.
    Returns (is_valid, message).
    """
    if not os.path.exists(license_file_path):
        return False, "License file not found."

    try:
        with open(license_file_path, 'rb') as f:
            encrypted_data = f.read()

        fernet = Fernet(SECRET_KEY)
        decrypted_json_str = fernet.decrypt(encrypted_data).decode('utf-8')

        # Parse the JSON payload
        payload = json.loads(decrypted_json_str)
        stored_uuid = payload.get('uuid')
        issue_date_str = payload.get('issue_date')
        expiry_date_str = payload.get('expiry_date')

        # 1. UUID Match Check
        current_uuid = get_hardware_uuid()
        if stored_uuid != current_uuid:
            return False, "Hardware UUID mismatch."

        # Parse dates
        current_date = datetime.now().date()
        try:
            issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            return False, "Invalid date format in license."

        # 2. Expiry Check
        if current_date > expiry_date:
            return False, "License Expired."

        # 3. Anti Back-Dating Check
        if current_date < issue_date:
            return False, "System clock tampered (back-dated). License invalidated."

        return True, "License Valid"

    except Exception as e:
        print(f"License verification failed: {e}")
        return False, "Invalid or corrupted license file."
