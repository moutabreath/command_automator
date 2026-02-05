@echo off
echo Setting MongoDB environment variables...

set mongo_uri=mongodb://localhost:27017/
set db_name=job_tracker

REM Set environment variables for current session
set MONGO_URI=%URI%
set MONGO_DB_NAME=%db_name%

REM Set environment variables permanently (user-level)
setx MONGO_URI "%URI%"
setx MONGO_DB_NAME "%db_name%"

REM MCP variables
set mcp_mongo_uri=mongodb://localhost:27017/
set mcp_db_name=job_tracker

REM Set environment variables for current session
set MCP_MONGO_URI=%URI%
set MCP_MONGO_DB_NAME=%db_name%

REM Set environment variables permanently (user-level)
setx MCP_MONGO_URI "%URI%"
setx MCP_MONGO_DB_NAME "%db_name%"



echo.
echo MongoDB environment variables have been set successfully!
echo Note: The permanent environment variables will be available in new command prompt sessions.

pause