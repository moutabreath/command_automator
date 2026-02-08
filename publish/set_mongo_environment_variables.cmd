@echo off
echo Setting MongoDB environment variables...

set mongo_uri=mongodb://localhost:27017/
set db_name=job_tracker
set job_applications_collection_name=job_applications

REM Set environment variables for current session
set MONGO_URI=%mongo_uri%
set MONGO_DB_NAME=%db_name%
set JOB_APPLICATIONS_COLLECTION_NAME=%job_applications_collection_name%

REM Set environment variables permanently (user-level)
setx MONGO_URI "%mongo_uri%"
setx MONGO_DB_NAME "%db_name%"
setx JOB_APPLICATIONS_COLLECTION_NAME "%job_applications_collection_name%"


echo.
echo MongoDB environment variables have been set successfully!
echo Note: The permanent environment variables will be available in new command prompt sessions.

pause