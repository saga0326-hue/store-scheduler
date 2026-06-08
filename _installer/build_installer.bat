@echo off
setlocal
cd /d %~dp0

echo ============================================
echo  Build Installer - Step by Step
echo ============================================
echo.

REM ── Step 1: Clean ────────────────────────────
if exist app_package rmdir /s /q app_package
mkdir app_package

REM ── Step 2: Create venv from local Python ────
echo [1/4] Creating Python environment...
python -m venv app_package\venv
if errorlevel 1 (
    echo ERROR: Python not found. Install Python first.
    pause & exit /b 1
)

REM ── Step 3: Install packages ──────────────────
echo [2/4] Installing packages...
app_package\venv\Scripts\pip install streamlit pandas openpyxl -q
if errorlevel 1 (
    echo ERROR: Package install failed.
    pause & exit /b 1
)

REM ── Step 4: Copy app files ────────────────────
echo [3/4] Copying app files...
copy ..\app.py       app_package\app.py      >nul
copy launcher.vbs    app_package\launcher.vbs >nul

REM ── Step 5: Build installer ───────────────────
echo [4/4] Building installer EXE...
if not exist dist mkdir dist

set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo.
    echo [ERROR] Inno Setup not found!
    echo Please install it from: https://jrsoftware.org/isdl.php
    echo Then run this script again.
    pause & exit /b 1
)

"%ISCC%" installer.iss
echo.
echo ============================================
echo  DONE!
echo  File: _installer\dist\盤點系統_安裝程式_v1.0.exe
echo ============================================
pause
