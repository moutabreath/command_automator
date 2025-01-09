import string

from PyQt6.QtWidgets import QFrame, QSizePolicy, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QComboBox
from PyQt6.QtGui import QMovie

class PyQtUtils:

    @staticmethod
    def add_blank_line(vertical_box_layout, layout_above_separator, layout_below_separator) -> QVBoxLayout:
        separator = PyQtUtils.create_horizontal_separator()
        if layout_above_separator is not None:
            vertical_box_layout.addLayout(layout_above_separator)
        vertical_box_layout.addWidget(separator)
        if layout_below_separator is not None:
            vertical_box_layout.addLayout(layout_below_separator)
        return vertical_box_layout

    @staticmethod
    def create_vertical_separator() -> QFrame:
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        separator.setLineWidth(3)
        return separator

    @staticmethod
    def create_horizontal_box(widget1, widget2, spacer_item=None) ->QHBoxLayout:
        horizontal_box = QHBoxLayout()
        horizontal_box.addWidget(widget1)
        if spacer_item is not None:
            horizontal_box.addItem(spacer_item)
        horizontal_box.addWidget(widget2)
        return horizontal_box

    @staticmethod
    def create_vertical_box(widget1, widget2) -> QVBoxLayout:
        vertical_box = QVBoxLayout()
        vertical_box.addWidget(widget1)
        vertical_box.addWidget(widget2)
        return vertical_box
    
    @staticmethod
    def create_horizontal_separator() -> QFrame:
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        separator.setLineWidth(3)
        return separator

    @staticmethod
    def set_selected_value(data, combo_box: QComboBox, attribute: string):
        if data[attribute] != "":
            index = combo_box.findText(data[attribute])
            if index != -1:
                combo_box.setCurrentText(data[attribute])


    @staticmethod
    def start_animation_in_movie(v_box_layout : QVBoxLayout, spinner_and_cancel_v_layout : QVBoxLayout,
                                btn_cancel_exec : QPushButton, movie_label: QLabel, movie : QMovie):       
        v_box_layout.addLayout(spinner_and_cancel_v_layout)
        btn_cancel_exec.show()
        movie_label.show()
        movie.start()

    @staticmethod
    def stop_animation_in_movie(code_tab_layout : QVBoxLayout, spinner_and_cancel_v_layout : QVBoxLayout,
                                btn_cancel_exec : QPushButton, movie_label: QLabel, movie : QMovie):
        movie.stop()
        btn_cancel_exec.hide()
        movie_label.hide()
        code_tab_layout.removeItem(spinner_and_cancel_v_layout)

    @staticmethod
    def make_dark_mode(pyqtWidget):
        # Set dark mode style
        pyqtWidget.setStyleSheet("""QWidget { color: #333; background-color: #222; }
    
        QTabBar::tab {
            color: #fff; 
            background-color: #222; 
            border: 0.5px solid green;
            border-bottom-color: solid green; /* same as the pane color */
            border-top-color: solid green; /* same as the pane color */
            border-top-left-radius: 0.5px;
            border-top-right-radius: 0.5px;
            min-width: 8ex;
            padding: 2px;
        }

        /* Apply dark mode to the selected tab title */
        QTabBar::tab:selected {
            color: #222;
            background-color: green;
        }
        QLabel { color: #fff; border: 1px; border-radius: 5px; padding: 5px; } 
        QCheckBox { color: #fff; border: 1px; border-radius: 5px; padding: 5px; } 
        QPushButton { color: #fff; background-color: green; border-radius: 5px; padding: 5px;} 
        QComboBox {color: #fff; background-color: #222; border: 2px solid green} 
        QComboBox:items{ color: #fff; border: 2px solid green }
        QListView{ color:  #fff; }
        QLineEdit {color: #fff; border: 2px solid green } 
        QPlainTextEdit {color: #fff; border: 2px solid green}  """)