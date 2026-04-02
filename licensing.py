import os
import subprocess
from cryptography.fernet import Fernet
from config import LICENSE_PATH

# ------------------------------------------------------------------------------
# Security Note: This uses standard AES-128 encryption via Fernet.
# The master key used to sign the tokens must be kept secret by the developer.
# In a real-world scenario, this should be obfuscated or fetched securely,
# but for this generic desktop tool architecture, it is hardcoded here.
# ------------------------------------------------------------------------------
MASTER_KEY = b'G9y9_vA1QO0W4kE1z2sO-P_Ld0e5_1m_zPqO1_wD0c8='

def get_hardware_uuid() -> str:
    """
    Fetches a permanent hardware identifier using standard OS commands.
    On Windows, it uses WMIC to get the baseboard or CSPRODUCT UUID.
    Falls back to a generic ID string if the command fails (e.g., non-Windows OS).
    """
    if os.name == 'nt':
        try:
            # Using WMIC to get the CSPRODUCT UUID
            output = subprocess.check_output(
                "wmic csproduct get uuid",
                shell=True,
                text=True
            )
            # Parse the output: The first line is "UUID", the second is the actual ID.
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            if len(lines) > 1:
                return lines[1]
            return "UNKNOWN-WINDOWS-UUID"
        except Exception:
            return "ERROR-FETCHING-UUID"
    else:
        # For non-Windows platforms (development/testing)
        return "DEV-MACHINE-NON-WINDOWS"

def generate_license_token(hardware_id: str) -> str:
    """
    Generates an encrypted AES token binding the software to the specific hardware UUID.
    Used exclusively by the Keygen Developer Tool.
    """
    f = Fernet(MASTER_KEY)
    encrypted_token = f.encrypt(hardware_id.encode('utf-8'))
    return encrypted_token.decode('utf-8')

def verify_license() -> bool:
    """
    Validates if the current machine possesses a valid license.key file
    that decrypts to the current machine's hardware UUID.
    """
    if not LICENSE_PATH.exists():
        return False

    try:
        with open(LICENSE_PATH, 'r') as file:
            encrypted_token = file.read().strip()

        f = Fernet(MASTER_KEY)
        decrypted_uuid = f.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')

        current_uuid = get_hardware_uuid()

        return decrypted_uuid == current_uuid
    except Exception:
        # Catch decryption errors (InvalidToken), file read errors, etc.
        return False

def save_license(token: str) -> bool:
    """
    Saves the provided license token to the license.key file.
    """
    try:
        with open(LICENSE_PATH, 'w') as file:
            file.write(token.strip())
        return True
    except Exception:
        return False
