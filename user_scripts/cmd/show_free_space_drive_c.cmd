fsutil volume diskfree C:
@REM @echo off
@REM setlocal

@REM echo Checking free space on drive C:

@REM for /f "skip=1" %%a in ('wmic logicaldisk where "DeviceID='C:'" get FreeSpace') do (
@REM     set "freeSpace=%%a"
@REM     goto :done
@REM )

@REM :done
@REM echo Free space on drive C: %freeSpace% bytes

@REM endlocal