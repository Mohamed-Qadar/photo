; Inno Setup script for PhotoStudio -> builds PhotoStudio-Setup.exe
; Wraps the PyInstaller one-folder output (dist\PhotoStudio) into an installer.
; Build:  iscc installer\photostudio.iss
; No administrator privileges required (installs per-user).

#define AppName        "PhotoStudio"
#define AppVersion      "1.2.0"
#define AppPublisher    "Eng. Mohamed Ibrahim Abdi"
#define AppURL          "https://github.com/Mohamed-Qadar/photo"
#define AppExe          "PhotoStudio.exe"

[Setup]
AppId={{B3F2B2E1-9C4A-4D7E-9A1B-7C2E5A0D1F34}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}/releases
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=PhotoStudio - offline-first photo & design studio
VersionInfoCopyright=(c) {#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Per-user install => no admin prompt.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename=PhotoStudio-Setup
SetupIconFile=..\photostudio\resources\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; The entire PyInstaller output folder.
Source: "..\dist\PhotoStudio\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

; Note: the installer only removes files it placed under {app}. User projects
; (.pstudio files saved elsewhere, e.g. Documents) are never touched on uninstall.
