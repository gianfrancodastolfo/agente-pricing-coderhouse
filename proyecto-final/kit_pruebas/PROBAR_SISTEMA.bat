@echo off
chcp 65001 >nul
echo Corriendo el kit de pruebas (tarda unos 6 minutos, no cierres esta ventana)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0probar_sistema.ps1"
echo.
pause
