@echo off
setlocal EnableDelayedExpansion
cd /d %~dp0

echo ================================================
echo  Build Installer - Inventory Scheduler
echo ================================================
echo.

REM ── Step 1: Clean up ────────────────────────────
if exist app_package (
    echo [1/5] Removing old build...
    rmdir /s /q app_package
)
mkdir app_package
mkdir app_package\python

REM ── Step 2: Download Python 3.11 Embedded ───────
echo [2/5] Downloading Python 3.11 embedded (64-bit)...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'python-embedded.zip' -UseBasicParsing"
if not exist python-embedded.zip (
    echo ERROR: Download failed. Check your internet connection.
    pause & exit /b 1
)
echo Extracting...
powershell -Command "Expand-Archive -Path 'python-embedded.zip' -DestinationPath 'app_package\python' -Force"
del python-embedded.zip
echo Python extracted.

REM ── Step 3: Enable site-packages ────────────────
echo [3/5] Configuring Python embedded...
powershell -Command ^
    "(Get-Content 'app_package\python\python311._pth') ^
     -replace '#import site','import site' ^
     | Set-Content 'app_package\python\python311._pth'"

powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'app_package\python\get-pip.py' -UseBasicParsing"
app_package\python\python.exe app_package\python\get-pip.py --no-warn-script-location -q
del app_package\python\get-pip.py
echo pip ready.

REM ── Step 4: Install packages ─────────────────────
echo [4/5] Installing packages (may take 3-5 minutes)...
app_package\python\python.exe -m pip install streamlit pandas openpyxl --no-warn-script-location -q
if errorlevel 1 (
    echo ERROR: Package install failed.
    pause & exit /b 1
)
echo Packages installed.

REM ── Step 5: Copy app files ────────────────────────
echo [5/5] Copying app files...
copy ..\app.py       app_package\app.py    >nul
copy launcher.vbs    app_package\launcher.vbs >nul

echo.
echo ================================================
echo  app_package is ready!
echo ================================================
echo.

REM ── Try Inno Setup ───────────────────────────────
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if defined ISCC (
    echo Building installer EXE...
    if not exist dist mkdir dist
    "%ISCC%" installer.iss
    echo.
    echo ================================================
    echo  DONE!
    echo  Installer: _installer\dist\盤點系統_安裝程式_v1.0.exe
    echo ================================================
) else (
    echo [NOTE] Inno Setup not found.
    echo To build the installer EXE, install Inno Setup 6 from:
    echo   https://jrsoftware.org/isdl.php
    echo Then run this script again.
    echo.
    echo Alternatively, zip the "app_package" folder to distribute
    echo as a portable version.
)
echo.
pause
