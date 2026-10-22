@echo off
title Push to GitHub - bootanimation-studio
echo [bootanimation-studio] Force pushing clean code to GitHub...
echo If Git Credential Manager opens in your browser, please click [Authorize].
echo.
git push -u origin main --force
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Clean code force-pushed to GitHub successfully!
    echo URL: https://github.com/Zhonxing/bootanimation-studio
) else (
    echo.
    echo [NOTICE] Push failed or canceled. Please check your network or GitHub login.
)
echo.
pause
