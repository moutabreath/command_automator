@echo off
set APPDATA_DIR=%APPDATA%\commands_automator
set SOURCE_DIR=..\src

echo Copying configuration files to APPDATA...

REM Copy unified config file
if exist "%SOURCE_DIR%\config\commands_automator.config" (
    if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"
    copy "%SOURCE_DIR%\config\commands_automator.config" "%APPDATA_DIR%\commands_automator.config" /y
    echo Copied unified config to APPDATA
) else (
    echo Warning: unified config not found
)

REM Copy job search config
if exist "%SOURCE_DIR%\llm\mcp_servers\job_search\config" (
    if exist "%APPDATA_DIR%\mcp_servers\job_search\config" rmdir /s /q "%APPDATA_DIR%\mcp_servers\job_search\config"
    xcopy "%SOURCE_DIR%\llm\mcp_servers\job_search\config" "%APPDATA_DIR%\mcp_servers\job_search\config" /e /i /y
    echo Copied job search config to APPDATA
) else (
    echo Warning: job search config not found
)

REM Copy user scripts
if exist "%SOURCE_DIR%\scripts_manager\user_scripts" (
    if exist "%APPDATA_DIR%\scripts_manager\user_scripts" rmdir /s /q "%APPDATA_DIR%\scripts_manager\user_scripts"
    xcopy "%SOURCE_DIR%\scripts_manager\user_scripts" "%APPDATA_DIR%\scripts_manager\user_scripts" /e /i /y
    echo Copied user scripts to APPDATA
) else (
    echo Warning: user scripts not found
)

REM Copy resume resources
if exist "%SOURCE_DIR%\llm\mcp_servers\resume\resources" (
    if exist "%APPDATA_DIR%\mcp_servers\resume\resources" rmdir /s /q "%APPDATA_DIR%\mcp_servers\resume\resources"
    xcopy "%SOURCE_DIR%\llm\mcp_servers\resume\resources" "%APPDATA_DIR%\mcp_servers\resume\resources" /e /i /y
    echo Copied resume resources to APPDATA
) else (
    echo Warning: resume resources not found
)

REM Copy job_titles.json
if exist "%SOURCE_DIR%\jobs_tracking\config\job_titles_keywords.json" (
    copy "%SOURCE_DIR%\jobs_tracking\config\job_titles_keywords.json" "%APPDATA_DIR%\jobs_tracking\config\job_titles_keywords.json" /y
    echo Copied job_titles.json to APPDATA
) else (
    echo Warning: job_titles.json not found
)

REM Copy executable file
if exist "..\commands_automator_api.exe" (
    copy "..\commands_automator_api.exe" "%APPDATA_DIR%\commands_automator_api.exe" /y
    echo Copied executable to APPDATA
) else (
    echo Warning: executable not found
)

REM Copy README file
if exist "..\README.md" (
    copy "..\README.md" "%APPDATA_DIR%\README.md" /y
    echo Copied README to APPDATA
) else (
    echo Warning: README not found
)

echo Configuration files copied successfully