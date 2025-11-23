@echo off
SETLOCAL

rem Usage: kill_app_with_name.cmd [process_name]
rem If no process_name is provided, defaults to "commands_automator_api.exe"
if "%~1"=="" (
    set "EXE=commands_automator_api.exe"
) else (
    set "EXE=%~1"
)

rem Ensure .exe suffix for tasklist/taskkill comparisons
if /I not "%EXE:~-4%"==".exe" (
    set "EXE=%EXE%.exe"
)

set "NAME=%EXE%"

echo Looking for %EXE% ...
tasklist /FI "IMAGENAME eq %NAME%" | find /I "%NAME%" >nul
if errorlevel 1 (
    echo No running %EXE% found.
    exit /b 0
)

echo Terminating %EXE% ...
taskkill /IM "%NAME%" /F >nul 2>&1

REM wait up to 10 seconds for processes to disappear
set /a COUNT=0
:waitloop
tasklist /FI "IMAGENAME eq %NAME%" | find /I "%NAME%" >nul
if errorlevel 1 (
    echo %EXE% stopped.
    exit /b 0
)
set /a COUNT+=1
if %COUNT% GEQ 50 (
    echo Failed to stop %EXE% after timeout.
    exit /b 1
)
timeout /t 0 /nobreak >nul
ping -n 1 127.0.0.1 >nul
goto waitloop