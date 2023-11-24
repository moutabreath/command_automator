@echo off
setlocal

echo Checking free space on drive C:

for /f "skip=1" %%a in ('wmic logicaldisk where "DeviceID='C:'" get FreeSpace') do (
    set "freeSpace=%%a"
    goto :done
)

:done
echo Free space on drive C: %freeSpace% bytes

endlocal