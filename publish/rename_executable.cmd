@echo off

set SOURCE_DIR=.\dist
set "OLD_NAME=commands_automator_initializer.exe"
set "NEW_NAME=commands_automator.exe"

if exist "%SOURCE_DIR%\%OLD_NAME%" (
    echo Renaming %OLD_NAME% to %NEW_NAME%...
    move /Y "%SOURCE_DIR%\%OLD_NAME%" "%SOURCE_DIR%\%NEW_NAME%"
) else (
    echo File "%SOURCE_DIR%\%OLD_NAME%" not found
)