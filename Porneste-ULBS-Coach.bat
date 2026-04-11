@echo off
title ULBS Coach - Server AI
color 0A
echo.
echo ========================================
echo    ULBS Coach - Asistent AI
echo    Pornire server...
echo ========================================
echo.
cd /d "%~dp0backend"
echo Server pornit! Deschide browserul la:
echo http://127.0.0.1:5000
echo.
echo Apasa CTRL+C pentru a opri serverul.
echo.
py -3.12 app.py
pause