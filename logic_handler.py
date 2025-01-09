import glob
import json
import ntpath
import os
import subprocess
from collections import defaultdict
from pathlib import Path

import chardet
from python_utils.logger import Logger


class LogicHandler:
    def __init__(self):
        self.names_to_scripts = {}
        self.scripts_attributes = {}
        Logger.init_logger()
        self.load_scripts_config()
        self.mono_list = []
        self.mono_versions = defaultdict()

    def load_scripts_config(self):
        try:
            f = open('configs\\scripts_config.json')
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

        files = glob.glob(os.getcwd() + '\\actionables/**/*.py', recursive=True)
        files2 = glob.glob(os.getcwd() + '\\actionables/**/*.sh', recursive=True)
        files3 = glob.glob(os.getcwd() + '\\actionables/**/*.cmd', recursive=True)
        files4 = glob.glob(os.getcwd() + '\\actionables/**/*.exe', recursive=True)
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

    def get_arguments_for_script(self, script_path, additional_text):
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
        if self.should_use_free_text(script_name):
            if additional_text == "" or additional_text is None:
                return None            
            free_text_args = additional_text.split(" ")
            split_arr = list(filter(None, ' '.join(free_text_args).split()))
            args.extend(split_arr)
        other_script_name_as_input = self.get_other_script_name_as_input(script_name)
        if other_script_name_as_input is not None:
            files = glob.glob(os.getcwd() + f'\\cleaners/**/{other_script_name_as_input}', recursive=True)
            f_drive_cleaner_path = files[0]
            args.append(f_drive_cleaner_path)
        Logger.print_log("[logic_handler.get_arguments_for_script] running " + str(args))
        return args

    @staticmethod
    def get_updated_venv(arg):
        if not ('python' in arg):
            return
        new_venv = os.environ
        python_env = new_venv.get("PYTHONPATH", "")
        Logger.print_log("[logic_handler.get_updated_venv] PYTHONPATH before " + new_venv.get("PYTHONPATH", ""))
        if (len(python_env) != 0) and (python_env[-1] != ';'):
            new_venv["PYTHONPATH"] = new_venv.get("PYTHONPATH", "") + ";"
        if not (os.getcwd() in python_env):
            new_venv["PYTHONPATH"] = new_venv.get("PYTHONPATH", "") + os.getcwd() + ";"
        Logger.print_log("[logic_handler.get_updated_venv] PYTHONPATH after " + new_venv.get("PYTHONPATH", ""))
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

    @staticmethod
    def get_string_from_thread_result(result, err):
        str_result = ""
        Logger.print_log("[logic.handler.get_string_from_thread_result] entered.")
        if isinstance(result, (bytes, bytearray)):
            encoding_stats = chardet.detect(result)
            encoding = encoding_stats['encoding']
            if encoding is not None:
                str_result = result.decode(encoding)
                Logger.print_log(f"[logic.handler.get_string_from_thread_result] str_result is {str_result}.")
            else:
                Logger.print_log("[logic.handler.get_string_from_thread_result] encoding is None")
                str_result = ""
            if err is not None:
                if isinstance(err, str):
                    Logger.print_error_message(str(err), err)
                    str_result = str_result + " " + err

        if len(str_result) == 0:
            str_result = "Execution Done"
        return str_result

    def should_add_one_v(self, script_name):
        return self.scripts_attributes[script_name]['one_v_required']

    def should_add_mono(self, script_name):
        return self.scripts_attributes[script_name]['monolith_required']

    def is_for_qa(self, script_name):
        if 'for_qa' in self.scripts_attributes[script_name]:
            return self.scripts_attributes[script_name]['for_qa']
        return False

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

    @staticmethod
    def get_bin_folder_parent_path(version_path: Path):
        if os.path.isfile(version_path.joinpath("qrelease", "Bin", "starter.exe")):
            return version_path.joinpath("qrelease")
        elif os.path.isfile(version_path.joinpath("Bin", "starter.exe")):
            return version_path

    def get_run_command_text(self, running_version_text, is_provision_10, is_powerup_checked, override_file):
        running_version = self.get_version_path(running_version_text)
        running_version = LogicHandler.get_bin_folder_parent_path(running_version)
        version = "PROVision"
        if is_provision_10:
            version = 'PROVision10'
        powerup = ""
        if is_powerup_checked:
            powerup = '-powerup'
        override = ""
        if override_file != "":
            override = f' -J-Dwf.override.filename="{os.path.abspath(override_file)}"'
        arguments = f'Bin\\Starter.exe -S-platform {version} -login {powerup} -no_second_screen -frame -useHD -newLnF' \
                    f' -ignore16bits -S-debug {override}'

        run_version_command = f'{running_version}\\{arguments}'
        return run_version_command
