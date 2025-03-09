import json
import logging
import os
from qtpy import QtWidgets
from PyQt6.QtWidgets import QTextEdit, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
from PyQt6.QtCore import Qt 
from PyQt6.QtCore import QThreadPool
from PyQt6.QtGui import QMovie

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
  
    def __init__(self):
        super().__init__()
        # Consts
        self.lLLMLogicHanlder = LLMLogicHanlder()
        self.CONFIG_FILE_PATH = f'{os.getcwd()}/{self.lLLMLogicHanlder.CURRENT_PATH}/llm-config.json'

        # UI threads
        self.signals = Signals()
        self.thread_pool = QThreadPool.globalInstance()
        self.gemini_ui_worker = None

        # modal window
        self.modal_layout = None
        self.modal_window = QtWidgets.QMainWindow()
        self.movie = QMovie('resources\\loader.gif')
        self.central_widget = QtWidgets.QWidget(self.modal_window)
        self.movie_label = QtWidgets.QLabel(self)


        # UI layout
        self.main_layout = QVBoxLayout()

        self.txtBoxResponse = QTextEdit()
        self.btn_query_llm = QPushButton('Send Query')
        self.txtBoxQuery = TextEditor('Message LLM')

        self.txt_bx_main_file_input = QLineEdit()
        self.btn_select_main_file = QPushButton("Select Resume File")

        self.txt_bx_secondary_files_input = QLineEdit()
        self.btn_select_seconadary_dir = QPushButton("Job files dir")
        self.btn_send_files_to_llm = QPushButton("Chat using files")
        
        hBoxLayoutResponse = QHBoxLayout()
        
        self.txtBoxResponse.setReadOnly(True)
        self.txtBoxResponse.setStyleSheet("color: white;")
        hBoxLayoutResponse.addWidget(self.txtBoxResponse)      
        self.main_layout.addLayout(hBoxLayoutResponse)

        hBoxLayoutButtonAndQuery = QHBoxLayout()            
        
        self.btn_query_llm.clicked.connect(self.send_to_chat_gpt)
        
        self.txtBoxQuery.setStyleSheet("color: white;")
        hBoxLayoutButtonAndQuery.addWidget(self.txtBoxQuery)
        hBoxLayoutButtonAndQuery.addWidget(self.btn_query_llm)        
        self.main_layout.addLayout(hBoxLayoutButtonAndQuery)    
    

        # File inputs section        
        bxFiles = QHBoxLayout()

        self.btn_select_main_file.clicked.connect(self.get_resume)        
        self.btn_select_seconadary_dir.clicked.connect(self.get_job_desc_dir)        
        self.btn_send_files_to_llm.clicked.connect(self.start_resume_building)        

        self.init_files_display(bxFiles)
        self.main_layout.addLayout(bxFiles)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_send_files_to_llm)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

        # Configurations
        self.load_configuration()
        self.setup_save_configuration_events()

 

    def init_files_display(self, vBoxFiles: QVBoxLayout):
        boxTxtBx = QVBoxLayout()

        boxTxtBx.addWidget(self.txt_bx_main_file_input)
        boxTxtBx.addWidget(self.txt_bx_secondary_files_input)

        vBoxFiles.addLayout(boxTxtBx)

        bxButtons = QVBoxLayout()
        bxButtons.addWidget(self.btn_select_main_file)
        bxButtons.addWidget(self.btn_select_seconadary_dir)
        
        vBoxFiles.addLayout(bxButtons)


    def send_to_chat_gpt(self):
        text = self.txtBoxQuery.toPlainText()
        
        self.worker = GeminiStreamWorker(text, self.lLLMLogicHanlder.gemini_agent)        
        self.worker.chunk_signal.connect(self.update_text)        
        self.worker.start()

    def update_text(self, chunk):
        # Append the new text chunk to the text area
        self.txtBoxResponse.insertPlainText(chunk)

    
    def get_resume(self):
        selected_file_name = QFileDialog.getOpenFileName(self, 'Open file',
                                                         self.lLLMLogicHanlder.RESUME_FILES_PATH_PREFIX, "Docx, PDF or txt files (*.docx *.pdf, *.txt)")
        self.txt_bx_main_file_input.setText(selected_file_name[0])

    def get_job_desc_dir(self):
        # initial_dir = os.getcwd() + "/tabs/llm/jobs_descriptions"
        # selected_dir = QFileDialog.getExistingDirectory(self, 'Select Directory', initial_dir)
        selected_file_name = QFileDialog.getOpenFileName(self, 'Open file',
                                                          self.lLLMLogicHanlder.RESUME_FILES_PATH_PREFIX, "txt files (*.txt)")
        self.txt_bx_secondary_files_input.setText(selected_file_name[0])

    def start_resume_building(self):
        resume_path = self.txt_bx_main_file_input.text()
        job_desc_path = self.txt_bx_secondary_files_input.text()
        response = self.lLLMLogicHanlder.start_resume_building(self.applicant_name_value, resume_path, job_desc_path)
        self.txtBoxResponse.setText(response)


    def run_command(self, process_input):
        try:
            self.gemini_ui_worker = GeminiUIWorker(1)
            self.gemini_ui_worker.signals.completed.connect(self.start_animation)
            self.gemini_ui_worker.signals.started.connect(self.stop_animation)
            self.gemini_ui_worker.prompt = process_input
            self.thread_pool.start(self.gemini_ui_worker)
        except IOError as e:
            logging.log(logging.ERROR, "run_command: error", e)

    def start_animation(self, n):
        self.start_animation_in_movie(self.main_layout, self.modal_layout,
                                            self.movie_label, self.movie)

    def stop_animation(self, n):
        self.stop_animation_in_movie(self.main_layout, self.modal_layout, 
                                           self.movie_label, self.movie)

    
    def start_animation_in_movie(main_layout: QtWidgets.QVBoxLayout, spinner_layout: QVBoxLayout,
                             movie_label: QLabel, movie: QMovie):
        main_layout.addLayout(spinner_layout)
        movie_label.show()
        movie.start()


    def stop_animation_in_movie(main_layout: QtWidgets.QHBoxLayout, spinner_layout: QVBoxLayout,
                           movie_label: QLabel, movie: QMovie):
        movie.stop()
        movie_label.hide()
        main_layout.removeItem(spinner_layout)
            
    # save and load previous texts
    def setup_save_configuration_events(self):
        self.txt_bx_main_file_input.textChanged.connect(self.save_configuration)
        self.txt_bx_secondary_files_input.textChanged.connect(self.save_configuration)
  
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
        try:
            f.close()
        except IOError:
            return


    def save_configuration(self):
        data = {
            self.MAIN_FILE_PATH: self.txt_bx_main_file_input.text(),
            self.SECONDARY_FILE_PATH: self.txt_bx_secondary_files_input.text(),
            self.SECONDARY_FILE_PATH: self.applicant_name_value
        }
        with open(self.CONFIG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)