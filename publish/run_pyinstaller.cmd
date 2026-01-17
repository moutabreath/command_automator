@echo off

@REM python -m PyInstaller --clean --debug=all src/commands_automator/commands_automator_api.py -i src/commands_automator/ui/resources/Commands_Automator.ico --onedir --add-data "src/commands_automator/ui;ui" --noconfirm  > build_log.txt 2>&1
@REM python -m PyInstaller  --clean commands_automator_api.spec > build_log.txt 2>&1 -y


@REM add certifi for https imports such as bootstrap
..\.venv\Scripts\python.exe -m PyInstaller ^
    ..\src\commands_automator_initializer.py ^
    -i "..\src\ui\resources\Commands_Automator.ico" ^
    -F ^
    --add-data "..\src\ui;ui" ^
    --hidden-import=mcp.server.fastmcp ^
    --hidden-import=multiprocessing ^
    --hidden-import=multiprocessing.pool ^
    --hidden-import=multiprocessing.managers ^
    --hidden-import=multiprocessing.connection ^
    --hidden-import=aiofiles ^
    --hidden-import=pathlib ^
    --hidden-import=dependency_injector ^
    --hidden-import=dependency_injector.errors ^
    --hidden-import=dependency_injector.containers ^
    --hidden-import=dependency_injector.providers ^
    --hidden-import=dependency_injector.wiring ^
    --hidden-import=dependency_injector.resources ^
    --hidden-import=certifi ^
    --windowed

if errorlevel 1 (
    echo Build failed. Check build errors.
    exit /b 1
)