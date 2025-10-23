if "%~1"=="" (
    echo Usage: %0 ^<source^> ^<destination^>
    exit /b 1
)
if "%~2"=="" (
    echo Usage: %0 ^<source^> ^<destination^>
    exit /b 1
)
set source=%1%
set destination=%2%
if not exist "%source%" (
    echo Error: Source path does not exist
    exit /b 1
)

if exist "%source%\*" (
    robocopy "%source%" "%destination%" /S /E /MT:16 /NFL /NDL /NJH /NJS
) else (
    xcopy "%source%" "%destination%" /Y /I
    if errorlevel 1 (
        echo Error: XCopy failed
            exit /b 1
        )
)