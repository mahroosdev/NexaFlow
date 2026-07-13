@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-private-apk.ps1"
echo.
if exist "%~dp0Android Installer\NexaFlow_Android_Private.apk" (
  echo APK built:
  echo %~dp0Android Installer\NexaFlow_Android_Private.apk
) else (
  echo APK was not created. Check the release build log printed above.
)
pause
