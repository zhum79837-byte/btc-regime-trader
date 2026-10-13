@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found. Run setup.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 (
  echo.
  echo App failed to start. Review the error above, then run setup.bat if dependencies are missing.
  pause
  exit /b 1
)

