@echo off
echo Setting MCP environment variables...


REM Mongo MCP variables

set mongo_uri=mongodb://localhost:27017/
set db_name=job_tracker

set mcp_mongo_uri=mongodb://localhost:27017/
set mcp_db_name=job_tracker
set MCP_APPLICATION_COLLECTION_NAME=job_applications

REM Set environment variables for current session
set MCP_MONGO_URI=%mongo_uri%
set MCP_MONGO_DB_NAME=%db_name%
set MCP_APPLICATION_COLLECTION_NAME=%MCP_APPLICATION_COLLECTION_NAME%

REM Set environment variables permanently (user-level)
setx MCP_MONGO_URI "%mongo_uri%"
setx MCP_MONGO_DB_NAME "%db_name%"
setx MCP_APPLICATION_COLLECTION_NAME "%MCP_APPLICATION_COLLECTION_NAME%"


REM MCP host variables
set mcp_host="127.0.0.1"
set mcp_port=8765


REM Set environment variables for current session
set MCP_HOST=%mcp_host%
set MCP_PORT=%mcp_port%

REM Set environment variables permanently (user-level)
setx MCP_HOST "%mcp_host%"
setx MCP_PORT "%mcp_port%"



echo.
echo MCP environment variables have been set successfully!
echo Note: The permanent environment variables will be available in new command prompt sessions.

pause