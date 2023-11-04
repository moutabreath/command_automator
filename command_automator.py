import ctypes
import json
import sys
import threading
from datetime import datetime
import keyboard
from PyQt6.QtGui import QIcon, QMovie
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QComboBox, QPushButton, QPlainTextEdit, QLabel, \
    QVBoxLayout, QHBoxLayout, QFrame, QLineEdit, QFileDialog, QSizePolicy
from PyQt6.QtCore import Qt, QSize

from logger import Logger
from logic_handler import LogicHandler
from thread_runner import ThreadRunner


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

        self.sub_main_vertical_box_layout = None
        self.btn_cancel_exec = QPushButton('Cancel')
        self.spinner_and_cancel_v_layout = None
        self.window_alt = QMainWindow()
        self.movie = QMovie('loader.gif')
        self.central_widget = QWidget(self.window_alt)
        self.movie_label = QLabel(self)

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
        self.make_dark_mode()
        self.txt_box_free_text.textEdited.connect(self.save_additional_text)

        self.sub_main_vertical_box_layout = QVBoxLayout()

        items = self.logic_handler.load_scripts()
        self.action_list.addItems(items)
        self.action_list.activated.connect(self.save_configuration)

        button_execute_script = QPushButton('Execute')
        button_execute_script.clicked.connect(self.execute_script)

        spacer_item = None  # The code for creating a spacer item in PyQt6 is different.

        horizontal_box_scripts_and_button = self.create_horizontal_box(self.action_list, button_execute_script,
                                                                       spacer_item)
        self.sub_main_vertical_box_layout = self.add_blank_line(self.sub_main_vertical_box_layout, None,
                                                                horizontal_box_scripts_and_button)
        separator = self.create_horizontal_separator()
        self.sub_main_vertical_box_layout.addWidget(separator)
        label_description = QLabel("Script Description")
        self.txt_box_description = QPlainTextEdit()
        self.sub_main_vertical_box_layout.addWidget(label_description)
        self.sub_main_vertical_box_layout.addWidget(self.txt_box_description)

        label_free_text = QLabel('Command Text (Ony If Applicable)')
        label_result_text = QLabel('Command Result')
        free_text_and_result = QVBoxLayout()
        self.box_layout_additional = self.create_vertical_box(label_free_text, self.txt_box_free_text)
        self.box_layout_result = self.create_vertical_box(label_result_text, self.txt_box_result)
        separator = self.create_horizontal_separator()
        free_text_and_result.addLayout(self.box_layout_additional)
        free_text_and_result.addWidget(separator)
        free_text_and_result.addLayout(self.box_layout_result)

        self.spinner_and_cancel_v_layout = QVBoxLayout()
        self.btn_cancel_exec.clicked.connect(self.cancel_script_exec)
        self.spinner_and_cancel_v_layout.addWidget(self.movie_label)
        cancel_btn_layout = QHBoxLayout()
        cancel_btn_layout.addWidget(self.btn_cancel_exec)
        cancel_btn_layout.addItem(spacer_item)
        self.spinner_and_cancel_v_layout.addLayout(cancel_btn_layout)
        # self.sub_main_vertical_box_layout.addLayout(self.spinner_and_cancel_v_layout)
        self.sub_main_vertical_box_layout.addWidget(separator)
        self.sub_main_vertical_box_layout.addLayout(free_text_and_result)

        # Create horizontal box layout for the entire window
        layout = QHBoxLayout()

        # Add vertical box layout to horizontal box layout
        layout.addLayout(self.sub_main_vertical_box_layout)

        # Set layout
        self.setLayout(layout)

        # Add event listener to drop-down list
        self.action_list.currentIndexChanged.connect(self.selectionchange)
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
        with open("commands-executor-config.json", "w") as write:
            json.dump(data, write)

    def load_configuration(self):
        try:
            with open('commands-executor-config.json') as f:
                data = json.load(f)
                self.set_selected_value(data, self.action_list, "selected_script")
                if 'additional_text' in data and data['additional_text'] != "":
                    self.txt_box_free_text.setText(data["additional_text"])
        except IOError:
            return

    @staticmethod
    def set_selected_value(data, combo_box, attribute):
        if data[attribute] != "":
            index = combo_box.findText(data[attribute])
            if index != -1:
                combo_box.setCurrentText(data[attribute])

    def start_animation_in_movie(self):
        self.sub_main_vertical_box_layout.addLayout(self.spinner_and_cancel_v_layout)
        self.btn_cancel_exec.show()
        self.movie_label.show()
        self.movie.start()

    def stop_animation_in_movie(self):
        self.movie.stop()
        self.btn_cancel_exec.hide()
        self.movie_label.hide()
        self.sub_main_vertical_box_layout.removeItem(self.spinner_and_cancel_v_layout)

    def execute_on_keypress(self):
        self.execute_script()

    def make_dark_mode(self):
        # Set dark mode style
        self.setStyleSheet("""QWidget { color: #333; background-color: #222; }
        QLabel { color: #fff; border: 1px; border-radius: 5px; padding: 5px; } 
        QCheckBox { color: #fff; border: 1px; border-radius: 5px; padding: 5px; } 
        QPushButton { color: #fff; background-color: green; border-radius: 5px; padding: 5px;} 
        QComboBox {color: #fff; background-color: #222; border: 2px solid green} 
        QComboBox:items{ color: #fff; border: 2px solid green }
        QListView{ color:  #fff; }
        QLineEdit {color: #fff; border: 2px solid green } 
        QPlainTextEdit {color: #fff; border: 2px solid green}  """)

    @staticmethod
    def add_blank_line(vertical_box_layout, layout_above_separator, layout_below_separator):
        separator = CommandAutomator.create_horizontal_separator()
        if layout_above_separator is not None:
            vertical_box_layout.addLayout(layout_above_separator)
        vertical_box_layout.addWidget(separator)
        if layout_below_separator is not None:
            vertical_box_layout.addLayout(layout_below_separator)
        return vertical_box_layout

    @staticmethod
    def create_horizontal_separator():
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        separator.setLineWidth(3)
        return separator

    @staticmethod
    def create_vertical_separator():
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        separator.setLineWidth(3)
        return separator

    @staticmethod
    def create_horizontal_box(widget1, widget2, spacer_item=None):
        horizontal_box = QHBoxLayout()
        horizontal_box.addWidget(widget1)
        if spacer_item is not None:
            horizontal_box.addItem(spacer_item)
        horizontal_box.addWidget(widget2)
        return horizontal_box

    @staticmethod
    def create_vertical_box(widget1, widget2):
        vertical_box = QVBoxLayout()
        vertical_box.addWidget(widget1)
        vertical_box.addWidget(widget2)
        return vertical_box

    def selectionchange(self, i):
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
