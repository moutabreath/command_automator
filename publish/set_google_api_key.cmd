@echo off
echo Adding GOOGLE_API_KEY environment variable...

REM Replace "your_api_key_here" with your actual Google API key
set API_KEY=your_api_key_here

REM Check if the placeholder was replaced
if "%API_KEY%"=="your_api_key_here" (
  echo ERROR: You must replace "your_api_key_here" with your actual Google API key
  echo Please edit this script and set the correct API_KEY value
  pause
  exit /b 1
)
REM Set environment variable for current session
set GOOGLE_API_KEY=%API_KEY%

REM Set environment variable permanently (user-level)
setx GOOGLE_API_KEY "%API_KEY%"
echo.
echo GOOGLE_API_KEY has been set successfully!
echo The GOOGLE_API_KEY has been set for the current session.
echo Note: The permanent environment variable will be available in new command prompt sessions.
echo You may need to restart applications to use the new environment variable.

pause