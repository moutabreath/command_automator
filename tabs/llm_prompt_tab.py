import PyQt6
from PyQt6.QtGui import QIcon, QMovie
from PyQt6 import QtCore
from qtpy import QtWidgets, QtCore
from PyQt6.QtWidgets import QTextEdit, QSpacerItem, QPlainTextEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,  QSizePolicy

from python_utils.pyqt import pyqt_utils
from python_utils.pyqt.text_editor import TextEditor
from tabs.llm_logic_handler import LLMLogicHanlder


class LLMPromptTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.lLLMLogicHanldeR = LLMLogicHanlder()

        btn_query_llm = QPushButton('Send Query')
        btn_query_llm.clicked.connect(self.send_to_chat_gpt)

        self.llm_layout = QVBoxLayout()
        
        hBoxLayoutResponse = QHBoxLayout()
        hBoxLayoutButtonAndQuery = QHBoxLayout()
        
        txtBoxResponse = QTextEdit()
        txtBoxResponse.setReadOnly(True)

        self.txtBoxQuery = TextEditor('Message LLM')


        hBoxLayoutResponse.addWidget(txtBoxResponse)
        hBoxLayoutButtonAndQuery.addWidget( self.txtBoxQuery)
        hBoxLayoutButtonAndQuery.addWidget(btn_query_llm)

        self.llm_layout.addLayout(hBoxLayoutResponse)
        self.llm_layout.addLayout(hBoxLayoutButtonAndQuery)

        self.setLayout(self.llm_layout)

    def send_to_chat_gpt(self):
        text = self.txtBoxQuery.toPlainText()
        text = self.lLLMLogicHanldeR.chat_with_gpt(text)
         