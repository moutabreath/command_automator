pyinstaller command_automator_api.py -i ui/resources/Commands_Automator.ico --onedir --add-data "ui;ui"
xcopy scripts dist\command_automator_api\scripts /E /I /Y
xcopy config dist\command_automator_api\config /E /I /Y