; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "TaktPlayer"
#define MyAppVersion "1.0.6"
#define MyAppVersionForFlie "1_0_6"
#define MyAppPublisher "Takt Industries AS"
#define MyAppURL "http://www.taktindustries.com/"
#define MyAppExeName "TaktPlayer.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppID={{2E8348A5-AC01-43E6-B31A-7899CF50C725}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=true
OutputBaseFilename={#MyAppName}_Setup_V{#MyAppVersionForFlie}
SetupIconFile=C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\graphics\TaktPlayerNoGUI.ico
Compression=lzma/Max
SolidCompression=true
MinVersion=5.1.2600
AppCopyright=Takt Industries AS 2012
AppVerName={#MyAppVersion}
PrivilegesRequired=none

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\dist\TaktPlayer\TaktPlayer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\documentation\Output\TaktPlayer_debug.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\VersionInfo.log"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\outOfMemoryPreview.jpg"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\ffmpeg\bin\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Program Files (x86)\OpenCV\bin\*"; DestDir: {app}; Flags: IgnoreVersion; 
Source: "C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\dist\TaktPlayer\*"; DestDir: "{app}"; Excludes: "avicap32.dll,avifil32.dll,msacm32.dll,msvfw32.dll"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\graphics\*; DestDir: {app}\graphics; Flags: ignoreversion recursesubdirs createallsubdirs; 
Source: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\licenses\*; DestDir: {app}\liceses; Flags: ignoreversion recursesubdirs createallsubdirs; 
; NOTE: Don't use "Flags: ignoreversion" on any shared system files
Source: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\testFiles\*; DestDir: {app}\testFiles; Flags: ignoreversion recursesubdirs createallsubdirs; 
Source: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\config\Default.cfg; DestDir: {app}\config; Flags: IgnoreVersion; 
Source: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\config\EffectsDemo.cfg; DestDir: {app}\config; Flags: IgnoreVersion; 
Source: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\config\ModulationDemo.cfg; DestDir: {app}\config; Flags: IgnoreVersion; 
Source: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\config\PlaybackModesDemo.cfg; DestDir: {app}\config; Flags: IgnoreVersion; 

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\graphics\TaktPlayer.ico"
Name: "{group}\{#MyAppName} No GUI"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}";  IconFilename: "{app}\graphics\TaktPlayerNoGui.ico"; Parameters: "--nogui"
Name: "{group}\TaktGUI"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}";  IconFilename: "{app}\graphics\TaktGui.ico"; Parameters: "--guionly"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\graphics\TaktPlayer.ico"; Tasks: desktopicon
Name: "{commondesktop}\{#MyAppName} No GUI"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}";  IconFilename: "{app}\graphics\TaktPlayerNoGui.ico"; Parameters: "--nogui"; Tasks: desktopicon
Name: "{commondesktop}\TaktGUI"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}";  IconFilename: "{app}\graphics\TaktGui.ico"; Parameters: "--guionly"; Tasks: desktopicon

[Dirs]
Name: graphics;
Name: licenses;
Name: testFiles;
Name: config;

[InnoIDE_PreCompile]
Name: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\TaktPlayer_pcUpdateVersionInfo.bat; Flags: AbortOnError CmdPrompt;
Name: C:\Users\pcn\Workspace\MusicalVideoPlayer_Player\TaktPlayer_pcMake.bat; Flags: AbortOnError CmdPrompt;
