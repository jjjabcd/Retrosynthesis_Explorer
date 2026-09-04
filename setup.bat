@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows.ps1" -Mode setup
if errorlevel 1 (
  echo Setup failed. See the message above, then retry setup.bat.
  pause
  exit /b 1
)
echo Setup complete. Start the app with run.bat.
pause
