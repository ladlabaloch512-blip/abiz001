import os
import json
import uuid
import shutil
import zipfile
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QInputDialog
from PyQt6.QtCore import Qt

from core.database import (get_all_profiles, add_profile, delete_profile,
                           get_next_sequential_id, add_group, delete_group,
                           get_all_groups, update_profile_group, update_profile_proxy,
                           update_profile_status)

# Need the specific background workers for session extraction/injection
# We can port those over to services/task_runner or use a localized thread
from services.task_runner import ACTIVE_LAUNCHERS, BrowserTaskWorker

class ProfileService:
    """
    Houses all business logic for profile data creation, migration,
    deletion, grouping, and external attachment to keep the UI class pure.
    """
    def __init__(self, ui_instance, app_dir: str):
        self.ui = ui_instance
        self.app_dir = app_dir
        self.profiles_base = os.path.join(self.app_dir, 'profiles')

    # ==========================================
    # 📂 MIGRATION & DATA (IMPORT/EXPORT)
    # ==========================================

    def import_profiles_from_txt(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self.ui, "Select Bulk Accounts TXT", "", "Text Files (*.txt);;All Files (*)", options=options)

        if not file_path:
            return

        success_count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                parts = line.strip().split('|')
                email, password, proxy = "", "", ""

                if len(parts) >= 2:
                    email = parts[0]
                    password = parts[1]
                if len(parts) == 3:
                    proxy = parts[2]

                if email and password:
                    account_id = str(uuid.uuid4())[:8]
                    next_seq = get_next_sequential_id(self.app_dir)
                    profile_name = f"id{next_seq}"
                    success, _ = add_profile(self.app_dir, profile_name, account_id, "Default", proxy, "", email, password)
                    if success:
                        success_count += 1

            self.ui.load_table_data()
            QMessageBox.information(self.ui, "Import Complete", f"Successfully imported {success_count} accounts from TXT.")
        except Exception as e:
            QMessageBox.critical(self.ui, "Import Error", f"Failed to read TXT file:\n{e}")

    def import_via_cookies(self):
        options = QFileDialog.Option.ShowDirsOnly
        folder_path = QFileDialog.getExistingDirectory(self.ui, "Select Folder containing JSON Cookie files", "", options=options)

        if not folder_path:
            return

        imported_count = 0
        try:
            for filename in os.listdir(folder_path):
                if filename.endswith('.json'):
                    json_path = os.path.join(folder_path, filename)

                    account_id = str(uuid.uuid4())[:8]
                    next_seq = get_next_sequential_id(self.app_dir)
                    profile_name = f"id{next_seq}"

                    success, _ = add_profile(self.app_dir, profile_name, account_id)
                    if success:
                        target_dir = os.path.join(self.profiles_base, f"id_{account_id}")
                        os.makedirs(target_dir, exist_ok=True)

                        # Copy as portable_session.json to trigger Auto-Inject logic in Pillar 2
                        dst_path = os.path.join(target_dir, 'portable_session.json')
                        shutil.copy(json_path, dst_path)
                        imported_count += 1

            self.ui.load_table_data()
            QMessageBox.information(self.ui, "Import Complete", f"Successfully built {imported_count} profiles from cookie files.")
        except Exception as e:
            QMessageBox.critical(self.ui, "Import Error", f"Failed to read folder:\n{e}")

    def execute_bulk_export(self, selected_ids: list):
        if not selected_ids:
            QMessageBox.warning(self.ui, "Selection Error", "Please select at least one profile to export.")
            return

        options = QFileDialog.Option.ShowDirsOnly
        export_dir = QFileDialog.getExistingDirectory(self.ui, "Select Export Destination Folder", "", options=options)
        if not export_dir:
            return

        profiles = get_all_profiles(self.app_dir)
        db_path = os.path.join(self.app_dir, 'sys_config_v2.db')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"FB_Profiles_Export_{timestamp}.zip"
        zip_path = os.path.join(export_dir, zip_filename)

        QMessageBox.information(self.ui, "Export Started", "Profile export started.\nZIP payload being created...")

        exported_count = 0
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(db_path):
                    zipf.write(db_path, 'sys_config_v2.db')

                for p in profiles:
                    if p['id'] in selected_ids:
                        target_folder = os.path.join(self.profiles_base, f"id_{p['account_id']}")
                        if os.path.exists(target_folder):
                            # The portable_session.json should already exist in the folder due to Pillar 2 (Zero-Resource killer extracts it on close).
                            # We just zip the folder and its specific metadata.
                            exported_count += 1
                            for root, dirs, files in os.walk(target_folder):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, self.app_dir)
                                    zipf.write(file_path, arcname)

                            meta_str = json.dumps(p, indent=4)
                            zipf.writestr(f"profiles/id_{p['account_id']}/profile_info.json", meta_str)

            if exported_count > 0:
                QMessageBox.information(self.ui, "Export Complete", f"Successfully exported {exported_count} profiles to:\n{zip_path}")
            else:
                QMessageBox.warning(self.ui, "Export Failed", "No valid profile directories were found to export.")
                os.remove(zip_path)
        except Exception as e:
            QMessageBox.critical(self.ui, "Export Error", f"An error occurred during export:\n{str(e)}")

    def execute_import_backup(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self.ui, "Select Backup ZIP File", "", "ZIP Files (*.zip)", options=options)
        if not file_path:
            return

        QMessageBox.information(self.ui, "Import Started", "Profile import started. Please wait...")

        imported_count = 0
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                for member in zipf.namelist():
                    if member.endswith('profile_info.json'):
                        with zipf.open(member) as f:
                            meta_data = json.loads(f.read().decode('utf-8'))

                        old_acc_id = meta_data.get('account_id')
                        if not old_acc_id: continue

                        new_acc_id = str(uuid.uuid4())[:8]
                        next_seq = get_next_sequential_id(self.app_dir)
                        new_profile_name = f"id{next_seq}"

                        success, _ = add_profile(self.app_dir, new_profile_name, new_acc_id,
                                               meta_data.get('group_name', 'Default'),
                                               meta_data.get('account_proxy', ''),
                                               meta_data.get('custom_user_agent', ''),
                                               meta_data.get('email', ''),
                                               meta_data.get('password', ''))
                        if success:
                            imported_count += 1
                            target_dir = os.path.join(self.profiles_base, f"id_{new_acc_id}")
                            os.makedirs(target_dir, exist_ok=True)

                            old_prefix = f"profiles/id_{old_acc_id}/".replace('\\', '/')
                            for sub_member in zipf.namelist():
                                sub_member_norm = sub_member.replace('\\', '/')
                                if sub_member_norm.startswith(old_prefix) and not sub_member_norm.endswith('profile_info.json'):
                                    rel_path = sub_member_norm[len(old_prefix):]
                                    if rel_path:
                                        out_path = os.path.join(target_dir, os.path.normpath(rel_path))
                                        os.makedirs(os.path.dirname(out_path), exist_ok=True)
                                        if not sub_member_norm.endswith('/'):
                                            with zipf.open(sub_member) as source, open(out_path, "wb") as target:
                                                shutil.copyfileobj(source, target)

            self.ui.load_table_data()
            QMessageBox.information(self.ui, "Import Complete", f"Successfully imported {imported_count} profiles. Portable sessions are ready to be automatically injected upon Launch.")
        except Exception as e:
            QMessageBox.critical(self.ui, "Import Error", f"Failed to restore backup:\n{str(e)}")

    # ==========================================
    # 🔢 MANAGEMENT (CREATE/DELETE/WIPE)
    # ==========================================

    def bulk_empty_create(self):
        count, ok = QInputDialog.getInt(self.ui, "Bulk Create Empty", "Number of generic profiles to create:", 1, 1, 100, 1)
        if ok and count > 0:
            created = 0
            for _ in range(count):
                account_id = str(uuid.uuid4())[:8]
                next_seq = get_next_sequential_id(self.app_dir)
                profile_name = f"id{next_seq}"

                success, _ = add_profile(self.app_dir, profile_name, account_id)
                if success:
                    created += 1

            self.ui.load_table_data()
            QMessageBox.information(self.ui, "Created", f"Successfully generated {created} empty profiles.")

    def execute_bulk_delete(self, selected_ids: list):
        if not selected_ids:
            QMessageBox.warning(self.ui, "Selection Error", "Please select at least one profile to delete.")
            return

        reply = QMessageBox.warning(self.ui, 'Confirm Deletion',
                                     f"Are you sure you want to permanently delete {len(selected_ids)} selected profiles?\nThis will destroy local storage and cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            deleted = 0
            profiles = get_all_profiles(self.app_dir)

            for profile_id in selected_ids:
                if profile_id in ACTIVE_LAUNCHERS:
                    QMessageBox.warning(self.ui, "In Use", f"Cannot delete running profile ID {profile_id}. Please stop it first.")
                    continue

                acc_id = None
                for p in profiles:
                    if p['id'] == profile_id:
                        acc_id = p['account_id']
                        break

                delete_profile(self.app_dir, profile_id)

                if acc_id:
                    profile_dir = os.path.join(self.profiles_base, f"id_{acc_id}")
                    if os.path.exists(profile_dir):
                        try:
                            shutil.rmtree(profile_dir)
                        except Exception as e:
                            print(f"Failed to delete directory {profile_dir}: {e}")
                deleted += 1

            self.ui.load_table_data()
            QMessageBox.information(self.ui, "Deleted", f"Successfully deleted {deleted} accounts.")

    def execute_disk_cleanup(self):
        profiles = get_all_profiles(self.app_dir)
        cleaned = 0

        for p in profiles:
            if p['id'] in ACTIVE_LAUNCHERS:
                continue

            acc_id = p['account_id']
            profile_dir = os.path.join(self.profiles_base, f"id_{acc_id}")

            # Utilizing the new strict wipe defined in the browser_engine specs
            target_folders = [
                os.path.join(profile_dir, "Default", "Cache"),
                os.path.join(profile_dir, "Default", "System Cache"),
                os.path.join(profile_dir, "Default", "Code Cache"),
                os.path.join(profile_dir, "Default", "GPUCache"),
                os.path.join(profile_dir, "Crash Reports"),
                os.path.join(profile_dir, "ShaderCache"),
                os.path.join(profile_dir, "Shader Cache")
            ]
            for folder in target_folders:
                if os.path.exists(folder):
                    try:
                        shutil.rmtree(folder)
                        cleaned += 1
                    except: pass

        QMessageBox.information(self.ui, "Cleanup Complete", f"Safely wiped {cleaned} cache blobs. Cookies and local states are intact.")

    # ==========================================
    # 👥 GROUPING
    # ==========================================

    def add_new_group(self):
        text, ok = QInputDialog.getText(self.ui, 'New Group', 'Enter group name:')
        if ok and text.strip():
            if add_group(self.app_dir, text.strip()):
                QMessageBox.information(self.ui, "Success", "Group created.")
            else:
                QMessageBox.warning(self.ui, "Error", "Group already exists or invalid name.")

    def delete_selected_group(self, group_name: str):
        if not group_name or group_name == 'Default':
            QMessageBox.warning(self.ui, "Error", "Cannot delete the Default group or no group selected.")
            return

        reply = QMessageBox.warning(self.ui, 'Confirm', f"Delete group '{group_name}'?\nProfiles in this group will be moved to 'Default'.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_group(self.app_dir, group_name)
            self.ui.load_table_data()

    def execute_bulk_group_update(self, selected_ids: list):
        if not selected_ids:
            QMessageBox.warning(self.ui, "Selection Error", "Please select at least one profile.")
            return

        groups = get_all_groups(self.app_dir)
        group_names = [g['group_name'] for g in groups]

        new_group, ok = QInputDialog.getItem(self.ui, "Move to Group", "Select target group:", group_names, 0, False)
        if ok and new_group:
            for profile_id in selected_ids:
                update_profile_group(self.app_dir, profile_id, new_group)
            self.ui.load_table_data()
            QMessageBox.information(self.ui, "Group Updated", f"Moved {len(selected_ids)} profiles to group: {new_group}")

    # ==========================================
    # SINGLE PROFILE ROW MANAGEMENT
    # ==========================================
    def manage_single_proxy(self, profile_id):
        new_proxy, ok = QInputDialog.getText(self.ui, "Update Proxy", "Enter new Proxy (IP:PORT or IP:PORT:USER:PASS):")
        if ok:
            update_profile_proxy(self.app_dir, profile_id, new_proxy.strip())
            self.ui.load_table_data()
            QMessageBox.information(self.ui, "Proxy Updated", "Proxy updated successfully.")

    def export_single_cookie(self, profile_data):
        options = QFileDialog.Option.DontUseNativeDialog
        save_path, _ = QFileDialog.getSaveFileName(self.ui, "Save Session Cookie", f"{profile_data['profile_name']}_cookies.json", "JSON Files (*.json)", options=options)

        if not save_path:
            return

        profile_id = profile_data['id']
        # If the browser is currently running, fetch live cookies immediately
        if profile_id in ACTIVE_LAUNCHERS:
            try:
                driver = ACTIVE_LAUNCHERS[profile_id].driver
                if driver:
                    cookies = driver.get_cookies()
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, indent=4)
                    QMessageBox.information(self.ui, "Export Complete", "Successfully saved live session cookies.")
                else:
                    QMessageBox.warning(self.ui, "Export Failed", "Browser driver is missing.")
            except Exception as e:
                QMessageBox.critical(self.ui, "Export Error", f"Failed to extract live cookies:\n{e}")
        else:
            QMessageBox.warning(self.ui, "Not Running", "The profile must be actively running to export its live session cookies.\nPlease launch it first.")

    # ==========================================
    # POWER FEATURE: ATTACH EXISTING CHROME FOLDERS
    # ==========================================
    def connect_existing_profiles(self):
        options = QFileDialog.Option.ShowDirsOnly
        root_folder = QFileDialog.getExistingDirectory(self.ui, "Select Directory containing Chrome User Data Folders", "", options=options)

        if not root_folder:
            return

        attached_count = 0
        try:
            for folder_name in os.listdir(root_folder):
                folder_path = os.path.join(root_folder, folder_name)
                # Check if it looks like a valid Chrome Profile Dir (contains "Default" or "Local State")
                if os.path.isdir(folder_path) and (os.path.exists(os.path.join(folder_path, "Default")) or os.path.exists(os.path.join(folder_path, "Local State"))):

                    account_id = str(uuid.uuid4())[:8]
                    next_seq = get_next_sequential_id(self.app_dir)

                    # Sanitize folder_name for profile_name
                    sanitized = "".join([c for c in folder_name if c.isalnum() or c in ['_', '-']])[:10]
                    profile_name = f"linked_{sanitized}_{next_seq}"

                    success, _ = add_profile(self.app_dir, profile_name, account_id)
                    if success:
                        target_dir = os.path.join(self.profiles_base, f"id_{account_id}")
                        # Ensure we physically move the external user-data-dir into our app structure
                        try:
                            shutil.move(folder_path, target_dir)
                            attached_count += 1
                        except Exception as copy_e:
                            # If move fails (e.g., cross-drive linking), fallback to recursive copy then delete
                            shutil.copytree(folder_path, target_dir)
                            shutil.rmtree(folder_path, ignore_errors=True)
                            attached_count += 1

            self.ui.load_table_data()
            if attached_count > 0:
                QMessageBox.information(self.ui, "Import Complete", f"Successfully attached and took control of {attached_count} external Chrome profiles.")
            else:
                QMessageBox.warning(self.ui, "Import Error", "No valid Chrome Profile Data Folders (with 'Default' subdirs) found in that directory.")
        except Exception as e:
            QMessageBox.critical(self.ui, "Import Error", f"Failed to attach folders:\n{e}")
