@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  "D:\code\Python313\python.exe" -m venv .venv
  if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto :failed
echo Setup complete. Double-click run_app.bat to start.
pause
exit /b 0

:failed
echo.
echo Setup failed. Review the error above.
pause
exit /b 1

