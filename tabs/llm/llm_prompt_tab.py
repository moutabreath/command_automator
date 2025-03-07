import json
import os
from qtpy import QtWidgets
from PyQt6.QtWidgets import QTextEdit, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit

from python_utils.pyqt.text_editor import TextEditor
from tabs.llm.llm_logic_handler import LLMLogicHanlder


class LLMPromptTab(QtWidgets.QWidget):
    MAIN_FILE_PATH = 'main_file_path' 
    SECONDARY_FILE_PATH = 'secondary_file_dir'
    APPLICANT_NAME_TAG = 'applicant_name'
    applicant_name_value = ''
  
    def __init__(self):
        super().__init__()

        self.lLLMLogicHanlder = LLMLogicHanlder()
        self.CONFIG_FILE_PATH = f'{os.getcwd()}/{self.lLLMLogicHanlder.CURRENT_PATH}/llm-config.json'

        self.worker = None

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
        success, text = self.lLLMLogicHanlder.gemini_agent.chat_with_gemini(text)
        if (not(success)):
            self.txtBoxResponse.setText("An error occured when chatting with llm")

        self.btn_query_llm.setEnabled(True)
        self.btn_query_llm.setStyleSheet(old_style_sheet)

        self.txtBoxResponse.setText(text)
    
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