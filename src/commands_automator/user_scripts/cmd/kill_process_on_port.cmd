@echo off
setlocal enabledelayedexpansion

REM Check if port parameter is provided
if "%1"=="" (
    echo Usage: %0 ^<port_number^>
    echo Example: %0 8765
    exit /b 1
)

set "PORT=%~1"

REM Validate numeric port (1-65535)
echo(%PORT%| findstr /R "^[0-9][0-9]*$" >nul || (echo Invalid port: %PORT% & exit /b 2))
set /a PORT_NUM=%PORT% >nul 2>&1 || (echo Invalid port: %PORT% & exit /b 2)

for /f "tokens=5" %%i in ('netstat -ano -p TCP ^| findstr /R /C:":%PORT% .*LISTENING"') do (
    set "PID=%%i"
    if not "!PID!"=="" (
        echo Found process with PID: !PID!
        taskkill /F /PID !PID!
        if !ERRORLEVEL! EQU 0 (
            echo Successfully killed process with PID !PID!
        ) else (
            echo Failed to kill process with PID !PID!
            exit /b 3
        )
        exit /b 0
    )
)

echo No process found using port %PORT%
exit /b 0

echo Done.