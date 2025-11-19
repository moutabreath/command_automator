@echo off
setlocal
fsutil volume diskfree C:
if %errorlevel% neq 0 (
    echo Error: Unable to check free space on drive C:
    exit /b 1
)

endlocal