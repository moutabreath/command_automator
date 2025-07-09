pyinstaller command_automator_api.pyw -i ui/resources/Commands_Automator.ico -F --add-data "ui;ui"
xcopy dist\command_automator_api.exe .\command_automator_api.exe /y