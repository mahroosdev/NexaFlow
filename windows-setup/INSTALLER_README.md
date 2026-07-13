# NexaFlow Windows Installer

This folder is prepared for the professional Windows setup flow.

## Current App Used By Installer

The Inno Setup script packages:

```text
dist\NexaFlow\NexaFlow.exe
```

The `dist\NexaFlow` folder is generated staging. It can be removed after the setup EXE and ZIP are rebuilt and smoke-tested.

## Build Complete Windows Release

The preferred non-interactive build regenerates the guides, standalone app, setup installer, setup ZIP, and synchronized release checksums:

```powershell
$env:NEXAFLOW_GUIDE_PYTHON = '<Python with tools/requirements-guides.txt installed>'
.\BUILD_RELEASE.ps1
```

Use `-SkipGuides` only when the generated DOCX/PDF already match the current canonical `installer-assets\docs\USER_GUIDE.md`.

## Build Setup Installer Only

1. Install Inno Setup 6.
2. Open this folder.
3. Run:

```text
BUILD_INSTALLER.bat
```

Output:

```text
Installers\NexaFlow_Setup.exe
Installers\NexaFlow_v1.0_Setup.zip
```

## Repository Files

- `dist\NexaFlow\NexaFlow.exe` - temporary standalone build used as installer input
- `installer-assets\` - files included in the installer
- `..\website\` - independently published Netlify website source; it is not duplicated inside the Windows installation
- `NexaFlow_Installer.iss` - Inno Setup script
- `BUILD_INSTALLER.bat` - setup builder
- `INSTALL_INNO_SETUP.ps1` - optional Inno Setup installer helper
- `nexaflow.spec` - PyInstaller build recipe
- `nexaflow.ico` - app/setup icon

Final distributable files belong only in `Installers\`. Build and `dist` folders are regenerable and intentionally ignored.
