import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from PyQt6.QtWidgets import QMessageBox

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveSyncService:
    """
    Handles the Google OAuth2 authentication flow to allow private user sync
    of sys_config_v2.db and Cookie ZIP files.
    """
    def __init__(self, app_dir: str):
        self.app_dir = app_dir
        self.token_file = os.path.join(self.app_dir, 'token.json')
        # Placeholder for actual client_secret.json downloaded from Google Cloud Console
        self.credentials_file = os.path.join(self.app_dir, 'credentials.json')

    def authenticate(self, ui_parent):
        """
        Executes the OAuth 2.0 flow using a local server.
        """
        if not os.path.exists(self.credentials_file):
            QMessageBox.warning(ui_parent, "Missing Credentials",
                                "The Google Cloud OAuth credentials.json file is missing.\n"
                                "Please place it in the application root directory.")
            return False

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                print(f"Error reading existing token: {e}")

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    creds = self._run_auth_flow(ui_parent)
            else:
                creds = self._run_auth_flow(ui_parent)

            if creds:
                # Save the credentials for the next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())

        if creds and creds.valid:
            QMessageBox.information(ui_parent, "Authentication Success", "Successfully linked to Google Drive.\nSync services are now active.")
            return True
        return False

    def _run_auth_flow(self, ui_parent):
        try:
            QMessageBox.information(ui_parent, "OAuth Setup", "A browser window will now open to securely authenticate with your Google account.")
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
            # Local server flow automatically opens the browser and handles the redirect URI
            creds = flow.run_local_server(port=0)
            return creds
        except Exception as e:
            QMessageBox.critical(ui_parent, "Authentication Error", f"Failed to complete Google OAuth flow:\n{e}")
            return None
