@echo off
echo Adding GOOGLE_API_KEY environment variable...

REM Replace "your_api_key_here" with your actual Google API key
set API_KEY=your_api_key_here

REM Set environment variable for current session
set GOOGLE_API_KEY=%API_KEY%

REM Set environment variable permanently (system-wide)
setx GOOGLE_API_KEY "%API_KEY%"

echo.
echo GOOGLE_API_KEY has been set successfully!
echo Current session value: %GOOGLE_API_KEY%
echo.
echo Note: The permanent environment variable will be available in new command prompt sessions.
echo You may need to restart applications to use the new environment variable.

pause