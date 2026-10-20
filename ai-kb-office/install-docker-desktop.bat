@echo off
echo ================================================
echo   Docker Desktop: fast download + auto install
echo ================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install-docker-desktop.ps1"
echo.
pause
