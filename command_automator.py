import ctypes
import json
import sys
import threading
from datetime import datetime

import PyQt6
import keyboard
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QMovie
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QComboBox, QPushButton, QPlainTextEdit, QLabel, \
    QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog
from qtpy import QtWidgets, QtCore
from python_utils.logger import Logger
from logic_handler import LogicHandler
from python_utils.pyqt import pyqt_utils
from python_utils.pyqt.thread_runner import ThreadRunner


class CommandAutomator(QWidget):
    txt_box_result: QPlainTextEdit

    def __init__(self):
        super().__init__()
        self.logic_handler = LogicHandler()
        self.thread_runner = ThreadRunner()
        self.txt_box_selected_override = QLineEdit()
        self.setWindowIcon(QIcon('CommandsAutomator.png'))
        my_app_id = 'tal.CommandsAutomator.1'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

        self.action_list = QComboBox()

        self.txt_box_free_text = QLineEdit()
        self.box_layout_additional = None
        self.box_layout_result = None
        self.txt_box_result = QPlainTextEdit()
        self.txt_box_description = QPlainTextEdit()

        self.code_tab_layout = None
        self.btn_cancel_exec = QPushButton('Cancel')
        self.spinner_and_cancel_v_layout = None
        self.window_alt = QtWidgets.QMainWindow()
        self.movie = QMovie('loader.gif')
        self.central_widget = QtWidgets.QWidget(self.window_alt)
        self.movie_label = QtWidgets.QLabel(self)

        self.setup_spinner()
        self.init_display()

        keyboard.add_hotkey('ctrl + shift + e', self.execute_on_keypress)  # , args=('Hotkey', 'Detected')

    def setup_spinner(self):
        self.central_widget.setObjectName("main-widget")
        self.movie_label.setGeometry(25, 25, 200, 200)
        self.movie_label.setMinimumSize(QSize(250, 250))
        self.movie_label.setMaximumSize(QSize(250, 250))
        self.movie_label.setObjectName("lb1")
        self.movie_label.setMovie(self.movie)

    def init_display(self):
        pyqt_utils.make_dark_mode(self)

        # Create a tab widget
        tab_widget = PyQt6.QtWidgets.QTabWidget()

        # Create the tab for the code snippet
        code_tab = PyQt6.QtWidgets.QWidget()

        self.txt_box_free_text.textEdited.connect(self.save_additional_text)

        self.code_tab_layout = QVBoxLayout()

        items = self.logic_handler.load_scripts()
        self.action_list.addItems(items)
        self.action_list.activated.connect(self.save_configuration)

        button_execute_script = QPushButton('Execute')
        button_execute_script.clicked.connect(self.execute_script)

        spacer_item = None  # The code for creating a spacer item in PyQt6 is different.

        horizontal_box_scripts_and_button = pyqt_utils.create_horizontal_box(self.action_list, button_execute_script,
                                                                             spacer_item)
        self.code_tab_layout = pyqt_utils.add_blank_line(self.code_tab_layout, None,
                                                         horizontal_box_scripts_and_button)
        separator = pyqt_utils.create_horizontal_separator()
        self.code_tab_layout.addWidget(separator)
        label_description = QLabel("Script Description")
        self.txt_box_description = QPlainTextEdit()
        self.code_tab_layout.addWidget(label_description)
        self.code_tab_layout.addWidget(self.txt_box_description)

        label_free_text = QLabel('Command Text (Ony If Applicable)')
        label_result_text = QLabel('Command Result')
        free_text_and_result = QVBoxLayout()
        self.box_layout_additional = pyqt_utils.create_vertical_box(label_free_text, self.txt_box_free_text)
        self.box_layout_result = pyqt_utils.create_vertical_box(label_result_text, self.txt_box_result)
        separator = pyqt_utils.create_horizontal_separator()
        free_text_and_result.addLayout(self.box_layout_additional)
        free_text_and_result.addWidget(separator)
        free_text_and_result.addLayout(self.box_layout_result)

        self.spinner_and_cancel_v_layout = QtWidgets.QVBoxLayout()
        self.btn_cancel_exec.clicked.connect(self.cancel_script_exec)
        self.spinner_and_cancel_v_layout.addWidget(self.movie_label)
        cancel_btn_layout = PyQt6.QtWidgets.QHBoxLayout()
        cancel_btn_layout.addWidget(self.btn_cancel_exec)
        cancel_btn_layout.addItem(spacer_item)
        self.code_tab_layout.addWidget(separator)
        self.code_tab_layout.addLayout(free_text_and_result)
        self.spinner_and_cancel_v_layout.addLayout(cancel_btn_layout)

        code_tab.setLayout(self.code_tab_layout)
        tab_widget.addTab(code_tab, "App and Scripts Runner")
        # tab_widget.addTab(self.tests_tab, "Tests runner")

        # Add the tab widget to the main window
        self.setLayout(PyQt6.QtWidgets.QHBoxLayout())
        self.layout().addWidget(tab_widget)

        # Add event listener to drop-down list
        self.action_list.currentIndexChanged.connect(self.selection_change)
        self.load_configuration()

        # self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Commands Automator')
        self.show()

    def cancel_script_exec(self):
        self.thread_runner.stop_command()

    def get_file(self):
        selected_file_name, _ = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "XML files (*.xml)")
        self.txt_box_selected_override.setText(selected_file_name)

    def save_additional_text(self, text):
        self.save_configuration()

    def save_configuration(self):
        data = {
            "selected_script": self.action_list.currentText(),
            "additional_text": self.txt_box_free_text.text()
        }
        with open("config\\commands-executor-config.json", "w") as file:
            json.dump(data, file, indent=4)

    def load_configuration(self):
        try:
            with open('config\\commands-executor-config.json') as f:
                data = json.load(f)
                pyqt_utils.set_selected_value(data, self.action_list, "selected_script")
                if 'additional_text' in data and data['additional_text'] != "":
                    self.txt_box_free_text.setText(data["additional_text"])
        except IOError:
            return

    def start_animation_in_movie(self):
        self.code_tab_layout.addLayout(self.spinner_and_cancel_v_layout)
        self.btn_cancel_exec.show()
        self.movie_label.show()
        self.movie.start()

    def stop_animation_in_movie(self):
        self.movie.stop()
        self.btn_cancel_exec.hide()
        self.movie_label.hide()
        self.code_tab_layout.removeItem(self.spinner_and_cancel_v_layout)

    def execute_on_keypress(self):
        self.execute_script()

    def selection_change(self, i):
        script_list_name = self.action_list.currentText()
        script_file = self.logic_handler.get_name_to_scripts()[script_list_name]
        text = self.logic_handler.get_script_description(script_file)
        self.txt_box_description.document().setPlainText(text)

    def execute_script(self):
        Logger.print_log(f"script execution started")
        file_name = self.action_list.currentText()
        script_path = self.logic_handler.get_name_to_scripts()[file_name]
        if script_path is None:
            script_path = file_name
        args = self.logic_handler.get_arguments_for_script(script_path, self.txt_box_free_text.text())
        if args is None:
            self.txt_box_result.document().setPlainText(
                "Missing argument. Please fill the text box for Additional Text")
            return
        self.txt_box_result.document().setPlainText(f'Executing at {datetime.now()}\n{script_path}\nargs: {args}')
        new_venv = self.logic_handler.get_updated_venv(args[0])
        try:
            self.thread_runner.run_command(args, self.stop_animation, self.start_animation, new_venv)
        except ex:
            Logger.print_error_message("Error running script", ex)

    def start_animation(self, n):
        self.start_animation_in_movie()

    def stop_animation(self, n):
        self.movie.stop()
        self.btn_cancel_exec.hide()
        self.movie_label.hide()
        result, err = self.thread_runner.get_run_result()
        string_result = self.logic_handler.get_string_from_thread_result(result, err)
        if len(string_result) != 0:
            self.txt_box_result.document().setPlainText(string_result)

    def kill_app(self):
        running_version = "dummy place holder"
        kill_command = f'wmic Path win32_process Where "CommandLine like \'%{running_version}\'" Call Terminate'
        self.logic_handler.run_windows_command(kill_command)

    def start_app_in_thread(self):
        run_version_command = 'dummy place holder'
        run_version_thread = threading.Thread(target=self.logic_handler.run_app, args=[str(run_version_command)])

        self.txt_box_result.document().setPlainText(
            "Starting app at " + str(datetime.now()) + " args:\n " + run_version_command)
        run_version_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CommandAutomator()
    app.gif_window = ex
    sys.exit(app.exec())
