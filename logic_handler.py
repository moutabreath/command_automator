import glob
import json
import os
import subprocess
from collections import defaultdict

import chardet

from logger import Logger


class LogicHandler:
    def __init__(self):
        self.names_to_scripts = {}
        self.scripts_attributes = {}
        Logger.init_logger()
        self.load_scripts_config()

    def load_scripts_config(self):
        try:
            f = open('scripts_config.json')
        except IOError:
            return
        data = json.load(f)
        scripts_config = data['scripts']
        for script in scripts_config:
            script_name, tag_name, script_desc, free_text = script['script_name'], script['short_description'], script[
                'detailed_Description'], script['free_text_required']
            if script_name == "" or tag_name == "" or script_desc == "" or free_text == "":
                continue
            self.scripts_attributes[script_name] = script

    def get_name_to_scripts(self):
        return self.names_to_scripts

    def load_scripts(self):
        executables = []
        files = glob.glob(os.getcwd() + '\\actionables/**/*.py', recursive=True)
        files2 = glob.glob(os.getcwd() + '\\actionables/**/*.sh', recursive=True)
        files3 = glob.glob(os.getcwd() + '\\actionables/**/*.cmd', recursive=True)
        files.extend(files2)
        files.extend(files3)
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

        if script_name.endswith('cmd'):
            args.append('cmd')
            args.append('/c')
        if script_name.endswith('py'):
            args.append('python')
        if script_name.endswith('sh'):
            args.append('bash')
        args.append(script_path)
        if self.should_use_free_text(script_name):
            if additional_text == "" or additional_text is None:
                return None
            args.append(additional_text)
        Logger.print_log("[logic_handler.get_arguments_for_script] running " + str(args))
        return args

    @staticmethod
    def get_updated_venv(arg):
        if arg != 'python':
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

    def should_use_free_text(self, script_name):
        return self.scripts_attributes[script_name]['free_text_required']
