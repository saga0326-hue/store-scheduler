#define MyAppName    "Inventory Scheduler"
#define MyAppNameTW  "盤點行事曆調度管理系統"
#define MyAppVersion "1.0"
#define MyAppExe     "launcher.vbs"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppNameTW}
AppVersion={#MyAppVersion}
AppVerName={#MyAppNameTW} v{#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=盤點系統_安裝程式_v1.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
OutputDir=dist
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "建立桌面捷徑"; GroupDescription: "附加工作:"; Flags: checked

[Files]
Source: "app_package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppNameTW}"; \
    Filename: "{sys}\wscript.exe"; \
    Parameters: """{app}\{#MyAppExe}"""; \
    WorkingDir: "{app}"; \
    Comment: "{#MyAppNameTW}"
Name: "{autodesktop}\{#MyAppNameTW}"; \
    Filename: "{sys}\wscript.exe"; \
    Parameters: """{app}\{#MyAppExe}"""; \
    WorkingDir: "{app}"; \
    Comment: "{#MyAppNameTW}"; \
    Tasks: desktopicon

[Run]
Filename: "{sys}\wscript.exe"; \
    Parameters: """{app}\{#MyAppExe}"""; \
    WorkingDir: "{app}"; \
    Description: "立即啟動系統"; \
    Flags: postinstall shellexec skipifsilent nowait

[UninstallRun]
Filename: "cmd.exe"; \
    Parameters: "/c for /f ""tokens=5"" %a in ('netstat -aon ^| find "":8501""') do taskkill /f /pid %a"; \
    Flags: runhidden
