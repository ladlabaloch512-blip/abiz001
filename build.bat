@echo off
echo =======================================================
echo Building FB AutoPilot PRO - Commercial Release
echo =======================================================

echo.
echo [1/3] Setting up Python Virtual Environment...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo [2/3] Installing Dependencies...
pip install --upgrade pip
pip install PyQt6 selenium undetected-chromedriver cryptography psutil webdriver-manager pyinstaller Pillow requests

echo.
echo [3/3] Compiling Executables...
REM Compile the Client Application
pyinstaller --noconfirm --onedir --windowed --icon=./assets/icon.ico --name "FB_AutoPilot_Pro" --paths . --collect-submodules shared_logic --hidden-import shared_logic --hidden-import shared_logic.security --add-data "shared_logic;shared_logic" --add-data "client_app/styles.qss;client_app" "client_app/MainTool.py"

REM Compile the KeyGen Admin Application
pyinstaller --noconfirm --onedir --windowed --icon=./assets/icon.ico --name "License_Generator" --paths . --collect-submodules shared_logic --hidden-import shared_logic --hidden-import shared_logic.security --add-data "shared_logic;shared_logic" "keygen_app/KeyGenTool.py"

echo.
echo =======================================================
echo Build Complete!
echo You can find your compiled EXEs in the "dist" folder.
echo Make sure to place "license.dat" in the same folder as "FB_AutoPilot_Pro.exe" when distributing.
echo =======================================================
pause
