import logging

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal as Signal, pyqtSlot as Slot

from tabs.llm.llm_agents.gemini_agent import GeminiAgent
from typing import Tuple

class Signals(QObject):
    started = Signal(int)
    completed = Signal(int)


class GeminiUIWorker(QRunnable):
    def __init__(self, n):
        super().__init__()
        self.n = n
        self.signals = Signals()
        self.agent_response: Tuple[bool, str] = None
        self.err = []
        self.use_python_class = False
        self.gemini_agent = GeminiAgent()
        self.prompt = ""
    
    def set_prompt(self, prompt):
        self.prompt = prompt

    @Slot()
    def run(self):
        logging.log(logging.DEBUG, "entered")
        self.signals.started.emit(self.n)
        logging.log(logging.DEBUG, "emit 'started'")
        try:
            success, response = self.gemini_agent.chat_with_gemini(self.prompt)
            if not(success):
                logging.log(logging.ERORR, f"error {str(self.err)} {type(self.err)}" )
                return
            self.agent_response = success, response
        except TimeoutError as ex:
            self.err = str(ex)
            logging.log(logging.ERROR, self.err, ex)
        except Exception as ex1:
            self.err = str(ex1)
            logging.log(logging.ERROR, self.err, ex1)
        try:
            self.signals.completed.emit(self.n)
            logging.log(logging.DEBUG, "emit 'completed'")
        except Exception as ex2:
            logging.log(logging.ERROR, self.err, ex2)
