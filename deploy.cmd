@echo off

REM Kill any running instance of the app before copying
taskkill /IM commands_automator_api.exe /F >nul 2>&1


@REM python -m PyInstaller --clean --debug=all commands_automator_api.py -i ui/resources/Commands_Automator.ico --onedir --add-data "ui;ui" --noconfirm  > build_log.txt 2>&1
@REM python -m PyInstaller  --clean commands_automator_api.spec > build_log.txt 2>&1 -y
.\.venv\Scripts\python.exe -m PyInstaller commands_automator_api.py -i ui/resources/Commands_Automator.ico -F --add-data "ui;ui" -w


xcopy "dist\commands_automator_api.exe" "commands_automator_api.exe" /Y

start "" ".\commands_automator_api.exe"