; VERA Inno Setup Script
; Requires Inno Setup 6+ — https://jrsoftware.org/isinfo.php

#define AppName "VERA"
#define AppVersion "0.97.9"
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

; Launcher exe — proper Windows app shortcut with icon
Source: "launcher_out\VERA.exe"; DestDir: "{app}\launcher_out"; Flags: ignoreversion

[Dirs]
Name: "{app}\data\models"
Name: "{app}\data\logs"

[Icons]
; Start Menu
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{userdesktop}\{#AppName}";     Filename: "{app}\{#AppExe}"; Tasks: desktopicon

; Startup (optional)
Name: "{userstartup}\{#AppName}";     Filename: "{app}\{#AppExe}"; Tasks: startupicon

[Run]
; Upgrade pip silently
Filename: "{code:GetPython}"; \
    Parameters: "-m pip install --upgrade pip --quiet"; \
    StatusMsg: "Preparing package manager..."; \
    Flags: waituntilterminated runhidden; \
    WorkingDir: "{app}"

; Install all Python dependencies silently
Filename: "{code:GetPython}"; \
    Parameters: "-m pip install -r ""{app}\requirements.txt"" --quiet"; \
    StatusMsg: "Installing VERA dependencies (this may take a minute)..."; \
    Flags: waituntilterminated runhidden; \
    WorkingDir: "{app}"

; Download espeak-ng MSI silently
Filename: "curl.exe"; \
    Parameters: "-L --silent -o ""{tmp}\espeak-ng.msi"" ""https://github.com/espeak-ng/espeak-ng/releases/download/1.52.0/espeak-ng.msi"""; \
    StatusMsg: "Downloading voice engine (espeak-ng)..."; \
    Flags: waituntilterminated runhidden; \
    WorkingDir: "{app}"

; Install espeak-ng silently
Filename: "msiexec.exe"; \
    Parameters: "/i ""{tmp}\espeak-ng.msi"" /quiet /norestart"; \
    StatusMsg: "Installing voice engine (espeak-ng)..."; \
    Flags: waituntilterminated runhidden; \
    WorkingDir: "{app}"

; Download Kokoro ONNX model
Filename: "curl.exe"; \
    Parameters: "-L --silent -o ""{app}\data\models\kokoro-v1.0.onnx"" ""https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"""; \
    StatusMsg: "Downloading voice model (kokoro-v1.0.onnx, ~270MB)..."; \
    Flags: waituntilterminated runhidden; \
    WorkingDir: "{app}"

; Download Kokoro voices bin
Filename: "curl.exe"; \
    Parameters: "-L --silent -o ""{app}\data\models\voices-v1.0.bin"" ""https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"""; \
    StatusMsg: "Downloading voice model (voices-v1.0.bin, ~40MB)..."; \
    Flags: waituntilterminated runhidden; \
    WorkingDir: "{app}"

; Offer to launch VERA immediately
Filename: "{app}\{#AppExe}"; \
    Description: "Launch {#AppName} now"; \
    Flags: postinstall nowait skipifsilent unchecked shellexec; \
    WorkingDir: "{app}"

[Code]
var
  PythonExe: String;

function FindPython(): String;
var
  Candidates: TArrayOfString;
  i: Integer;
  LocalAppData: String;
  ProgFiles: String;
begin
  LocalAppData := ExpandConstant('{localappdata}');
  ProgFiles    := ExpandConstant('{pf}');
  SetArrayLength(Candidates, 8);
  Candidates[0] := LocalAppData + '\Programs\Python\Python314\python.exe';
  Candidates[1] := LocalAppData + '\Programs\Python\Python313\python.exe';
  Candidates[2] := LocalAppData + '\Programs\Python\Python312\python.exe';
  Candidates[3] := LocalAppData + '\Programs\Python\Python311\python.exe';
  Candidates[4] := ProgFiles + '\Python314\python.exe';
  Candidates[5] := ProgFiles + '\Python313\python.exe';
  Candidates[6] := ProgFiles + '\Python312\python.exe';
  Candidates[7] := ProgFiles + '\Python311\python.exe';
  for i := 0 to GetArrayLength(Candidates) - 1 do
    if FileExists(Candidates[i]) then
    begin
      Result := Candidates[i];
      Exit;
    end;
  Result := 'python.exe'; // fallback — must be on PATH
end;

function GetPython(Param: String): String;
begin
  Result := PythonExe;
end;

procedure InitializeWizard();
begin
  PythonExe := FindPython();
end;

[UninstallDelete]
; Clean up generated/downloaded data on uninstall
Type: filesandordirs; Name: "{app}\data\logs"
Type: filesandordirs; Name: "{app}\data\models"
Type: filesandordirs; Name: "{app}\__pycache__"
; Note: data\config.json and data\memory.json are intentionally left behind
; so users don't lose their settings and memory on reinstall.
