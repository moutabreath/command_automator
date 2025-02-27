import os
from qtpy import QtWidgets
from PyQt6.QtWidgets import QTextEdit, QSpacerItem, QSizePolicy, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit

from python_utils.logger import Logger
from python_utils.pyqt import pyqt_utils
from python_utils.pyqt.text_editor import TextEditor
from tabs.llm.llm_logic_handler import LLMLogicHanlder


class LLMPromptTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.lLLMLogicHanldeR = LLMLogicHanlder()

        self.llm_layout = QVBoxLayout()
        
        hBoxLayoutResponse = QHBoxLayout()
        self.txtBoxResponse = QTextEdit()
        self.txtBoxResponse.setReadOnly(True)
        self.txtBoxResponse.setStyleSheet("color: white;")
        hBoxLayoutResponse.addWidget(self.txtBoxResponse)        
        self.llm_layout.addLayout(hBoxLayoutResponse)

        hBoxLayoutButtonAndQuery = QHBoxLayout()               
        self.btn_query_llm = QPushButton('Send Query')
        self.btn_query_llm.clicked.connect(self.send_to_chat_gpt)
        self.txtBoxQuery = TextEditor('Message LLM')
        self.txtBoxQuery.setStyleSheet("color: white;")
        hBoxLayoutButtonAndQuery.addWidget(self.txtBoxQuery)
        hBoxLayoutButtonAndQuery.addWidget(self.btn_query_llm)        
        self.llm_layout.addLayout(hBoxLayoutButtonAndQuery)    
    

        # File inputs section        
        bxFiles = QHBoxLayout()

        self.txt_bx_main_file_input = QLineEdit()
        self.btn_select_main_file = QPushButton("Select Resume File")
        self.btn_select_main_file.clicked.connect(self.get_resume) 

        self.txt_bx_secondary_files_input = QLineEdit()
        self.btn_select_seconadary_dir = QPushButton("Job files dir")
        self.btn_select_seconadary_dir.clicked.connect(self.get_job_desc_dir)

        self.btn_send_files_to_llm = QPushButton("Chat using files")
        self.btn_send_files_to_llm.clicked.connect(self.start_resume_building)
        

        self.init_display(bxFiles)

     
        self.llm_layout.addLayout(bxFiles)

        self.setLayout(self.llm_layout)

    def init_display(self, vBoxFiles: QVBoxLayout):
        boxTxtBx = QVBoxLayout()

        boxTxtBx.addWidget(self.txt_bx_main_file_input)
        boxTxtBx.addWidget(self.txt_bx_secondary_files_input)

        vBoxFiles.addLayout(boxTxtBx)

        bxButtons = QVBoxLayout()
        bxButtons.addWidget(self.btn_select_main_file)
        bxButtons.addWidget(self.btn_select_seconadary_dir)
        bxButtons.addWidget(self.btn_send_files_to_llm)
        
        vBoxFiles.addLayout(bxButtons)


    def send_to_chat_gpt(self): 
        self.btn_query_llm.setEnabled(False)
        old_style_sheet = self.btn_query_llm.styleSheet()
        # self.btn_query_llm.setStyleSheet("color: gray;")

        text = self.txtBoxQuery.toPlainText()
        text = self.lLLMLogicHanldeR.chat_with_gemini(text)


        self.btn_query_llm.setEnabled(True)
        self.btn_query_llm.setStyleSheet(old_style_sheet)

        self.txtBoxResponse.setText(text)
    
    def get_resume(self):
        initial_dir = os.getcwd() + "/tabs/llm/resume"
        selected_file_name = QFileDialog.getOpenFileName(self, 'Open file',
                                                         initial_dir, "Docx or PDF files (*.docx *.pdf)")
        self.txt_bx_main_file_input.setText(selected_file_name[0])

    def get_job_desc_dir(self):
        initial_dir = os.getcwd() + "/tabs/llm/jobs_descriptions"
        selected_dir = QFileDialog.getExistingDirectory(self, 'Select Directory', initial_dir)
        self.txt_bx_secondary_files_input.setText(selected_dir)

    def start_resume_building(self):
        resume_path = self.txt_bx_main_file_input.text()
        reume_text = self.get_resume_from_file(resume_path)
        Logger.print_log("Resume file has been read, sending to LLM")
        for chunk in self.lLLMLogicHanldeR.stream_chat_with_gemini(reume_text):
            self.txtBoxResponse.append(chunk)


    def get_resume_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            Logger.print_error_message("Error reading resume file: UnicodeDecodeError", e)
            return ""
        except IOError as e:
            Logger.print_error_message("Error reading resume file", e)
            return ""
        
        return content