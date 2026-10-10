@echo off
echo Adding GOOGLE_API_KEY environment variable...

REM Pass the Google API key as the first script argument.
if "%~1"=="" (
  echo ERROR: Google API key is required.
  echo Usage: %~nx0 YOUR_GOOGLE_API_KEY
  pause
  exit /b 1
)

REM Set environment variable for current session
set "GOOGLE_API_KEY=%~1"

REM Set environment variable permanently (user-level)
setx GOOGLE_API_KEY "%~1"
echo.
echo GOOGLE_API_KEY has been set successfully!
echo The GOOGLE_API_KEY has been set for the current session.
echo Note: The permanent environment variable will be available in new command prompt sessions.
echo You may need to restart applications to use the new environment variable.
