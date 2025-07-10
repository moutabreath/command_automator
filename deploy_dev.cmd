@echo off

REM Kill any running instance of the app before copying
taskkill /IM commands_automator_api.exe /F >nul 2>&1

call .\.venv\Scripts\activate

@REM python -m PyInstaller commands_automator_api.py -i ui/resources/Commands_Automator.ico --onedir --add-data "ui;ui" --noconfirm
python -m PyInstaller  --clean --debug=all commands_automator.spec > build_log.txt 2>&1

call deactivate

xcopy user_scripts dist\commands_automator_api\user_scripts /E /I /Y
xcopy config dist\commands_automator_api\config /E /I /Y

start "" ".\dist\command_automator_api\command_automator_api.exe"