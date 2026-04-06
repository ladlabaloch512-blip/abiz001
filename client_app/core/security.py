import os
import subprocess
import json
from datetime import datetime
from cryptography.fernet import Fernet
import sys

# The fixed Secret Key known only to the developer.
from shared_logic.config import SECRET_KEY

def get_hardware_uuid():
    """
    Retrieves the machine's UUID via wmic on Windows, ensuring no empty strings or trailing spaces.
    Falls back to reading /etc/machine-id on Linux for cross-platform debugging.
    """
    try:
        if os.name == 'nt':
            output = subprocess.check_output('wmic csproduct get uuid', shell=True, text=True)
            # The output has "UUID" as header, then the actual UUID.
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            if len(lines) >= 2:
                # Typically the second line is the UUID
                uuid = lines[1]
                if uuid and uuid != "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
                    return uuid
        else:
            # Linux fallback
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
    except Exception as e:
        print(f"Failed to fetch hardware UUID: {e}")

    # Ultimate fallback if wmic is disabled/fails
    import uuid
    return str(uuid.getnode())

def get_cipher():
    """Returns the Fernet cipher object initialized with the secret key."""
    return Fernet(SECRET_KEY)

def verify_license(current_uuid, license_path=None):
    """
    Reads the license.dat file, decrypts it, and verifies:
    1. The UUID matches the current system UUID.
    2. The license is not expired.

    Robust Pathing: It checks os.getcwd() first (where the user ran the script),
    then falls back to the provided `license_path` (usually sys._MEIPASS).
    """

    # 1. Path Resolution
    cwd_path = os.path.join(os.getcwd(), 'license.dat')

    actual_path = None
    if os.path.exists(cwd_path):
        actual_path = cwd_path
    elif license_path and os.path.exists(license_path):
        actual_path = license_path

    if not actual_path:
        print(f"License file not found at {cwd_path} or {license_path}")
        return False

    print(f"Found license at: {actual_path}")

    # 2. Decrypt and Verify
    try:
        with open(actual_path, 'rb') as f:
            encrypted_data = f.read()

        cipher = get_cipher()
        decrypted_data = cipher.decrypt(encrypted_data).decode('utf-8')

        license_info = json.loads(decrypted_data)

        # Check UUID
        licensed_uuid = license_info.get('uuid')
        if not licensed_uuid or licensed_uuid.strip() != current_uuid.strip():
            print("License UUID mismatch.")
            print(f"Expected: {licensed_uuid}")
            print(f"System:   {current_uuid}")
            return False

        # Check Expiry
        expiry_date_str = license_info.get('expiry_date')
        if expiry_date_str and expiry_date_str != "Never":
            try:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
                if datetime.now() > expiry_date:
                    print("License has expired.")
                    return False
            except ValueError:
                print("Invalid expiry date format in license.")
                return False

        return True

    except Exception as e:
        print(f"License verification failed (Decryption/Format Error): {e}")
        return False
