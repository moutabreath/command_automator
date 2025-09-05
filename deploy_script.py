import os
import shutil
from datetime import datetime

def copy_to_deploy():
    # Source and destination paths
    source_dir = os.path.dirname(os.path.abspath(__file__))  # Current directory
    deploy_dir = os.path.join(source_dir, 'deploy')
    
    # Create timestamp folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
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
            'src/commands_automator/user_scripts',
            'src/commands_automator/ui/resources',
            'src/commands_automator/llm/resources',
            'src/commands_automator/config'
        ]
        
        for folder_name in folders_to_copy:
            source_folder = os.path.join(source_dir, folder_name)
            dest_folder = os.path.join(deploy_dir, folder_name)
            
            if os.path.exists(source_folder):
                shutil.copytree(source_folder, dest_folder)
                print(f"Copied {folder_name} folder and its contents")
            else:
                print(f"Warning: {folder_name} folder not found in source directory")
        print(f"\nDeployment completed successfully!")
        print(f"Files deployed to: {deploy_dir}")        
    except Exception as e:
        print(f"Error during deployment: {str(e)}")
        raise  # Re-raise the exception for debugging



if __name__ == "__main__":
    copy_to_deploy()
