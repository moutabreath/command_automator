@echo off
setlocal enabledelayedexpansion

:: Check if port number was provided
if "%~1"=="" (
    echo Usage: %~nx0 [port_number]
    echo Example: %~nx0 8080
    exit /b 1
)

set PORT=%~1

:: Validate that input is a number
echo %PORT%| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo Error: Port must be a valid number
    exit /b 1
)

:: Validate port range
if %PORT% LSS 1 (
    echo Error: Port must be between 1 and 65535
    exit /b 1
)
if %PORT% GTR 65535 (
    echo Error: Port must be between 1 and 65535
    exit /b 1
)
echo Searching for process using port %PORT%...

:: Find the PID using the port
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT% "') do (
    set PID=%%a
    goto :found
)

echo No process found using port %PORT%
exit /b 0

:found
:: Get process name
for /f "tokens=1" %%a in ('tasklist /fi "PID eq %PID%" /fo table /nh') do (
    set PROCESS_NAME=%%a
)

if "!PROCESS_NAME!"=="" (
    echo Error: Could not retrieve process name for PID %PID%
    exit /b 1
)
echo Found process: %PROCESS_NAME% (PID: %PID%)
echo Killing process...

:: Kill the process
taskkill /F /PID %PID%

if errorlevel 1 (
    echo Error: Failed to kill process. You may need administrator privileges.
    exit /b 1
) else (
    echo Process killed successfully!
    exit /b 0
)