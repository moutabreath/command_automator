set source=%1%
set destination=%2%
if not exist "%source%" (
    echo Error: Source path does not exist
    exit /b 1
)

if exist "%source%\*" (
    robocopy "%source%" "%destination%" /S /E /MT:16 /NFL /NDL /NJH /NJS
) else (
    xcopy "%source%" "%destination%"
)