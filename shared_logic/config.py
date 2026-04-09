# shared_logic/config.py

# A secure 32-byte URL-safe base64-encoded key for Fernet encryption.
# You can generate a new one using: from cryptography.fernet import Fernet; Fernet.generate_key()
SECRET_KEY = b'nYjs38pZojN8qayoajbzcqqnP0OmTeun_VxqYZcDOQw='

# Placeholder for the WhatsApp link
BUY_LINK = 'https://wa.me/YOUR_PHONE_NUMBER'

# Database name (kept generic for privacy)
DB_NAME = 'sys_config.db'
