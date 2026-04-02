@echo off
echo ==========================================
echo Starting Generic App Build Automation...
echo ==========================================

echo [1/5] Creating Virtual Environment...
python -m venv venv

echo [2/5] Activating Virtual Environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading PIP and Installing Requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [4/5] Building Executables using PyInstaller...
:: Build Main Application (Windowed, no console, standalone file)
pyinstaller --noconfirm --onefile --windowed --name "ApplicationCore" --add-data "locators.json;." "main.py"

:: Build Keygen Application (Windowed, no console, standalone file)
pyinstaller --noconfirm --onefile --windowed --name "DeveloperKeygen" "ui_keygen.py"

echo [5/5] Cleaning up temporary build artifacts...
rmdir /s /q build
del /q ApplicationCore.spec
del /q DeveloperKeygen.spec

echo ==========================================
echo Compilation Complete!
echo Check the 'dist' folder for the executable files.
echo ==========================================
pause
