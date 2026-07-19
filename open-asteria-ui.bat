@echo off
setlocal
chcp 65001 >nul
call "%~dp0start-asteria.cmd" %*
exit /b %ERRORLEVEL%
