import glob
import os
import shutil
from datetime import datetime

def copy_to_deploy():
    # Source and destination paths
    source_dir = os.path.dirname(os.path.abspath(__file__))  # Current directory
    deploy_dir = os.path.join(source_dir, 'deploy')
    
    # Create timestamp folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    deploy_dir = os.path.join(deploy_dir, timestamp)
    
    # Create deploy directory if it doesn't exist
    os.makedirs(deploy_dir, exist_ok=True)
    
    try:
        # List of specific files to copy
        files_to_copy = [
            'command_automator.exe',
            'chatbot_keys.txt'
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
            'configs',
            'actionables'
        ]
        
        for folder_name in folders_to_copy:
            source_folder = os.path.join(source_dir, folder_name)
            dest_folder = os.path.join(deploy_dir, folder_name)
            
            if os.path.exists(source_folder):
                shutil.copytree(source_folder, dest_folder)
                print(f"Copied {folder_name} folder and its contents")
            else:
                print(f"Warning: {folder_name} folder not found in source directory")
        files = glob.glob(os.getcwd() + '/**/chat_bot_keys.txt', recursive=True)
        shutil.copyfile(files[0], f'{deploy_dir}/configs/chatbot_keys.txt')
        print(f"\nDeployment completed successfully!")
        print(f"Files deployed to: {deploy_dir}")
        
    except Exception as e:
        print(f"Error during deployment: {str(e)}")
        raise  # Re-raise the exception for debugging

def find_chatbot_keys():
    """Recursively search for chatbot_keys.txt in the current directory and its subdirectories"""
    source_dir = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(source_dir):
        if 'chatbot_keys.txt' in files:
            return os.path.join(root, 'chatbot_keys.txt')
    return None

if __name__ == "__main__":
    copy_to_deploy()
