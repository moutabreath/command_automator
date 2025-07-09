pyinstaller command_automator_api.py -i ui/resources/Commands_Automator.ico -F --add-data "ui;ui" -w
xcopy dist\command_automator_api.exe .\command_automator_api.exe /y