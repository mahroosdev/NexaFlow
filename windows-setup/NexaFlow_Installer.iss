; NexaFlow - Professional Windows Installer
; Requires Inno Setup 6.x

#define MyAppName "NexaFlow"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "NexaFlow"
#define MyAppExeName "NexaFlow.exe"

[Setup]
AppId={{92C1F5A9-5F5F-4C5A-8F5F-9C1F5A9F5F4C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\NexaFlow
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=installer-assets\LICENSE.txt
OutputDir=Installers
OutputBaseFilename=NexaFlow_Setup
SetupIconFile=installer-assets\nexaflow.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ShowLanguageDialog=no
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[InstallDelete]
Type: files; Name: "{app}\NexaFlow_Launcher.vbs"
Type: files; Name: "{autodesktop}\NexaFlow.lnk"
Type: files; Name: "{autodesktop}\NexaFlow v1.lnk"
Type: files; Name: "{autodesktop}\NexaFlow v1.0.lnk"
Type: files; Name: "{autoprograms}\NexaFlow.lnk"
Type: files; Name: "{autoprograms}\NexaFlow v1.lnk"
Type: files; Name: "{autoprograms}\NexaFlow v1.0.lnk"

[Files]
Source: "dist\NexaFlow\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installer-assets\NexaFlow_Welcome.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer-assets\nexaflow.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "installer-assets\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer-assets\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer-assets\PRIVACY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer-assets\SUPPORT.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer-assets\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer-assets\VERSION"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer-assets\docs\*.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\nexaflow.ico"; AppUserModelID: "NexaFlow.v1.0.Desktop"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\nexaflow.ico"; AppUserModelID: "NexaFlow.v1.0.Desktop"; Tasks: desktopicon

[Run]
Filename: "{sys}\wscript.exe"; Parameters: """{app}\NexaFlow_Welcome.vbs"""; Flags: waituntilterminated postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
