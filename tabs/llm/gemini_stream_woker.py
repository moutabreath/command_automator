from PyQt6.QtCore import QThread, pyqtSignal as Signal, pyqtSlot as Slot

from tabs.llm.llm_agents.gemini_agent import GeminiAgent

class GeminiStreamWorker(QThread):
    # A custom signal that sends out text chunks
    chunk_signal = Signal(str)

    def __init__(self, prompt, gemini_agent: GeminiAgent, parent=None):
        super().__init__(parent)
        self.gemini_agent = gemini_agent
        self.prompt = prompt

    def run(self):
        # Call send_message_stream to get the response chunks.
        # Each 'chunk' is expected to have a 'text' attribute.
        response = self.gemini_agent.stream_chat_with_gemini(self.prompt)
        for chunk in response:
            self.chunk_signal.emit(chunk.text)