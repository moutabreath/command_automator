@echo off
echo Killing commands_automator_api.exe processes...

REM Kill process by name
call "..\src\scripts_manager\user_scripts\cmd\kill_app_with_name.cmd" "commands_automator_api.exe"

REM Kill process holding port 8765
call "..\src\scripts_manager\user_scripts\cmd\kill_app_holding_port.cmd" "8765"

echo Process cleanup completed