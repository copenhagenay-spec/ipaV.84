; VERA Inno Setup Script
; Requires Inno Setup 6+ — https://jrsoftware.org/isinfo.php

#define AppName "VERA"
#define AppVersion "0.86"
#define AppExe "launcher_out\VERA.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Your Name Here
DefaultDirName={localappdata}\{#AppName}
DefaultGroupName={#AppName}
OutputBaseFilename=VERA_Setup_{#AppVersion}
OutputDir=installer_out
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=data\assets\ipa.ico
WizardStyle=modern
MinVersion=10.0
; Prevent downgrade installs
AppMutex=VERAMutex

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
Name: "startupicon"; Description: "Launch VERA at &Windows startup"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Python source
Source: "*.py";              DestDir: "{app}";              Flags: ignoreversion
Source: "run_ipa.cmd";       DestDir: "{app}";              Flags: ignoreversion
Source: "uninstall.cmd";     DestDir: "{app}";              Flags: ignoreversion
Source: "requirements.txt";  DestDir: "{app}";              Flags: ignoreversion
Source: "VERSION";           DestDir: "{app}";              Flags: ignoreversion

; Assets
Source: "data\assets\*";     DestDir: "{app}\data\assets";  Flags: ignoreversion recursesubdirs

; Docs
Source: "docs\*";            DestDir: "{app}\docs";         Flags: ignoreversion recursesubdirs

; setup_installer.cmd is generated below — drives pip + Kokoro model download
Source: "setup_installer.cmd"; DestDir: "{app}";            Flags: ignoreversion

; Launcher exe — proper Windows app shortcut with icon
Source: "launcher_out\VERA.exe"; DestDir: "{app}\launcher_out"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{commondesktop}\{#AppName}";   Filename: "{app}\{#AppExe}"; Tasks: desktopicon

; Startup (optional)
Name: "{userstartup}\{#AppName}";     Filename: "{app}\{#AppExe}"; Tasks: startupicon

[Run]
; Run dependency installer after files are copied
Filename: "{app}\setup_installer.cmd"; \
    Description: "Install Python dependencies and download voice model"; \
    Flags: postinstall waituntilterminated runascurrentuser shellexec; \
    WorkingDir: "{app}"

; Offer to launch VERA immediately
Filename: "{app}\{#AppExe}"; \
    Description: "Launch {#AppName} now"; \
    Flags: postinstall nowait skipifsilent unchecked shellexec; \
    WorkingDir: "{app}"

[UninstallDelete]
; Clean up generated/downloaded data on uninstall
Type: filesandordirs; Name: "{app}\data\logs"
Type: filesandordirs; Name: "{app}\data\models"
Type: filesandordirs; Name: "{app}\__pycache__"
; Note: data\config.json and data\memory.json are intentionally left behind
; so users don't lose their settings and memory on reinstall.
