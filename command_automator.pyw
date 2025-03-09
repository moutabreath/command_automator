import ctypes
import json
import logging
import sys
from datetime import datetime

import PyQt6
import keyboard
from PyQt6.QtWidgets import QWidget, QPlainTextEdit, QSpacerItem, QComboBox, QPushButton, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QTabWidget, QSizePolicy, QFileDialog, QApplication
from PyQt6.QtGui import QIcon, QMovie
from PyQt6 import QtCore
from qtpy import QtWidgets, QtCore
from PyQt6.QtCore import Qt

from logic_handler import LogicHandler


from python_utils.pyqt.thread_runner import ThreadRunner
from python_utils.pyqt import pyqt_utils
from tabs.llm.llm_prompt_tab import LLMPromptTab    


class CommandAutomator(PyQt6.QtWidgets.QWidget):

    txt_box_result: QPlainTextEdit
    RUN_APP_KEY_SHORTCUT = 'alt + r'
    KILL_APP_KEY_SHORTCUT = 'alt + g'
    EXECUTE_SCRIPT_KEY_SHORTCUT = 'ctrl + alt + e'

    def __init__(self):
        super().__init__()
        self.logic_handler = LogicHandler()
        self.thread_runner = ThreadRunner()
        self.txt_box_selected_override = QLineEdit()
        my_app_id = 'tal.commandsAutomator.1'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

        self.action_list = QComboBox()

        self.txt_box_free_text = QPlainTextEdit()
        self.txt_box_flags = QLineEdit()        
        self.box_layout_additional = None
        self.box_layout_result = None
        self.txt_box_result = QPlainTextEdit()
        self.txt_box_description = QPlainTextEdit()


        self.sub_main_vertical_box_layout = None
        self.main_layout = None
        
        self.btn_cancel_exec = QPushButton('Cancel')
        self.spinner_layout = None
        self.window_alt = QtWidgets.QMainWindow()
        self.movie = QMovie('resources\\loader.gif')
        self.central_widget = QtWidgets.QWidget(self.window_alt)
        self.movie_label = QtWidgets.QLabel(self)

        self.setup_spinner()
        self.init_display()
        self.init_keyboard_shortcuts()
        
    def init_keyboard_shortcuts(self):
        keyboard.add_hotkey(CommandAutomator.EXECUTE_SCRIPT_KEY_SHORTCUT, self.execute_on_keypress)  # , args=('Hotkey', 'Detected'))
      

    def setup_spinner(self):
        self.central_widget.setObjectName("main-widget")
        self.movie_label.setGeometry(QtCore.QRect(25, 25, 200, 200))
        self.movie_label.setMinimumSize(QtCore.QSize(250, 250))
        self.movie_label.setMaximumSize(QtCore.QSize(250, 250))
        self.movie_label.setObjectName("lb1")
        self.movie_label.setMovie(self.movie)

    def init_display(self):
        pyqt_utils.make_dark_mode(self)
        self.setup_save_configuration_events()

        tab_widget = QTabWidget()

        script_exec_tab = QWidget()

        self.main_layout = QVBoxLayout()

        spacer_item = QSpacerItem(0, 0, QSizePolicy.Expanding)
        work_trees_layout = self.create_work_trees_elements(spacer_item)
        items = self.logic_handler.load_scripts()
        self.action_list.addItems(items)
        self.action_list.activated.connect(self.save_configuration)
        button_execute_script = QPushButton('Execute')
        button_execute_script.setToolTip(CommandAutomator.EXECUTE_SCRIPT_KEY_SHORTCUT)
        button_execute_script.clicked.connect(self.execute_script)
        horizontal_box_scripts_and_button = pyqt_utils.create_horizontal_box(self.action_list, button_execute_script,
                                                                             spacer_item)
        self.main_layout = pyqt_utils.add_blank_line(self.main_layout, work_trees_layout,
                                                         horizontal_box_scripts_and_button)
        seperator = pyqt_utils.create_horizontal_separator()
        self.main_layout.addWidget(seperator)
        label_description = QLabel("Script Description")
        self.txt_box_description = QPlainTextEdit()
        self.main_layout.addWidget(label_description)
        self.main_layout.addWidget(self.txt_box_description)
        label_free_text = QLabel('Command Text (Ony If Applicable)')
        label_result_text = QLabel('Command Result')
        label_flags = QLabel('Additional Arguments/Flags')
        free_text_and_result = QVBoxLayout()
        self.box_layout_additional = pyqt_utils.create_vertical_box(label_free_text, self.txt_box_free_text)
        self.box_layout_flags = pyqt_utils.create_vertical_box(label_flags, self.txt_box_flags)
        self.box_layout_result = pyqt_utils.create_vertical_box(label_result_text, self.txt_box_result)
        separator = pyqt_utils.create_horizontal_separator()
        free_text_and_result.addLayout(self.box_layout_additional)
        free_text_and_result.addLayout(self.box_layout_flags)
        free_text_and_result.addWidget(separator)
        free_text_and_result.addLayout(self.box_layout_result)

        self.spinner_layout = QVBoxLayout()
        self.btn_cancel_exec.clicked.connect(self.cancel_script_exec)
        self.spinner_layout.addWidget(self.movie_label)
        cancel_btn_layout = QHBoxLayout()
        cancel_btn_layout.addWidget(self.btn_cancel_exec)
        cancel_btn_layout.addItem(spacer_item)
        self.main_layout.addWidget(separator)
        self.main_layout.addLayout(free_text_and_result)
        self.spinner_layout.addLayout(cancel_btn_layout)

        # Set the layout for the code snippet tab
        script_exec_tab.setLayout(self.main_layout)

        # Add the code snippet tab to the tab widget
        tab_widget.addTab(script_exec_tab, "App and Scripts Runner")
        tab_widget.addTab(LLMPromptTab(), "LLM")

        # Add the tab widget to the main window
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(tab_widget)

        # Add event listener to drop-down list
        self.action_list.currentIndexChanged.connect(self.selectionchange)
        self.load_configuration()
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Commands Automator')
        self.setWindowIcon(QIcon('resources\\Commands_Automator.ico'))
        self.show()
        
    # def event(self, event):
    #     if event.type() == QEvent.FocusIn:
    #         self.init_keyboard_shortcuts(self)
    #     return super().event(event)

    def setup_save_configuration_events(self):
        self.txt_box_free_text.textChanged.connect(self.save_additional_text)
        self.txt_box_flags.textChanged.connect(self.save_additional_text)
        
    def cancel_script_exec(self):
        self.thread_runner.stop_command()

    def save_additional_text(self):
        self.save_configuration()


    def load_configuration(self):
        with open('configs\\commands-executor-config.json', 'r') as f:
            data = json.load(f)
    
        pyqt_utils.set_selected_value(data, self.action_list, "selected_script")
        if 'additional_text' in data and data['additional_text'] != "":
            self.txt_box_free_text.document().setPlainText(data["additional_text"])
        if 'flags' in data and data['flags'] != "":
            self.txt_box_flags.setText(data['flags'])


    def save_configuration(self):
        data = {
            "selected_script": self.action_list.currentText(),
            "additional_text": self.txt_box_free_text.toPlainText(),
            "flags": self.txt_box_flags.text()
        }
        with open("configs\\commands-executor-config.json", "w") as file:
            json.dump(data, file, indent=4)

    def execute_on_keypress(self):
        self.execute_script()

    def create_work_trees_elements(self,spacer_item):
        
        work_trees_layout = QVBoxLayout()
        seperator = pyqt_utils.create_horizontal_separator()

        button_kill_mono = QPushButton('Kill App')
        button_kill_mono.setToolTip(CommandAutomator.KILL_APP_KEY_SHORTCUT)
        # button_kill_mono.setStyleSheet("color: #fff; background-color: red; border-radius: 5px; padding: 5px;}")
        button_run_mono = QPushButton('Start app')
        button_run_mono.setToolTip(CommandAutomator.RUN_APP_KEY_SHORTCUT)

        horizontal_box_powerup_provision = QHBoxLayout()
        horizontal_box_powerup_provision.addItem(spacer_item)

        work_trees_layout.addWidget(seperator)
        work_trees_layout.addWidget(seperator)
        work_trees_layout.addLayout(horizontal_box_powerup_provision)
        work_trees_layout.addWidget(seperator)
        return work_trees_layout


    def selectionchange(self, i):
        script_list_name = self.action_list.currentText()
        script_file = self.logic_handler.get_name_to_scripts()[script_list_name]
        text = self.logic_handler.get_script_description(script_file)
        self.txt_box_description.document().setPlainText(text)

    def execute_script(self):
        logging.log(logging.DEBUG, f"script execution started")
        file_name = self.action_list.currentText()
        script_path = self.logic_handler.get_name_to_scripts()[file_name]
        if script_path is None:
            script_path = file_name
        args = self.logic_handler.get_arguments_for_script(script_path, self.txt_box_free_text.toPlainText(), self.txt_box_flags.text())
        if args is None:
            self.txt_box_result.document().setPlainText("Missing argument. Please fill the text box for Additional Text")
            return
        self.txt_box_result.document().setPlainText(f'Executing at {datetime.now()}\n{script_path}\nargs: {args}')
        new_venv = self.logic_handler.get_updated_venv(args[0])
        self.thread_runner.run_command(args, self.stop_animation, self.start_animation, new_venv)

    def start_animation(self, n):
        pyqt_utils.start_animation_in_movie(self.main_layout, self.spinner_layout, self.btn_cancel_exec,
                                            self.movie_label, self.movie)

    def stop_animation(self, n):
        pyqt_utils.stop_animation_in_movie(self.main_layout, self.spinner_layout, self.btn_cancel_exec, 
                                           self.movie_label, self.movie)
        result,err = self.thread_runner.get_run_result()
        string_result = self.logic_handler.get_string_from_thread_result(result, err)
        if len(string_result) != 0:
            self.txt_box_result.document().setPlainText(string_result)


    # def kill_app(self):
    #     running_version = self.combo_box_mono_options.currentText()
    #     kill_command = f'wmic Path win32_process Where "CommandLine like \'%{running_version}\\Qrelease%\'" Call Terminate'
    #     self.logic_handler.run_windows_command(kill_command)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CommandAutomator()
    app.gif_window = ex
    sys.exit(app.exec_())
