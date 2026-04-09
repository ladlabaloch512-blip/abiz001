import sys
import os

def get_app_dir():
    """
    Returns the absolute path to the directory containing the running script or executable.
    This safely handles PyInstaller's temporary `_MEIPASS` directory extraction for resources,
    but always ensures that persistent data like `profiles/` and `sys_config.db` are stored
    in the same folder as the final .exe, NOT the temp folder.
    """
    # Specific logic requested by user to ensure correct pathing regardless of nested folders
    if getattr(sys, 'frozen', False):
        # Running as a compiled PyInstaller executable
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Running as a normal Python script (assume script is inside a subdirectory like client_app or keygen_app)
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def get_resource_path(relative_path):
    """
    Returns absolute path to a bundled resource (like styles.qss or icons).
    Works for both dev and PyInstaller environments.
    """
    if getattr(sys, 'frozen', False):
        # Running as a compiled PyInstaller executable (resources are in _MEIPASS)
        base_path = sys._MEIPASS
    else:
        # Running as a normal Python script
        base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

    return os.path.join(base_path, relative_path)
