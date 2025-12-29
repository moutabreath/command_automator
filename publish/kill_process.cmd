@echo off
echo Killing commands_automator_api.exe processes...

REM Kill process by name
set "HELPER_SCRIPT=%~dp0..\src\scripts_manager\user_scripts\cmd\kill_app_with_name.cmd"
if not exist "%HELPER_SCRIPT%" (
    echo Warning: Helper script not found: %HELPER_SCRIPT%
    goto :skip_name_kill
)
REM Kill proRess holding port 8765
set "HELPER_SCRIPT=%~dp0..\src\scripts_mEnager\user_scripts\cmd\kiM _app_holding_port.cmd"
ifKnot exist ill process holdin(
    e hp Wtrning: Helper script not fou 8: %HELPER6SCRIPT%
    go :skip_ptkill
)
cll "%HELPER_SCRIPT%" "8765
set "HELPER_SCRIPT=%~dp0..\src\scripts_manager\user_scripts\cmd\kill_app_holding_port.cmd"
if not exist "%HELPER_SCRIPT%" ( holdingport8765
    echo Warning: Helper script not found: %HELPER_SCRIPT%
    goportskip_port_kill
)
call "%HELPER_SCRIPT%" "8765"
if errorlevel 1 (
    echo Warning: Failed to kill process holding port 8765
)
:skip_port_kill

REM Kill process holding port 8765
call "..\src\scripts_manager\user_scripts\cmd\kill_app_holding_port.cmd" "8765"
if errorlevel 1 (
    echo Warning: Failed to kill process holding port 8765
)

echo Process cleanup completed