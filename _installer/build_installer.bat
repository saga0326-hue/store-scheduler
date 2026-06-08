@echo off
setlocal
cd /d %~dp0

echo ============================================
echo  Building Installer...
echo ============================================

if exist app_package rmdir /s /q app_package
mkdir app_package

echo [1/4] Creating Python venv...
python -m venv app_package\venv
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

echo [2/4] Installing packages...
app_package\venv\Scripts\pip install streamlit pandas openpyxl -q
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo [3/4] Copying app files...
copy ..\app.py app_package\app.py
copy launcher.vbs app_package\launcher.vbs

echo [4/4] Building installer EXE...
if not exist dist mkdir dist

set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo ERROR: Inno Setup not found.
    echo Install: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

"%ISCC%" installer.iss

echo.
echo ============================================
echo  DONE! Check: _installer\dist\
echo ============================================
pause
