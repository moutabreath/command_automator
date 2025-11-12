@echo off
setlocal

REM Usage check
if "%~1"=="" (
    echo Usage: %~nx0 ^<source^> ^<destination^>
    exit /b 1
)
if "%~2"=="" (
    echo Usage: %~nx0 ^<source^> ^<destination^>
    exit /b 1
)

set "source=%~1"
set "destination=%~2"

if not exist "%source%" (
    echo Error: Source path does not exist: "%source%"
    exit /b 1
)

REM If source is a directory (has children), use robocopy
if exist "%source%\*" (
    REM Ensure destination directory exists
    if not exist "%destination%" mkdir "%destination%"
    robocopy "%source%" "%destination%" /S /E /MT:16 /NFL /NDL /NJH /NJS
    set "rc=%ERRORLEVEL%"
    if %rc% GEQ 8 (
        echo Error: Robocopy failed with exit code %rc%
        exit /b 1
    ) else (
        echo Robocopy completed (exit code %rc%)
        exit /b 0
    )
) else (
    REM Source is a file
    REM If destination is an existing directory, copy into it
    if exist "%destination%\" (
        copy /Y "%source%" "%destination%\" >nul
    ) else (
        REM Ensure destination parent exists
        for %%I in ("%destination%") do set "destdir=%%~dpI"
        if not exist "%destdir%" mkdir "%destdir%"
        copy /Y "%source%" "%destination%" >nul
    )
    if errorlevel 1 (
        echo Error: File copy failed
        exit /b 1
    ) else (
        echo File copied successfully
        exit /b 0
    )
)