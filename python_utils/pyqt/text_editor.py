from PyQt6.QtWidgets import QTextEdit

class TextEditor(QTextEdit):
    def __init__(self, placeholder_text):
        super().__init__()
        self.setPlaceholderText(placeholder_text)
        self.initUI()

    def initUI(self):
        self.setAcceptRichText(False)  # For plain text editing
        self.textChanged.connect(self.onTextChanged)
        self.setFixedHeight(30)

    def onTextChanged(self):
        if self.toPlainText():
            self.setPlaceholderText("")

        document_height = int(self.document().size().height())
        self.setFixedHeight(document_height + 10)