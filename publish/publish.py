import os
import subprocess
from sys import argv


current_dir = os.path.dirname(os.path.abspath(__file__))  # Current directory
base_dir = os.path.dirname(current_dir)
source_code_dir = os.path.join(base_dir, 'src')  # Source code directory
deploy_dir = "dist"


def kill_process():
    """Kills the commands_automator_api.exe process using CMD script"""
    try:
        subprocess.run(['kill_process.cmd'], cwd=current_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Process killed successfully")
    except Exception as e:
        print(f"Warning: Error killing process: {e}")



def start_process():
    """Starts the commands_automator_api.exe process using CMD script"""
    try:
        subprocess.run(['start_process.cmd'], cwd=current_dir, check=True)
        print("Start process script executed")
    except subprocess.CalledProcessError as e:
        print(f"Error starting process: {e}")
    except FileNotFoundError:
        print("Warning: start_process.cmd not found")

def copy_config_and_resources():
    """Copy configuration files using CMD script"""
    try:
        result = subprocess.run(['copy_files.cmd'], cwd=current_dir, check=True, capture_output=True, text=True)
        print("Configuration files copied successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error copying config files: {e.stderr}")
    except FileNotFoundError:
        print("Warning: copy_config.cmd not found")

def run_pyinstaller():
    print("Running deploy_locally.cmd...")
    try:
        result = subprocess.run(['run_pyinstaller.cmd'], cwd=current_dir, check=True, capture_output=True, text=True)
        print("Deploy script completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"Deploy script failed with return code {e.returncode}")
        print(f"Error output: {e.stderr}")
        raise
    except FileNotFoundError:
        print("Warning: deploy_locally.cmd not found")

if __name__ == "__main__":    
    kill_process()
    if len(argv) > 1:
        if argv[1] == "--install":
            run_pyinstaller()
    copy_config_and_resources()
    start_process()
    
