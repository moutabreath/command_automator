@echo off

REM Kill any running instance of the app before copying
taskkill /IM commands_automator_api.exe /F >nul 2>&1


@REM python -m PyInstaller --clean --debug=all src/commands_automator/commands_automator_api.py -i src/commands_automator/ui/resources/Commands_Automator.ico --onedir --add-data "src/commands_automator/ui;ui" --noconfirm  > build_log.txt 2>&1
@REM python -m PyInstaller  --clean commands_automator_api.spec > build_log.txt 2>&1 -y
.\.venv\Scripts\python.exe -m PyInstaller src/commands_automator/commands_automator_api.py ^
    -i src/commands_automator/ui/resources/Commands_Automator.ico ^
    -F ^
    --add-data "src/commands_automator/ui;ui" ^
    --add-data "src/commands_automator/config;config" ^
    --add-data "src/commands_automator/llm;llm" ^
    --add-data "src/commands_automator/llm/mcp_servers/resume/resources;llm/mcp_servers/resume/resources" ^
    --hidden-import mcp.server.fastmcp ^
    --hidden-import multiprocessing ^
    --hidden-import multiprocessing.pool ^
    --hidden-import multiprocessing.managers ^
    --hidden-import multiprocessing.connection ^
    -w

if errorlevel 1 (
    echo Build failed. Check build errors.& exit /b 1
)

copy /Y "dist\commands_automator_api.exe" ".\commands_automator_api.exe" >nul
if errorlevel 1 (
  echo Copy failed: dist\commands_automator_api.exe not found.& exit /b 1
)
start "" ".\commands_automator_api.exe"