@echo off
REM ============================================================
REM  PhotoStudio - run the automated test suite
REM  Ensures the venv + dev dependencies exist, then runs pytest.
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

echo(
echo  === PhotoStudio tests ===
echo(

REM --- Find Python -----------------------------------------------------
set "PYLAUNCH="
py -3 --version >nul 2>&1 && set "PYLAUNCH=py -3"
if not defined PYLAUNCH (
    python --version >nul 2>&1 && set "PYLAUNCH=python"
)
if not defined PYLAUNCH (
    echo [ERROR] Python was not found on your PATH. Install Python 3.11+.
    goto :fail
)

REM --- Create venv if needed ------------------------------------------
if not exist "%VENV_PY%" (
    echo  Creating virtual environment ...
    !PYLAUNCH! -m venv "%VENV_DIR%"
    if errorlevel 1 ( echo [ERROR] venv creation failed. & goto :fail )
)

REM --- Install dev dependencies --------------------------------------
echo  Installing development dependencies ...
"%VENV_PY%" -m pip install --upgrade pip >nul
"%VENV_PY%" -m pip install -r dev-requirements.txt
if errorlevel 1 ( echo [ERROR] Failed to install dev dependencies. & goto :fail )

REM --- Run tests ------------------------------------------------------
echo(
echo  Running pytest ...
echo(
REM Qt offscreen so UI tests need no display; core/imaging tests are headless.
set "QT_QPA_PLATFORM=offscreen"
"%VENV_PY%" -m pytest %*
set "RC=%errorlevel%"
echo(
if "%RC%"=="0" (
    echo  All tests passed.
) else (
    echo [FAILED] pytest reported failures (exit code %RC%).
)
endlocal & exit /b %RC%

:fail
echo(
echo  Could not run tests. Fix the issue above and try again.
endlocal
pause
exit /b 1
