if "%~1"=="" (
    echo Usage: %0 ^<source^> ^<destination^>
    exit /b 1
)
if "%~2"=="" (
    echo Usage: %0 ^<source^> ^<destination^>
    exit /b 1
)
set source=%~1
set destination=%~2if not exist "%source%" (
    echo Error: Source path does not exist
    exit /b 1
)

if exist "%source%\*" (
    robocopy "%source%" "%destination%" /S /E /MT:16 /NFL /NDL /NJH /NJS
    if %ERRORLEVEL% LSS 8 exit /b 0
) else (
    xcopy "%source%" "%destination%" /Y /I
)