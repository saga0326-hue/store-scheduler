@echo off
cd /d %~dp0
echo Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit
)
echo Installing packages...
pip install -r requirements.txt
echo.
echo Done! Use [kaido_xitong.bat] to launch the system.
pause
