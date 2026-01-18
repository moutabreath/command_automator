@echo off
echo Starting commands_automator.exe...

set EXE_PATH=%APPDATA%\commands_automator\commands_automator.exe

if exist "%EXE_PATH%" (
    start "" "%EXE_PATH%"
    echo Process started.
) else (
    echo Warning: Executable not found at %EXE_PATH%
)