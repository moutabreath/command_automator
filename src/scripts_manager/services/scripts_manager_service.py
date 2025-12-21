import glob
import json
import logging
import os
import platform
import subprocess
import chardet
from typing import List, Dict, Optional, Tuple, Union

from utils.file_utils import USER_SCRIPTS_CONFIG_FILE, USER_SCRIPTS_DIR


class ScriptsManagerService:
    def __init__(self):
        self.names_to_scripts: Dict[str, str] = {}
        self.scripts_attributes: Dict[str, Dict] = {}
        self.load_scripts_config()

    def load_scripts_config(self) -> None:
        try:  
            with open(f'{USER_SCRIPTS_CONFIG_FILE}') as f:  
                data = json.load(f)  
        except (FileNotFoundError, OSError) as e:
            logging.error("Error loading scripts_config.json", exc_info=True)  
            return
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in scripts_config.json: {e}", exc_info=True)
            return  
        scripts_config = data.get('scripts', [])
        if not scripts_config:
            logging.warning("No scripts found in scripts_config.json")
            return
        for script in scripts_config:  
            script_name = script.get('script_name', '')
            tag_name = script.get('short_description', '')
            script_desc = script.get('detailed_description', '')
            if script_name == "" or tag_name == "" or script_desc == "":  
                continue  
            self.scripts_attributes[script_name] = script

    def get_name_to_scripts(self):
        return self.names_to_scripts

    def load_scripts(self) -> List[str]:
        """
        Load all executable scripts from the scripts directory.
        Returns:
            List[str]: List of executable script names
        """
        executables = []
        self.names_to_scripts.clear()
        
        # Get all script files
        extensions = ['*.py', '*.sh', '*.cmd', '*.exe']
        files = []
        try:            
            for ext in extensions:
                files.extend(glob.glob(f'{USER_SCRIPTS_DIR}/**/{ext}', recursive=True))

        except Exception as e:
            logging.error(f"Error loading scripts: {e}", exc_info=True)
     
        # Process each file
        for file in files:
            file_name = self.get_name_from_script(file)
            if file_name is None:
                file_name = os.path.basename(file)
            self.names_to_scripts[file_name] = file
            executables.append(file_name)

        # Sort alphabetically, case-insensitive
        executables.sort(key=str.lower)
        logging.debug(f"Loaded {len(executables)} scripts")
        return executables

    def get_script_attribute(self, file: str, attribute: str) -> str:
        script_name = os.path.basename(file)
        if script_name in self.scripts_attributes:
            return self.scripts_attributes[script_name].get(attribute, "")
        return ""
    
    def get_name_from_script(self, file: str) -> str:
        return self.get_script_attribute(file, 'short_description')

    def get_script_description(self, file: str) -> str:
        return self.get_script_attribute(file, 'detailed_description')

    def get_arguments_for_script(self, script_path: str, additional_text: str, flags: str) -> Optional[List[str]]:
        script_name = os.path.basename(script_path)
        args = []
        if script_name.endswith('.py'):
            args.append('python')
        elif script_name.endswith('.sh'):
            args.append('bash')
        elif script_name.endswith('.cmd'):
            args.append('cmd')
            args.append('/c')      
        args.append(script_path)

        if additional_text:
            args.append(additional_text)
        if self.should_use_free_text(script_name):
            if additional_text == "" or additional_text is None:
                return None
            # Split flags and filter empty strings
            args.extend(flags.split())    
        other_script_name_as_input = self.get_other_script_name_as_input(script_name)
        if other_script_name_as_input is not None:
            if '..' in other_script_name_as_input or os.path.isabs(other_script_name_as_input):
                logging.error(f"Invalid script name contains path traversal: {other_script_name_as_input}")
                return None
            base_dir = os.path.dirname(os.path.dirname(SCRIPTS_DIR))
            cleaners_path = os.path.join(base_dir, 'cleaners')
            files = glob.glob(f'{cleaners_path}/**/{other_script_name_as_input}', recursive=True)
            if files:
                f_drive_cleaner_path = files[0]
                args.append(f_drive_cleaner_path)
            else:
                logging.warning(f"Script '{other_script_name_as_input}' not found in cleaners directory")
        logging.log(logging.DEBUG, "running " + str(args))
        return args
       
    @staticmethod
    def get_updated_venv(arg):
        if not (arg and arg.lower().startswith('python')):
            return
        
        new_venv = os.environ.copy()
        python_env = new_venv.get("PYTHONPATH", "")
        logging.log(logging.DEBUG, "PYTHONPATH before " + new_venv.get("PYTHONPATH", ""))

        sep = ';' if platform.system() == 'Windows' else ':'
        paths = python_env.split(sep) if python_env else []
        cwd = os.getcwd()

        if (len(python_env) != 0) and (python_env[-1] != sep):
            new_venv["PYTHONPATH"] = new_venv.get("PYTHONPATH", "") + sep
        if cwd not in paths:
            new_venv["PYTHONPATH"] = new_venv.get("PYTHONPATH", "") + cwd + sep
        return new_venv
    
    @staticmethod
    def run_app(run_version_command: str) -> None:
        """Run a command."""
        startupinfo = None
        if platform.system() == 'Windows':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo = si
        # Ensure we're using the safe list form
        if isinstance(run_version_command, str):
            logging.error("run_app requires list form for safety, not string")
            raise TypeError("run_version_command must be a list, not string")
        try:
            subprocess.run(run_version_command, startupinfo=startupinfo, shell=False, check=True)
        except subprocess.CalledProcessError as e:
            logging.exception(f"Command failed: {e}")

    def get_string_from_thread_result(self, result: Union[bytes, bytearray], err: Optional[Union[str, bytes]]) -> str:
 
        str_result = ""
        logging.log(logging.DEBUG, "entered.")
        if isinstance(result, (bytes, bytearray)):
            encoding_stats = chardet.detect(result)
            encoding = encoding_stats['encoding']
            if encoding is not None:
                str_result = result.decode(encoding)
            else:
                logging.log(logging.DEBUG, "encoding is None")
                str_result = ""
        if err is not None:
            if isinstance(err, str):
                logging.error(f"Error during execution: {err}")
                str_result = str_result + " " + err

        if len(str_result) == 0:
            str_result = "Execution Done"
        return str_result

    def should_use_free_text(self, script_name):
        if script_name in self.scripts_attributes:
            return self.scripts_attributes[script_name].get('free_text_required', False)
        return False
            
    
    def get_other_script_name_as_input(self, script_name: str) -> Optional[str]:
        if script_name in self.scripts_attributes:
            return self.scripts_attributes[script_name].get('other_script_name_as_input')
        return None


    @staticmethod
    def is_dir_empty(dir_path):
        try:
            return not next(os.scandir(dir_path), None)
        except (FileNotFoundError, NotADirectoryError) as e:
            logging.error(f"Invalid directory path '{dir_path}': {e}")
            return True
    

    def execute_script(self, script_name: str, additional_text: str, flags: str) -> str:
        script_path = self.get_name_to_scripts().get(script_name, script_name)
        args = self.get_arguments_for_script(script_path, additional_text, flags)
        if args is None:
            return "error : Missing argument. Please fill the text box for Additional Text"
        new_venv = self.get_updated_venv(args[0])
        output, err  = self.run_internal(args, new_venv)
        return self.get_string_from_thread_result(output, err)

    def run_internal(self, args: List[str], venv: Dict[str, str]) -> Tuple[bytes, bytes]:
        logging.log(logging.DEBUG, "entered")
        proc = None
        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=venv)
            logging.log(logging.DEBUG, "popen done")
            output, err = proc.communicate(timeout=300) # 5 minute timeout
            logging.log(logging.DEBUG, "proc communicate done")
            if proc.returncode != 0:
                logging.warning(f"Process exited with code {proc.returncode}")
            return output, err
        except subprocess.TimeoutExpired:
            if proc:
                proc.kill()
            logging.error(f"Process timed out and was killed: {args}")
            return b"", b"Process timed out after 300 seconds"
        except Exception as e:
            logging.error(f"Failed to run subprocess: {e}", exc_info=True)
            return b"", str(e).encode()





