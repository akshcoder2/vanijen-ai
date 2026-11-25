@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt pyinstaller || exit /b 1
py -m PyInstaller --noconfirm --clean --windowed --onedir --name "Vanijen AI" --icon "assets\vanijen-icon.ico" --add-data "assets;assets" --hidden-import _sounddevice_data --collect-data _sounddevice_data jarvis.py || exit /b 1
echo App ready in dist\Vanijen AI. Distribute the whole folder, not just the EXE.
