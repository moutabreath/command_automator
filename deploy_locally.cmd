@echo off

REM Kill any running instance of the app before copying
taskkill /IM commands_automator_api.exe /F >nul 2>&1

@REM python -m PyInstaller --clean --debug=all src/commands_automator/commands_automator_api.py -i src/commands_automator/ui/resources/Commands_Automator.ico --onedir --add-data "src/commands_automator/ui;ui" --noconfirm  > build_log.txt 2>&1
@REM python -m PyInstaller  --clean commands_automator_api.spec > build_log.txt 2>&1 -y
.\.venv\Scripts\python.exe  -m PyInstaller ^   src/commands_automator_api.py ^
    -i "src/ui/resources/Commands_Automator.ico" ^
    -F ^
    --add-data "src/ui;ui" ^
    --add-data "src/scripts_manager/config;app/scripts_manager/config" ^
    --add-data "src/scripts_manager/user_scripts;app/scripts_manager/user_scripts" ^
    --add-data "src/llm/mcp_servers/resume/resources;app/llm/mcp_servers/resume/resources" ^
    --add-data "src/llm/mcp_servers/job_search/config;app/llm/mcp_servers/job_search/config" ^
    --hidden-import=mcp.server.fastmcp ^
    --hidden-import=multiprocessing ^
    --hidden-import=multiprocessing.pool ^
    --hidden-import=multiprocessing.managers ^
    --hidden-import=multiprocessing.connection ^
    --hidden-import=aiofiles ^
    --hidden-import=pathlib ^
    -w

if errorlevel 1 (
    echo Build failed. Check build errors.
    exit /b 1
)

copy /Y "dist\commands_automator_api.exe" ".\commands_automator_api.exe" >nul
if errorlevel 1 (
    echo Copy failed: dist\commands_automator_api.exe not found.
    exit /b 1
)

start "" ".\commands_automator_api.exe"