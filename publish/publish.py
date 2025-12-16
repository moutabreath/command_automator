import os
import shutil
import subprocess
from datetime import datetime


source_dir = os.path.dirname(os.path.abspath(__file__))  # Current directory

def copy_to_deploy():
    """
    Create a timestamped deployment directory and copy application files.
    
    Creates a directory at ./deploy/commands_automator_api_<timestamp>/ and copies
    the executable, README, and required resource folders. Prints warnings for
    missing files/folders but continues execution.
    
    Raises:
        Exception: Re-raises any exception encountered during file operations.
    """
    # Source and destination paths
    deploy_dir = os.path.join(source_dir, 'deploy')
    
    # Create timestamp folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    deploy_dir = os.path.join(deploy_dir, f'commands_automator_api_{timestamp}')
    
    # Create deploy directory if it doesn't exist
    os.makedirs(deploy_dir, exist_ok=True)
    
  
    
    try:
        # List of specific files to copy
        files_to_copy = [
            'commands_automator_api.exe',
            'README.md'
        ]
        
        # Copy individual files
        for file_name in files_to_copy:
            source_file = os.path.join(source_dir, file_name)
            dest_file = os.path.join(deploy_dir, file_name)
            
            if os.path.exists(source_file):
                shutil.copy2(source_file, dest_file)
                print(f"Copied {file_name}")
            else:
                print(f"Warning: {file_name} not found in source directory")
        
        # Copy folders with their structure
        folders_to_copy = [
            'src/scripts_manager/user_scripts',
            'src/ui/resources',
            'src/llm/resources',
            'src/scripts_manager/config'
        ]
        
        for folder_name in folders_to_copy:
            source_folder = os.path.join(source_dir, folder_name)
            dest_folder = os.path.join(deploy_dir, folder_name)
            
            if os.path.exists(source_folder):
                shutil.copytree(source_folder, dest_folder, dirs_exist_ok=True)
                print(f"Copied {folder_name} folder and its contents")
            else:
                print(f"Warning: {folder_name} folder not found in source directory")
        print(f"Files deployed to: {deploy_dir}")        
    except Exception as e:
        print(f"Error during deployment: {str(e)}")
        raise  # Re-raise the exception for debugging

def run_pyinstaller():
      # Run deploy_locally.cmd before copying
    print("Running deploy_locally.cmd...")
    try:
        result = subprocess.run(['deploy_locally.cmd'], cwd=source_dir, check=True, capture_output=True, text=True)
        print("Deploy script completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Deploy script failed with return code {e.returncode}")
        print(f"Error output: {e.stderr}")
        raise
    except FileNotFoundError:
        print("Warning: deploy_locally.cmd not found")

if __name__ == "__main__":
    run_pyinstaller()
    copy_to_deploy()
