from PyQt6.QtCore import QRunnable, QObject, pyqtSignal as Signal, pyqtSlot as Slot

from tabs.llm.llm_agents.gemini_agent import GeminiAgent
import logging



class Signals(QObject):
    received = Signal(str)
    completed = Signal()

class GeminiStreamWorker(QRunnable):
    # A custom signal that sends out text chunks
    # chunk_signal = Signal(str)
    # finished_signal = Signal()

    def __init__(self):
        super().__init__()
        self.signals = Signals()

    def set_required(self, prompt, gemini_agent: GeminiAgent):
        self.gemini_agent = gemini_agent
        self.prompt = prompt

    @Slot()
    def run(self):
        try:
            logging.debug(f"starting with prompt: {self.prompt}")
            response = self.gemini_agent.stream_chat_with_gemini(self.prompt)
            for chunk in response:
                # self.chunk_signal.emit(chunk)
                self.signals.received.emit(chunk)
        except Exception as e:
            print(f"Error in GeminiStreamWorker: {e}")
        finally:
            self.signals.completed.emit()