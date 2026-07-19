@echo off
setlocal
call "%~dp0start-asteria.cmd" %*
exit /b %ERRORLEVEL%
