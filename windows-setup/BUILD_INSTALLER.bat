@echo off
setlocal
title Building NexaFlow Setup

set "SCRIPT_DIR=%~dp0"
set "ISS_PATH=%SCRIPT_DIR%NexaFlow_Installer.iss"
set "DIST_EXE=%SCRIPT_DIR%dist\NexaFlow\NexaFlow.exe"
set "PACKAGE_DIR=%SCRIPT_DIR%Installers"
set "SETUP_EXE=%PACKAGE_DIR%\NexaFlow_Setup.exe"
set "ZIP_STAGE=%PACKAGE_DIR%\NexaFlow_v1.0_Setup"
set "ZIP_FILE=%PACKAGE_DIR%\NexaFlow_v1.0_Setup.zip"
set "ISCC_EXE="

echo.
echo  NexaFlow Windows Setup Builder
echo  -------------------------------------
echo.

if not exist "%DIST_EXE%" (
    echo  ERROR: Launch-ready application was not found:
    echo  %DIST_EXE%
    echo.
    echo  Put the current launch-ready app folder in windows-setup\dist\NexaFlow, then run this again.
    pause
    exit /b 1
)

if exist "%SCRIPT_DIR%..\tools\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%SCRIPT_DIR%..\tools\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC_EXE set "ISCC_EXE=%%I"
if not defined ISCC_EXE for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$paths=@($env:ProgramFiles + '\Inno Setup 6\ISCC.exe', ${env:ProgramFiles(x86)} + '\Inno Setup 6\ISCC.exe', $env:LOCALAPPDATA + '\Programs\Inno Setup 6\ISCC.exe', $env:USERPROFILE + '\AppData\Local\Programs\Inno Setup 6\ISCC.exe'); $paths | Where-Object { Test-Path $_ } | Select-Object -First 1"`) do if not defined ISCC_EXE set "ISCC_EXE=%%I"
if not defined ISCC_EXE (
    echo  ERROR: Inno Setup Compiler was not found.
    echo.
    echo  Install Inno Setup 6, or run:
    echo  powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%INSTALL_INNO_SETUP.ps1"
    echo.
    pause
    exit /b 1
)

if not exist "%PACKAGE_DIR%" mkdir "%PACKAGE_DIR%"

echo  Using launch-ready app:
echo  %DIST_EXE%
echo.
echo  Using Inno Setup:
echo  %ISCC_EXE%
echo.
echo  Compiling installer...
echo.

"%ISCC_EXE%" "%ISS_PATH%"
if errorlevel 1 (
    echo.
    echo  ERROR: Installer compilation failed.
    pause
    exit /b 1
)

if not exist "%SETUP_EXE%" (
    echo.
    echo  ERROR: Inno Setup finished, but the expected setup file was not created:
    echo  %SETUP_EXE%
    pause
    exit /b 1
)

echo.
echo  Done.
echo  Setup file:
echo  %SETUP_EXE%
echo.

echo  Creating web download zip...
if exist "%ZIP_STAGE%" rmdir /s /q "%ZIP_STAGE%"
mkdir "%ZIP_STAGE%"
copy /y "%SETUP_EXE%" "%ZIP_STAGE%\NexaFlow_Setup.exe" >nul
if exist "%PACKAGE_DIR%\NexaFlow_User_Guide.pdf" copy /y "%PACKAGE_DIR%\NexaFlow_User_Guide.pdf" "%ZIP_STAGE%\NexaFlow_User_Guide.pdf" >nul
if exist "%ZIP_FILE%" del /f /q "%ZIP_FILE%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -LiteralPath '%ZIP_STAGE%' -DestinationPath '%ZIP_FILE%' -Force"
if errorlevel 1 (
    echo.
    echo  WARNING: Setup was created, but the zip package could not be created.
    echo  You can still use:
    echo  %SETUP_EXE%
) else (
    rmdir /s /q "%ZIP_STAGE%"
    echo  Web download zip:
    echo  %ZIP_FILE%
)
echo.
pause
exit /b 0
