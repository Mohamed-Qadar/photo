@echo off
REM ============================================================
REM  PhotoStudio - development launcher (no installer / EXE)
REM  Checks Python, sets up a venv, installs deps, runs the app.
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "STAMP=%VENV_DIR%\.deps-installed"

echo(
echo  === PhotoStudio (development mode) ===
echo(

REM --- 1. Find a Python interpreter -------------------------------------
set "PYLAUNCH="
py -3 --version >nul 2>&1 && set "PYLAUNCH=py -3"
if not defined PYLAUNCH (
    python --version >nul 2>&1 && set "PYLAUNCH=python"
)
if not defined PYLAUNCH (
    echo [ERROR] Python was not found on your PATH.
    echo         Install Python 3.11+ from https://www.python.org/downloads/
    echo         and make sure "Add python.exe to PATH" is checked.
    goto :fail
)
echo  [1/4] Using Python: !PYLAUNCH!

REM --- 2. Create the virtual environment if missing --------------------
if not exist "%VENV_PY%" (
    echo  [2/4] Creating virtual environment in "%VENV_DIR%" ...
    !PYLAUNCH! -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        goto :fail
    )
) else (
    echo  [2/4] Virtual environment found.
)

REM --- 3. Install / update dependencies when requirements change -------
set "NEED_INSTALL=1"
if exist "%STAMP%" (
    REM Reinstall only if requirements.txt is newer than the stamp.
    for /f %%I in ('dir /b /o-d "requirements.txt" "%STAMP%" 2^>nul') do (
        if "%%I"=="%STAMP%" set "NEED_INSTALL=0"
        goto :after_check
    )
)
:after_check
if "%NEED_INSTALL%"=="1" (
    echo  [3/4] Installing dependencies from requirements.txt ...
    "%VENV_PY%" -m pip install --upgrade pip
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed. See messages above.
        goto :fail
    )
    echo installed > "%STAMP%"
) else (
    echo  [3/4] Dependencies up to date.
)

REM --- 4. Launch the application ---------------------------------------
echo  [4/4] Launching PhotoStudio ...
echo(
"%VENV_PY%" run.py
if errorlevel 1 (
    echo(
    echo [ERROR] PhotoStudio exited with an error (code %errorlevel%).
    goto :fail
)

echo(
echo  PhotoStudio closed normally.
endlocal
exit /b 0

:fail
echo(
echo  Startup failed. Fix the issue above and run this script again.
endlocal
pause
exit /b 1
