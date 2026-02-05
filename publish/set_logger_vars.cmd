@echo off
echo Setting environment variables for Commands Automator...

set LOG_LEVEL=DEBUG
set LOG_FILE=commands_automator.log

REM Set environment variables for current session
set LOG_LEVEL=%LOG_LEVEL%
set LOG_FILE=%LOG_FILE%

REM Set environment variables permanently (user-level)
setx LOG_LEVEL "%LOG_LEVEL%"
setx LOG_FILE "%LOG_FILE%"

echo.
echo Environment variables have been set successfully!
echo Note: The permanent environment variables will be available in new command prompt sessions.

pause
