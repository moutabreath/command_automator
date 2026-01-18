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

REM rename exe file
echo Renaming executable...
call rename_executable.cmd

REM Kill existing processes
echo Kill process started    
call kill_process.cmd

REM Copy configuration files
echo Copy file started
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