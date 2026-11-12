@echo off
set "P=%~dp0widget.pid"
if exist "%P%" (
  set /p PID=<"%P%"
  taskkill /pid %PID% /f >nul 2>&1
  del "%P%" >nul 2>&1
  echo Widget stopped.
) else (
  echo Widget is not running.
)
pause
