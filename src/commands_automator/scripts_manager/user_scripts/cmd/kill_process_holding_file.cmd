@echo off
setlocal enabledelayedexpansion

REM Check if a filename was provided
if "%~1"=="" (
    echo Usage: %~nx0 ^<filename^>
    echo Example: %~nx0 document.txt
    echo Example: %~nx0 "C:\path\to\file.xlsx"
    exit /b 1
)

set "filename=%~1"

REM Check if file exists
if not exist "%filename%" (
    echo Error: File "%filename%" not found.
    exit /b 1
)

echo Searching for processes using "%filename%"...
echo.

REM Use handle.exe from Sysinternals if available
where handle.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo Using handle.exe to find processes...
    for /f "tokens=3,5" %%a in ('handle.exe "%filename%" ^| findstr /i "%filename%"') do (
        set "pid=%%a"
        set "pid=!pid:pid:=!"
        if defined pid (
            for /f "tokens=1" %%p in ("!pid!") do (
                echo Found process using file: PID %%p
                set /p "confirm=Kill process %%p? (Y/N): "
                if /i "!confirm!"=="Y" (
                    taskkill /F /PID %%p
                    if !errorlevel! equ 0 (
                        echo Successfully killed process %%p
                    ) else (
                        echo Failed to kill process %%p
                    )
                )
            )
        )
    )
    goto :end
)

REM Fallback method using openfiles (requires admin)
echo handle.exe not found. Trying openfiles command...
echo Note: This requires administrative privileges.
echo.

openfiles /query /fo csv /v 2>nul | findstr /i "%filename%" >nul
if %errorlevel% neq 0 (
    echo No processes found using "%filename%"
    echo.
    echo Tip: Download handle.exe from Sysinternals for better results:
    echo https://learn.microsoft.com/en-us/sysinternals/downloads/handle
    goto :end
)

echo The file is in use, but openfiles cannot identify the specific process.
echo Please install handle.exe from Sysinternals for accurate process identification.

:end
echo.
echo Done.
endlocal