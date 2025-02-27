from qtpy import QtWidgets
from PyQt6.QtWidgets import QTextEdit, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit

from python_utils.pyqt import pyqt_utils
from python_utils.pyqt.text_editor import TextEditor
from tabs.llm_logic_handler import LLMLogicHanlder


class LLMPromptTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.lLLMLogicHanldeR = LLMLogicHanlder()

        self.llm_layout = QVBoxLayout()
        
        hBoxLayoutResponse = QHBoxLayout()       
        self.txtBoxResponse = QTextEdit()
        self.txtBoxResponse.setReadOnly(True)
        hBoxLayoutResponse.addWidget(self.txtBoxResponse)        
        self.llm_layout.addLayout(hBoxLayoutResponse)

        hBoxLayoutButtonAndQuery = QHBoxLayout()               
        self.btn_query_llm = QPushButton('Send Query')
        self.btn_query_llm.clicked.connect(self.send_to_chat_gpt)
        self.txtBoxQuery = TextEditor('Message LLM')
        hBoxLayoutButtonAndQuery.addWidget(self.txtBoxQuery)
        hBoxLayoutButtonAndQuery.addWidget(self.btn_query_llm)        
        self.llm_layout.addLayout(hBoxLayoutButtonAndQuery)


        hBoxFiles = QHBoxLayout()
        self.txt_bx_main_file_input = QLineEdit()
        btn_select_main_file = QPushButton("Select Resumee File")
        btn_select_main_file.clicked.connect(self.get_file)        
        self.txt_bx_secondaryfiles_input = QLineEdit()
        btn_select_seconadary_dir = QPushButton("Job descriptions direcotry")
        btn_select_seconadary_dir.clicked.connect(self.get_file)        

        self.setLayout(self.llm_layout)

    def send_to_chat_gpt(self): 
        self.btn_query_llm.setEnabled(False)
        old_style_sheet = self.btn_query_llm.styleSheet()
        self.btn_query_llm.setStyleSheet("color: gray;")

        text = self.txtBoxQuery.toPlainText()
        text = self.lLLMLogicHanldeR.chat_with_gemini(text)


        self.btn_query_llm.setEnabled(True)
        self.btn_query_llm.setStyleSheet(old_style_sheet)

        self.txtBoxResponse.setText(text)
    
    def get_file(self):
        selected_file_name = QFileDialog.getOpenFileName(self, 'Open file',
                                                         'c:\\', "XML files (*.xml)")
        self.txt_bx_main_file_input.setText(selected_file_name[0])