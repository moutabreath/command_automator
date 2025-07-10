pyinstaller command_automator_api.py -i ui/resources/Commands_Automator.ico --onedir --add-data "ui;ui"
xcopy user_scripts dist\command_automator_api\user_scripts /E /I /Y
xcopy config dist\command_automator_api\config /E /I /Y