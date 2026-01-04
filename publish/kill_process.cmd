@echo off
echo Killing commands_automator_api.exe processes...

REM Kill process by name
set "HELPER_SCRIPT=%~dp0..\src\scripts_manager\user_scripts\cmd\kill_app_with_name.cmd"
if not exist "%HELPER_SCRIPT%" (
    echo Warning: Helper script not found: %HELPER_SCRIPT%
    goto :skip_name_kill
)
call "%HELPER_SCRIPT%" "commands_automator_api.exe"
set "HELPER_SCRIPT=%~dp0..\src\scripts_manager\user_scripts\cmd\kill_app_holding_port.cmd"
if not exist "%HELPER_SCRIPT%" ( 
    echo Warning: Helper script not found: %HELPER_SCRIPT%
    goto skip_port_kill
)
call "%HELPER_SCRIPT%" "8765
:skip_port_kill


echo Process cleanup completed