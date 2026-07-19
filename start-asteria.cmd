@echo off
setlocal
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-asteria.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo Asteria did not start. Review the error and logs above.
  pause
)
exit /b %EXIT_CODE%
