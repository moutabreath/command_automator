import sys
import glob
import json
import logging
import os
import subprocess

import chardet

from logger import Logger

class CommandsAutomatorService:
    def __init__(self):
        self.names_to_scripts = {}
        self.scripts_attributes = {}
        Logger.init_logger()
        self.load_scripts_config()



    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.getcwd(), relative_path)

    def load_scripts_config(self):
        try:
            f = open('config\\scripts_config.json')
        except IOError:
            return
        data = json.load(f)
        scripts_config = data['scripts']
        for script in scripts_config:
            script_name, tag_name, script_desc = script['script_name'], script['short_description'], script['detailed_Description']
            if script_name == "" or tag_name == "" or script_desc == "":
                continue
            self.scripts_attributes[script_name] = script

    def get_name_to_scripts(self):
        return self.names_to_scripts

    def load_scripts(self):
        executables = []
        current_dir = os.getcwd()
        logging.debug(current_dir)
        scripts_dir = self.resource_path('user_scripts')
        logging.debug(scripts_dir)
        files = glob.glob(f'{scripts_dir}/**/*.py', recursive=True)
        files2 = glob.glob(f'{scripts_dir}/**/*.sh', recursive=True)
        files3 = glob.glob(f'{scripts_dir}/**/*.cmd', recursive=True)
        files4 = glob.glob(f'{scripts_dir}/**/*.exe', recursive=True)
        files.extend(files2)
        files.extend(files3)
        files.extend(files4)
        for file in files:
            file_name = self.get_name_from_script(file)
            if file_name is None:
                file_name = file
            self.names_to_scripts[file_name] = file
            executables.append(file_name)
        executables = sorted(executables, key=lambda x: x.lower())

        return executables

    def get_script_attribute(self, file, attribute):
        script_name = os.path.basename(file)
        if script_name in self.scripts_attributes:
            return self.scripts_attributes[script_name][attribute]
        return ""

    def get_name_from_script(self, file):
        return self.get_script_attribute(file, 'short_description')

    def get_script_description(self, file):
        return self.get_script_attribute(file, 'detailed_Description')

    def get_arguments_for_script(self, script_path, additional_text, flags):
        script_name = os.path.basename(script_path)
        args = []
        if script_name.endswith('py'):
            args.append('python')
        if script_name.endswith('sh'):
            args.append('bash')
        if script_name.endswith('cmd'):
            args.append('cmd')
            args.append('/c')            
        args.append(script_path)   
        args.append(additional_text)    
        if self.should_use_free_text(script_name):
            if additional_text == "" or additional_text is None:
                return None            
            free_text_args = flags.split(" ")
            split_arr = list(filter(None, ' '.join(free_text_args).split()))
            args.extend(split_arr)
        other_script_name_as_input = self.get_other_script_name_as_input(script_name)
        if other_script_name_as_input is not None:
            files = glob.glob(os.getcwd() + f'\\cleaners/**/{other_script_name_as_input}', recursive=True)
            f_drive_cleaner_path = files[0]
            args.append(f_drive_cleaner_path)
        logging.log(logging.DEBUG, "running " + str(args))
        return args

    @staticmethod
    def get_updated_venv(arg):
        if not ('python' in arg):
            return
        new_venv = os.environ
        python_env = new_venv.get("PYTHONPATH", "")
        logging.log(logging.DEBUG, "PYTHONPATH before " + new_venv.get("PYTHONPATH", ""))
        if (len(python_env) != 0) and (python_env[-1] != ';'):
            new_venv["PYTHONPATH"] = new_venv.get("PYTHONPATH", "") + ";"
        if not (os.getcwd() in python_env):
            new_venv["PYTHONPATH"] = new_venv.get("PYTHONPATH", "") + os.getcwd() + ";"
        logging.log(logging.DEBUG, "PYTHONPATH after " + new_venv.get("PYTHONPATH", ""))
        return new_venv

    @staticmethod
    def run_app(run_version_command: str):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(run_version_command, startupinfo=si)

    @staticmethod
    def run_windows_command(command_to_run):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(command_to_run)

    def get_string_from_thread_result(self, result, err):
        str_result = ""
        logging.log(logging.DEBUG, "entered.")
        if isinstance(result, (bytes, bytearray)):
            encoding_stats = chardet.detect(result)
            encoding = encoding_stats['encoding']
            if encoding is not None:
                str_result = result.decode(encoding)
                logging.log(logging.DEBUG, f"str_result is {str_result}.")
            else:
                logging.log(logging.DEBUG, "encoding is None")
                str_result = ""
            if err is not None:
                if isinstance(err, str):
                    logging.log(logging.ERROR, str(err), err)
                    str_result = str_result + " " + err

        if len(str_result) == 0:
            str_result = "Execution Done"
        return str_result


    def should_use_free_text(self, script_name):
        return self.scripts_attributes[script_name]['free_text_required']
    
    def get_other_script_name_as_input(self, script_name):
        if 'other_script_name_as_input' in self.scripts_attributes[script_name]:
            return self.scripts_attributes[script_name]['other_script_name_as_input']
        else:
            return None


    @staticmethod
    def is_dir_empty(dir_path):
        return not next(os.scandir(dir_path), None)
    

    def execute_script(self, script_name, additional_text, flags):
        script_path = self.get_name_to_scripts().get(script_name, script_name)
        args = self.get_arguments_for_script(script_path, additional_text, flags)
        if args is None:
            return {"error": "Missing argument. Please fill the text box for Additional Text"}
        new_venv = self.get_updated_venv(args[0])
        output, err  = self.run_internal(args, new_venv)
        return self.get_string_from_thread_result(output, err)

    def run_internal(self, args, venv):
        logging.log(logging.DEBUG, "entered")
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=venv)
        logging.log(logging.DEBUG, "popen done")
        output, err = self.proc.communicate()
        logging.log(logging.DEBUG, "proc communicate done")
        return output, err
        
    

   
