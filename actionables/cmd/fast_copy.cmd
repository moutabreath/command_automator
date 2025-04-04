set source=%1%
set destination=%2%
if exist "%source%" (
    xcopy "%source%" "%destination%"
) else (
    robocopy "%source%" "%destination%" /S /E /MT:16 /NFL /NDL /NJH /NJS
)