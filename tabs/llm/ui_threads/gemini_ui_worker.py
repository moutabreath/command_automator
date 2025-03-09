import logging
from typing import Tuple

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal as Signal, pyqtSlot as Slot

from tabs.llm.llm_agents.gemini_agent import GeminiAgent
from tabs.llm.llm_logic_handler import LLMLogicHanlder


class Signals(QObject):
    started = Signal(int)
    completed = Signal(int)


class GeminiUIWorker(QRunnable):
    def __init__(self, n):
        super().__init__()
        self.signals = Signals()
        self.agent_response: str = None
        self.err = None
        self.n = n 
        self.llm_logic_handler: LLMLogicHanlder = None
        self.gemini_agent = None
        self.input = []
    

    @Slot()
    def run(self):
        logging.debug("entered")
        self.signals.started.emit(self.n)
        logging.debug("emit 'started'")
        try:
            applicant_name = self.input[0]
            resume_path = self.input[1]
            job_desc_path = self.input[2]
            logging.debug(f'({applicant_name}, {resume_path}, {job_desc_path})')
            response = self.llm_logic_handler.start_resume_building(applicant_name, resume_path, job_desc_path)
            self.agent_response = response
        except TimeoutError as ex:
            logging.error("Error",  exc_info=True)
        except Exception as ex1:
            logging.error("Error",  exc_info=True)
        try:
            self.signals.completed.emit(self.n)
            logging.debug("emit 'completed'")
        except Exception as ex2:
            logging.error("error",  exc_info=True)
