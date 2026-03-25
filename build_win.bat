@echo off
REM Build Media Porter .exe for Windows
REM Usage: build_win.bat
REM Requires: pip install pyinstaller pywin32

echo === Media Porter — Windows Build ===

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo -- Building .exe with PyInstaller...
python -m PyInstaller MediaPorter_win.spec --noconfirm

if not exist "dist\MediaPorter.exe" (
    echo ERROR: dist\MediaPorter.exe not found after build
    exit /b 1
)

echo -- .exe built: dist\MediaPorter.exe
echo === Build complete ===
pause
