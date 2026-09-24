; ============================================================
; MP3 ORDER PRO
; СОБСТВЕН ИНСТАЛАТОР
; ============================================================

#define MyAppName "MP3 Order PRO"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Metodi Drumev"
#define MyAppExeName "launcher.exe"

; ============================================================
; SETUP
; ============================================================

[Setup]

AppId={{8C9E7D3A-4F27-4F3B-9B4A-9D7B6D2A1C11}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\MP3 Order PRO
DefaultGroupName={#MyAppName}

OutputDir=D:\Visual Studio Code Projects\MP3_Order\installer
OutputBaseFilename=MP3_Order_PRO_Setup

SetupIconFile=D:\Visual Studio Code Projects\MP3_Order\assets\MP3_Order_PRO.ico

UninstallDisplayIcon={app}\launcher.exe

Uninstallable=yes
CreateUninstallRegKey=yes

PrivilegesRequired=admin

WizardStyle=modern

ShowLanguageDialog=yes
LanguageDetectionMethod=uilanguage
UsePreviousLanguage=no

CloseApplications=yes
CloseApplicationsFilter=launcher.exe;MP3_Order_PRO.exe;MP3_Order_PRO_Updater.exe
RestartApplications=no

Compression=lzma
SolidCompression=yes

DisableProgramGroupPage=yes

; ============================================================
; ЛОГО В ИНСТАЛАТОРА
; ============================================================

WizardSmallImageFile=D:\Visual Studio Code Projects\MP3_Order\assets\MP3_Order_Installer.bmp

; ============================================================
; ЕЗИЦИ
; ============================================================

[Languages]

Name: "bulgarian"; MessagesFile: "compiler:Languages\Bulgarian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

; ============================================================
; СОБСТВЕНИ ТЕКСТОВЕ
; ============================================================

[CustomMessages]

bulgarian.CreateDesktopIcon=Създай пряк път на работния плот
english.CreateDesktopIcon=Create a desktop shortcut

bulgarian.LaunchProgram=Стартирай %1
english.LaunchProgram=Launch %1

; ============================================================
; ФАЙЛОВЕ НА ПРОГРАМАТА
; ============================================================

[Files]

; ------------------------------------------------------------
; LAUNCHER
; ------------------------------------------------------------

Source: "D:\Visual Studio Code Projects\MP3_Order\dist\launcher.exe"; DestDir: "{app}"; Flags: ignoreversion

; ------------------------------------------------------------
; ОСНОВНА ПРОГРАМА
; ------------------------------------------------------------

Source: "D:\Visual Studio Code Projects\MP3_Order\dist\MP3_Order_PRO.exe"; DestDir: "{app}"; Flags: ignoreversion

; ------------------------------------------------------------
; UPDATER
; ------------------------------------------------------------

Source: "D:\Visual Studio Code Projects\MP3_Order\dist\MP3_Order_PRO_Updater.exe"; DestDir: "{app}"; Flags: ignoreversion

; ------------------------------------------------------------
; ЛОГО
; ------------------------------------------------------------

Source: "D:\Visual Studio Code Projects\MP3_Order\assets\MP3_Order_Logo.png"; DestDir: "{app}\assets"; Flags: ignoreversion

; ------------------------------------------------------------
; FFMPEG
; ------------------------------------------------------------

Source: "D:\Visual Studio Code Projects\MP3_Order\ffmpeg-n9.0-latest-win64-gpl-9.0\*"; DestDir: "{app}\ffmpeg-n9.0-latest-win64-gpl-9.0"; Flags: ignoreversion recursesubdirs createallsubdirs

; ============================================================
; TASKS
; ============================================================

[Tasks]

Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

; ============================================================
; START MENU / DESKTOP SHORTCUTS
; ============================================================

[Icons]

; ------------------------------------------------------------
; START MENU
; ------------------------------------------------------------

Name: "{autoprograms}\MP3 Order PRO"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\launcher.exe"

; ------------------------------------------------------------
; DESKTOP
; ------------------------------------------------------------

Name: "{autodesktop}\MP3 Order PRO"; Filename: "{app}\launcher.exe"; Tasks: desktopicon; IconFilename: "{app}\launcher.exe"

; ============================================================
; СТАРТИРАНЕ СЛЕД ИНСТАЛАЦИЯ
; ============================================================

[Run]

Filename: "{app}\launcher.exe"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; ============================================================
; ДОПЪЛНИТЕЛНО ПОЧИСТВАНЕ
; ============================================================

[UninstallDelete]

; ------------------------------------------------------------
; АКО ОСТАНАТ ПРАЗНИ ПАПКИ
; ------------------------------------------------------------

Type: dirifempty; Name: "{app}\assets"

Type: dirifempty; Name: "{app}"

; ============================================================
; КОД ЗА ЕЗИКА НА MP3 ORDER PRO
; ============================================================

[Code]

const
  AppLanguageKey = 'Software\MP3_Order\MP3_Order_PRO';
  AppLanguageValue = 'language';

// ============================================================
// ЗАПИСВАМЕ ЕЗИКА ОТ ИНСТАЛАТОРА
// ============================================================

procedure SetAppLanguageFromInstaller;
var
  SelectedLanguage: String;
begin

  // ----------------------------------------------------------
  // АКО ВЕЧЕ ИМА ЗАПАЗЕН ЕЗИК,
  // НЕ ГО ПРЕЗАПИСВАМЕ.
  // ----------------------------------------------------------

  if RegValueExists(
    HKEY_CURRENT_USER,
    AppLanguageKey,
    AppLanguageValue
  ) then
  begin

    Exit;

  end;

  // ----------------------------------------------------------
  // ВЗЕМАМЕ ЕЗИКА, ИЗБРАН В ИНСТАЛАТОРА
  // ----------------------------------------------------------

  SelectedLanguage := ActiveLanguage;

  // ----------------------------------------------------------
  // BULGARIAN -> bg
  // ENGLISH -> en
  // ----------------------------------------------------------

  if SelectedLanguage = 'english' then
  begin

    RegWriteStringValue(
      HKEY_CURRENT_USER,
      AppLanguageKey,
      AppLanguageValue,
      'en'
    );

  end
  else
  begin

    RegWriteStringValue(
      HKEY_CURRENT_USER,
      AppLanguageKey,
      AppLanguageValue,
      'bg'
    );

  end;

end;

// ============================================================
// СЛЕД ИНСТАЛАЦИЯТА
// ============================================================

procedure CurStepChanged(CurStep: TSetupStep);
begin

  if CurStep = ssPostInstall then
  begin

    SetAppLanguageFromInstaller;

  end;

end;

// ============================================================
// ИЗТРИВАМЕ РЕГИСТЪРА НА MP3 ORDER PRO ПРИ UNINSTALL
// ============================================================

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin

  if CurUninstallStep = usUninstall then
  begin

    // ----------------------------------------------------------
    // ИЗТРИВАМЕ ЦЕЛИЯ КЛЮЧ НА ПРОГРАМАТА:
    //
    // HKEY_CURRENT_USER\Software\MP3_Order\MP3_Order_PRO
    //
    // Това включва всички настройки и всички под-ключове.
    // ----------------------------------------------------------

    RegDeleteKeyIncludingSubkeys(
      HKEY_CURRENT_USER,
      AppLanguageKey
    );

  end;

end;

// ============================================================
// КРАЙ НА ИНСТАЛАТОРА
// ============================================================