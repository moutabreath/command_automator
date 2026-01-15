@echo off
echo Starting deployment process...
REM Check if --install flag is provided
if "%1"=="--install" (
    echo Running PyInstaller...
    call run_pyinstaller.cmd
    if errorlevel 1 (
        echo PyInstaller failed
        exit /b 1
    )
)

echo Kill process started
    
REM Kill existing processes
call kill_process.cmd
echo "%1"

echo Copy file started

REM Copy configuration files
call copy_files.cmd
if errorlevel 1 (
    echo Failed to copy configuration files
    exit /b 1
)

echo Starting process
REM Start the process
call start_process.cmd
if errorlevel 1 (
    echo Failed to start process
    exit /b 1
)

echo Deployment completed successfully