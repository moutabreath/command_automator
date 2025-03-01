import json
import os
import chardet
from qtpy import QtWidgets
from PyQt6.QtWidgets import QTextEdit, QSpacerItem, QSizePolicy, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit
import logging

from python_utils.pyqt import pyqt_utils
from python_utils.pyqt.text_editor import TextEditor
from tabs.llm.llm_logic_handler import LLMLogicHanlder


class LLMPromptTab(QtWidgets.QWidget):
    CURRENT_PATH = '/tabs/llm'
    MAIN_FILE_PATH = 'main_file_path'
    SECONDARY_FILE_PATH = 'secondary_file_dir'
    CONFIG_FILE_PATH = f'{os.getcwd()}/{CURRENT_PATH}/llm-config.json'
  
    def __init__(self):
        super().__init__()

        self.lLLMLogicHanldeR = LLMLogicHanlder()

        self.llm_layout = QVBoxLayout()

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
        self.llm_layout.addLayout(hBoxLayoutResponse)

        hBoxLayoutButtonAndQuery = QHBoxLayout()            
        
        self.btn_query_llm.clicked.connect(self.send_to_chat_gpt)
        
        self.txtBoxQuery.setStyleSheet("color: white;")
        hBoxLayoutButtonAndQuery.addWidget(self.txtBoxQuery)
        hBoxLayoutButtonAndQuery.addWidget(self.btn_query_llm)        
        self.llm_layout.addLayout(hBoxLayoutButtonAndQuery)    
    

        # File inputs section        
        bxFiles = QHBoxLayout()

        self.btn_select_main_file.clicked.connect(self.get_resume)        
        self.btn_select_seconadary_dir.clicked.connect(self.get_job_desc_dir)        
        self.btn_send_files_to_llm.clicked.connect(self.start_resume_building)        

        self.init_files_display(bxFiles)

        self.load_configuration()
        self.setup_save_configuration_events()
     
        self.llm_layout.addLayout(bxFiles)

        self.setLayout(self.llm_layout)

    def init_files_display(self, vBoxFiles: QVBoxLayout):
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
                                                         initial_dir, "Docx, PDF or txtfiles (*.docx *.pdf, *.txt)")
        self.txt_bx_main_file_input.setText(selected_file_name[0])

    def get_job_desc_dir(self):
        initial_dir = os.getcwd() + "/tabs/llm/jobs_descriptions"
        selected_dir = QFileDialog.getExistingDirectory(self, 'Select Directory', initial_dir)
        self.txt_bx_secondary_files_input.setText(selected_dir)

    def start_resume_building(self):
        resume_path = self.txt_bx_main_file_input.text()
        reume_text = self.get_resume_from_file(resume_path)
        if reume_text == None or reume_text == "":
            logging.log(logging.ERROR, "file content null")
            self.txtBoxResponse.setText("Error while trying to reach gemini")
            return
        logging.log(logging.DEBUG, "Resume file has been read, sending to LLM")
        for chunk in self.lLLMLogicHanldeR.stream_chat_with_gemini(reume_text):
            self.txtBoxResponse.append(chunk)


    def get_resume_from_file(self, file_path):
        line = None
        content = ''
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                file_encoding = result['encoding']


            with open(file_path, 'r',  encoding=file_encoding) as file:
               
                line = file.readline()
                
                while line:
                    content += line
                    line = file.readline()
        except UnicodeDecodeError as e:
            logging.log(logging.ERROR,"Error reading resume file: UnicodeDecodeError", e)
            return ""
        except IOError as e:
            logging.log(logging.ERROR,"Error reading resume file", e)
            return ""
        
        return content
    
    
    def setup_save_configuration_events(self):
        self.txt_bx_main_file_input.textChanged.connect(self.save_additional_text)
        self.txt_bx_secondary_files_input.textChanged.connect(self.save_additional_text)

   
    def save_additional_text(self):
        self.save_configuration()

    
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
        try:
            f.close()
        except IOError:
            return


    def save_configuration(self):
        data = {
            self.MAIN_FILE_PATH: self.txt_bx_main_file_input.text(),
            self.SECONDARY_FILE_PATH: self.txt_bx_secondary_files_input.text()
        }
        with open(self.CONFIG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)