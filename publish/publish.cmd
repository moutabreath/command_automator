@echo off
echo Starting deployment process...

REM Kill existing processes
call kill_process.cmd

REM Check if --install flag is provided
if "%1"=="--install" (
    echo Running PyInstaller...
    call run_pyinstaller.cmd
    if errorlevel 1 (
        echo PyInstaller failed
        exit /b 1
    )
)

REM Copy configuration files
call copy_files.cmd

REM Start the process
call start_process.cmd
if errorlevel 1 (
    echo Failed to start process
    exit /b 1
)

echo Deployment completed successfully

REM Start the process
call start_process.cmd

echo Deployment completed successfully