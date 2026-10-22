@echo off
title Android BootAnimation Generator
echo Starting Android BootAnimation Generator...
python "%~dp0main.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error.
    pause
)
