@echo off
echo Setting MongoDB environment variables...

set mongo_uri=mongodb://localhost:27017/
set DB_NAME=job_tracker

REM Set environment variables for current session
set MONGODB_URI=%URI%
set MONGODB_DB_NAME=%DB_NAME%

REM Set environment variables permanently (user-level)
setx MONGODB_URI "%URI%"
setx MONGODB_DB_NAME "%DB_NAME%"

echo.
echo MongoDB environment variables have been set successfully!
echo Note: The permanent environment variables will be available in new command prompt sessions.

pause