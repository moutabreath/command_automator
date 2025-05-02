import json
import logging
import os

import keyboard
from qtpy import QtWidgets
from PyQt6.QtWidgets import QMainWindow, QWidget, QTextEdit, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QCheckBox
from PyQt6.QtCore import Qt, QRect, QSize, QThreadPool
from PyQt6.QtGui import QMovie
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QFileDialog

from python_utils.pyqt.runnable_worker import Signals
from python_utils.pyqt.text_editor import TextEditor
from tabs.llm.llm_logic_handler import LLMLogicHanlder
from tabs.llm.ui_threads.gemini_stream_worker import GeminiStreamWorker
from tabs.llm.ui_threads.gemini_ui_worker import GeminiUIWorker


class LLMPromptTab(QtWidgets.QWidget):
    MAIN_FILE_PATH = 'main_file_path' 
    SECONDARY_FILE_PATH = 'secondary_file_dir'
    APPLICANT_NAME_TAG = 'applicant_name'
    applicant_name_value = ''
    SEND_QUERY_KEYBOARD_SHORTCUT = 'enter'
    OUTPUT_RESUME_DIR_PATH = "output_resume_path"
    SAVE_RESULTS_TO_FILE = "save_results_to_file"
  
    def __init__(self):
        super().__init__()
        # Consts
        self.lLLMLogicHanlder: LLMLogicHanlder = LLMLogicHanlder()
        self.CONFIG_FILE_PATH: str = f'{os.getcwd()}/{self.lLLMLogicHanlder.CURRENT_PATH}/llm-config.json'

        # UI threads
        self.signals: Signals = Signals()
        self.thread_pool = QThreadPool.globalInstance()
        self.gemini_ui_worker = None

        # self.worker: GeminiStreamWorker = GeminiStreamWorker("", self.lLLMLogicHanlder.gemini_agent)        
        # self.worker.chunk_signal.connect(self.update_text)
        # self.worker.finished_signal.connect(self.enable_button)
        

        # UI layout
        self.main_layout: QVBoxLayout = QVBoxLayout()

        self.txtBoxResponse: QTextEdit = QTextEdit()
        self.txtBoxResponse.setStyleSheet("color: white;")
        self.btn_query_llm: QPushButton = QPushButton('Send Query')
        self.btn_select_image = QPushButton('+')
        self.txtBoxQuery: TextEditor = TextEditor('Message LLM')

        self.txt_bx_main_file_input = QLineEdit()
        self.btn_select_main_file = QPushButton("Resume File")

        self.txt_bx_secondary_files_input = QLineEdit()        
        self.btn_select_secondary_dir = QPushButton("Job Description File")

        self.txt_bx_resume_output = QLineEdit()
        self.btn_select_ouput_location = QPushButton("Resume File Output Dir")

        self.btn_send_files_to_llm = QPushButton("Chat using files")
        self.chbx_save_to_files = QCheckBox("Save to Files")

        hBoxLayoutResponse = QHBoxLayout()
        
        self.txtBoxResponse.setReadOnly(True)
        hBoxLayoutResponse.addWidget(self.txtBoxResponse)      
        self.main_layout.addLayout(hBoxLayoutResponse)

        
        box_layout_button_and_query = QHBoxLayout()            
        
        self.btn_select_image.clicked.connect(self.select_image)
        self.btn_query_llm.clicked.connect(self.send_to_chat_gpt)
        box_layout_button_and_query.addWidget(self.txtBoxQuery)
        box_layout_button_and_query.addWidget(self.btn_query_llm)
        box_layout_button_and_query.addWidget(self.btn_select_image)  # Add the '+' button to the layout
        self.main_layout.addLayout(box_layout_button_and_query)
    
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)  # Set size for the image thumbnail
        self.image_label.setStyleSheet("background-color: #333; border: 1px solid #555;")
        self.image_label.setVisible(False)  # Hide initially until an image is selected

        # File inputs section        
        bxFiles = QHBoxLayout()

        self.btn_select_main_file.clicked.connect(self.get_resume)        
        self.btn_select_secondary_dir.clicked.connect(self.get_job_desc_dir)        
        self.btn_select_ouput_location.clicked.connect(self.get_output_location)
        self.btn_send_files_to_llm.clicked.connect(self.start_resume_building)        

        self.init_files_display(bxFiles)
        self.main_layout.addLayout(bxFiles)        
        button_layout = QHBoxLayout()

        boxShouldSave = QHBoxLayout()
        boxShouldSave.addWidget(self.chbx_save_to_files)
        button_layout.addLayout(boxShouldSave)

        button_layout.addWidget(self.btn_send_files_to_llm)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

        # modal window
        self.spinner_layout = QVBoxLayout()
        self.modal_window = QMainWindow()
        self.movie = QMovie('resources\\loader.gif')
        self.central_widget = QWidget(self.modal_window)
        self.movie_label = QLabel(self)
        self.spinner_layout.addWidget(self.movie_label)

        self.setup_spinner()
        # Configurations
        self.load_configuration()
        self.setup_save_configuration_events()
        self.init_keyboard_shortcuts()

    
    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            'Select Image', 
            '', 
            'Image Files (*.png *.jpg *.jpeg *.bmp *.gif)'
        )
        
        if file_path:
            # Display the selected image
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                self.image_label.width(), 
                self.image_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setVisible(True)
            
            # Store the file path for later use (like sending to LLM)
            self.selected_image_path = file_path


    def init_keyboard_shortcuts(self):
        self.shortcut = QShortcut(QKeySequence("Enter"), self)
        self.shortcut.activated.connect(self.send_to_chat_gpt)

    def setup_spinner(self):
        self.central_widget.setObjectName("main-widget")
        self.movie_label.setGeometry(QRect(25, 25, 200, 200))
        self.movie_label.setMinimumSize(QSize(250, 250))
        self.movie_label.setMaximumSize(QSize(250, 250))
        self.movie_label.setObjectName("lb1")
        self.movie_label.setMovie(self.movie)
    
    def key_pressed_event(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.send_to_chat_gpt()
        else:
            super().keyPressEvent(event)

 

    def init_files_display(self, vBoxFiles: QVBoxLayout):
        boxTxtBx = QVBoxLayout()
        boxTxtBx.addWidget(self.txt_bx_main_file_input)
        boxTxtBx.addWidget(self.txt_bx_secondary_files_input)
        boxTxtBx.addWidget(self.txt_bx_resume_output)

        vBoxFiles.addLayout(boxTxtBx)

        bxButtons = QVBoxLayout()
        bxButtons.addWidget(self.btn_select_main_file)
        bxButtons.addWidget(self.btn_select_secondary_dir)
        bxButtons.addWidget(self.btn_select_ouput_location)
        
        vBoxFiles.addLayout(bxButtons)


    def send_to_chat_gpt(self):
        text = self.txtBoxQuery.toPlainText()
        if (text == None or text == ''):
            return
        # self.worker = GeminiStreamWorker()
        # self.worker.chunk_signal.connect(self.update_text)
        # self.worker.finished_signal.connect(self.enable_button)

        self.worker = GeminiStreamWorker()
        self.worker.set_required(text, self.lLLMLogicHanlder.gemini_agent)
        self.worker.signals.received.connect(self.update_text)
        self.worker.signals.completed.connect(self.enable_button)

        self.worker.set_required(text, self.lLLMLogicHanlder.gemini_agent)    
        
        self.worker.prompt = text
        self.txtBoxResponse.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.txtBoxResponse.append(f"{self.txtBoxQuery.toPlainText()}\n\n")
        self.txtBoxQuery.setText("")
        self.txtBoxResponse.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.txtBoxQuery.setReadOnly(True)
        self.btn_query_llm.setEnabled(False)
        self.thread_pool.start(self.worker)

    def update_text(self, chunk):
        # Append the new text chunk to the text area
        logging.debug(f"update_text: {chunk}")
        self.txtBoxResponse.append(chunk)
    
    def enable_button(self):
        self.btn_query_llm.setEnabled(True)
        self.txtBoxQuery.setReadOnly(False)

    
    def get_resume(self):
        selected_file_name = QFileDialog.getOpenFileName(self, 'Open file',
                                                         self.lLLMLogicHanlder.RESUME_FILES_PATH_PREFIX, "Docx, PDF or txt files (*.docx *.pdf, *.txt)")
        self.txt_bx_main_file_input.setText(selected_file_name[0])

    def get_job_desc_dir(self):
        selected_file_name = QFileDialog.getOpenFileName(self, 'Open file',
                                                          self.lLLMLogicHanlder.RESUME_FILES_PATH_PREFIX, "txt files (*.txt)")
        self.txt_bx_secondary_files_input.setText(selected_file_name[0])

    def get_output_location(self):
        selected_dir = QFileDialog.getExistingDirectory(self, 'Select Directory',
                                                         self.lLLMLogicHanlder.OUTPUT_RESUME_PATH_PREFIX)
        self.txt_bx_resume_output.setText(selected_dir)

    def start_resume_building(self):
        resume_path = self.txt_bx_main_file_input.text()
        job_desc_path = self.txt_bx_secondary_files_input.text()      
        resume_output_path = self.txt_bx_resume_output.text()  
        try:
            self.gemini_ui_worker = GeminiUIWorker(1)
            self.gemini_ui_worker.llm_logic_handler = self.lLLMLogicHanlder
            self.gemini_ui_worker.signals.completed.connect(self.stop_animation)
            self.gemini_ui_worker.signals.started.connect(self.start_animation)
            self.gemini_ui_worker.input = [self.applicant_name_value, resume_path, job_desc_path, resume_output_path]
            self.gemini_ui_worker.save_results_to_files = self.chbx_save_to_files.isChecked()
            self.thread_pool.start(self.gemini_ui_worker)
        except IOError as e:
            logging.exception("run_command: error", e)
            self.stop_animation(1)
        except Exception as e:
            logging.exception("run_command: error", e)
            self.stop_animation(1)


    def start_animation(self, n):
        self.start_animation_in_movie(self.main_layout, self.spinner_layout,
                                            self.movie_label, self.movie)

    def stop_animation(self, n):
        self.stop_animation_in_movie(self.main_layout, self.spinner_layout, 
                                           self.movie_label, self.movie)

    
    def start_animation_in_movie(self, main_layout: QtWidgets.QVBoxLayout, spinner_layout: QVBoxLayout,
                             movie_label: QLabel, movie: QMovie):
        main_layout.addLayout(spinner_layout)
        movie_label.show()
        movie.start()


    def stop_animation_in_movie(self, main_layout: QtWidgets.QHBoxLayout, spinner_layout: QVBoxLayout,
                           movie_label: QLabel, movie: QMovie):
        movie.stop()
        movie_label.hide()        
        main_layout.removeItem(spinner_layout)
        if self.gemini_ui_worker.agent_response == "":
              self.txtBoxResponse.setText("Something went wrong")
              return
        self.update_response()
            
    def format_response_for_display(self, response_text: str):
        lines = response_text.split('\n')
        formatted_lines = ""
        
        for line in lines:
            line = line.strip()
            if "*" in line:
                formatted_lines+=f"<b>{line}</b><br>"
            else:
                formatted_lines+=f'{line}<br>'
        
        return formatted_lines

    # In your code where you update the text box:
    def update_response(self):
        response_text = self.gemini_ui_worker.agent_response
        formatted_html = self.format_response_for_display(response_text)
        self.txtBoxResponse.setHtml(formatted_html)

    # If you need to preserve existing text:
    def append_response(self):
        response_text = self.gemini_ui_worker.agent_response
        formatted_html = self.format_response_for_display(response_text)
        current_html = self.txtBoxResponse.toHtml()
        self.txtBoxResponse.setHtml(current_html + formatted_html)

    # save and load previous texts
    def setup_save_configuration_events(self):
        self.txt_bx_main_file_input.textChanged.connect(self.save_configuration)
        self.txt_bx_secondary_files_input.textChanged.connect(self.save_configuration)
        self.txt_bx_resume_output.textChanged.connect(self.save_configuration)
        self.chbx_save_to_files.stateChanged.connect(self.save_configuration)
  
    def load_configuration(self):
        try:
            if not os.path.exists(self.CONFIG_FILE_PATH):
                return
            f = open(self.CONFIG_FILE_PATH)
        except IOError:
            return

        data = json.load(f)
        if self.MAIN_FILE_PATH in data and data[self.MAIN_FILE_PATH] != "":
            self.txt_bx_main_file_input.setText(data[self.MAIN_FILE_PATH])
        if self.SECONDARY_FILE_PATH  in data and data[self.SECONDARY_FILE_PATH] != "":
            self.txt_bx_secondary_files_input.setText(data[self.SECONDARY_FILE_PATH])
        if self.APPLICANT_NAME_TAG  in data and data[self.APPLICANT_NAME_TAG] != "":
            self.applicant_name_value = data[self.APPLICANT_NAME_TAG]
        if self.OUTPUT_RESUME_DIR_PATH  in data and data[self.OUTPUT_RESUME_DIR_PATH] != "":
             self.txt_bx_resume_output.setText(data[self.OUTPUT_RESUME_DIR_PATH])
        if self.SAVE_RESULTS_TO_FILE in data and data[self.SAVE_RESULTS_TO_FILE] != "":
             self.chbx_save_to_files.setChecked(data[self.SAVE_RESULTS_TO_FILE])
        try:
            f.close()
        except IOError:
            return


    def save_configuration(self):
        data = {
            self.MAIN_FILE_PATH: self.txt_bx_main_file_input.text(),
            self.SECONDARY_FILE_PATH: self.txt_bx_secondary_files_input.text(),
            self.APPLICANT_NAME_TAG: self.applicant_name_value,
            self.OUTPUT_RESUME_DIR_PATH: self.txt_bx_resume_output.text(),
            self.SAVE_RESULTS_TO_FILE: self.chbx_save_to_files.isChecked()
        }
        with open(self.CONFIG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)