import json
import logging
import os

from qtpy import QtWidgets
from PyQt6.QtWidgets import QMainWindow, QWidget, QTextEdit, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
from PyQt6.QtCore import Qt, QRect, QSize, QThreadPool
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

       

        # UI layout
        self.main_layout = QVBoxLayout()

        self.txtBoxResponse = QTextEdit()
        self.txtBoxResponse.setStyleSheet("color: white;")
        self.btn_query_llm = QPushButton('Send Query')
        self.txtBoxQuery = TextEditor('Message LLM')

        self.txt_bx_main_file_input = QLineEdit()
        self.btn_select_main_file = QPushButton("Select Resume File")

        self.txt_bx_secondary_files_input = QLineEdit()
        self.btn_select_seconadary_dir = QPushButton("Job files dir")
        self.btn_send_files_to_llm = QPushButton("Chat using files")
        
        hBoxLayoutResponse = QHBoxLayout()
        
        self.txtBoxResponse.setReadOnly(True)
        hBoxLayoutResponse.addWidget(self.txtBoxResponse)      
        self.main_layout.addLayout(hBoxLayoutResponse)

        hBoxLayoutButtonAndQuery = QHBoxLayout()            
        
        self.btn_query_llm.clicked.connect(self.send_to_chat_gpt)
        
        # self.txtBoxQuery.setStyleSheet("color: white;")
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

    def setup_spinner(self):
        self.central_widget.setObjectName("main-widget")
        self.movie_label.setGeometry(QRect(25, 25, 200, 200))
        self.movie_label.setMinimumSize(QSize(250, 250))
        self.movie_label.setMaximumSize(QSize(250, 250))
        self.movie_label.setObjectName("lb1")
        self.movie_label.setMovie(self.movie)

 

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
        try:
            self.gemini_ui_worker = GeminiUIWorker(1)
            self.gemini_ui_worker.llm_logic_handler = self.lLLMLogicHanlder
            self.gemini_ui_worker.signals.completed.connect(self.stop_animation)
            self.gemini_ui_worker.signals.started.connect(self.start_animation)
            self.gemini_ui_worker.input = [self.applicant_name_value, resume_path, job_desc_path]
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
            
    def format_response_for_display(self,response_text):
        # Split the text into lines
        lines = response_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('**'):
                # Handle bold lines (remove ** and wrap in bold tags)
                text = line[2:].strip()  # Remove ** from start
                if text.endswith('**'):
                    text = text[:-2]  # Remove ** from end if present
                formatted_lines.append(f"<b>{text}</b>")
            elif line.startswith('*'):
                # Handle list items (remove * and add bullet point)
                text = line[1:].strip()
                formatted_lines.append(f"• {text}")
            else:
                # Regular text
                formatted_lines.append(line)
        
        # Join with HTML line breaks
        return "<br>".join(formatted_lines)

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