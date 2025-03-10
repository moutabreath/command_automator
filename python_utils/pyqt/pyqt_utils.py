import PyQt6
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QFrame, QSizePolicy, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QIcon, QMovie


def add_blank_line(vertical_box_layout, layout_above_separator, layout_below_separator) -> QVBoxLayout:
    separator = create_horizontal_separator()
    if layout_above_separator is not None:
        vertical_box_layout.addLayout(layout_above_separator)
    vertical_box_layout.addWidget(separator)
    if layout_below_separator is not None:
        vertical_box_layout.addLayout(layout_below_separator)
    return vertical_box_layout


def create_vertical_separator():
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
    separator.setLineWidth(3)
    return separator


def create_horizontal_box(widget1, widget2, spacer_item=None):
    horizontal_box = QHBoxLayout()
    horizontal_box.addWidget(widget1)
    if spacer_item is not None:
        horizontal_box.addItem(spacer_item)
    horizontal_box.addWidget(widget2)
    return horizontal_box


def create_vertical_box(widget1, widget2, widget3 = None):
    vertical_box = QVBoxLayout()
    vertical_box.addWidget(widget1)
    vertical_box.addWidget(widget2)
    if widget3 != None:
        vertical_box.addWidget(widget3)
    return vertical_box


def create_horizontal_separator():
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
    separator.setLineWidth(3)
    return separator


def set_selected_value(data, combo_box, attribute):
    if data[attribute] != "":
        index = combo_box.findText(data[attribute])
        if index != -1:
            combo_box.setCurrentText(data[attribute])


def start_animation_in_movie(code_tab_layout: QtWidgets.QVBoxLayout, spinner_and_cancel_v_layout: QtWidgets.QVBoxLayout,
                             btn_cancel_exec: PyQt6.QtWidgets.QPushButton, movie_label: QtWidgets.QLabel,
                             movie: QMovie):
    code_tab_layout.addLayout(spinner_and_cancel_v_layout)
    btn_cancel_exec.show()
    movie_label.show()
    movie.start()


def stop_animation_in_movie(code_tab_layout: QtWidgets.QHBoxLayout, spinner_and_cancel_v_layout: QtWidgets.QVBoxLayout,
                            btn_cancel_exec: PyQt6.QtWidgets.QPushButton, movie_label: QtWidgets.QLabel, movie: QMovie):
    movie.stop()
    btn_cancel_exec.hide()
    movie_label.hide()
    code_tab_layout.removeItem(spinner_and_cancel_v_layout)

def make_dark_mode(pyqtWidget):
    pyqtWidget.setStyleSheet("""
        QWidget { 
            color: #333; 
            background-color: #222; 
        }

        QTabBar::tab {
            color: #fff; 
            background-color: #222; 
            border: 0.5px solid #9EA3F5;
            border-bottom-color: #9EA3F5;
            border-top-color: #9EA3F5;
            border-top-left-radius: 0.5px;
            border-top-right-radius: 0.5px;
            min-width: 8ex;
            padding: 2px;
        }

        QTabBar::tab:selected {
            color: #222;
            background-color: #9EA3F5;
        }

        QLabel { 
            color: #fff; 
            padding: 5px; 
        } 

        QCheckBox { 
            color: #fff; 
            border: 1px solid #9EA3F5; 
            border-radius: 5px; 
            padding: 5px; 
        } 

        QPushButton { 
            color: #fff; 
            background-color: #9EA3F5; 
            border-radius: 5px; 
            padding: 5px;
        } 

        QComboBox {
            color: #fff; 
            background-color: #222; 
            border: 2px solid #9EA3F5;
            padding: 5px;
            border-radius: 3px;
        } 

        QListView { 
            color: #fff;
            border: 2px solid #9EA3F5;
        }

        QLineEdit {
            color: #fff; 
            background-color: #222;
            border: 2px solid #9EA3F5;
            border-radius: 3px;
            padding: 5px;
        } 

        QPlainTextEdit {
            color: #fff; 
            background-color: #222;
            border: 2px solid #9EA3F5;
            border-radius: 3px;
            padding: 5px;
        } 

        QTextEdit {
            color: #fff; 
            background-color: #222;
            border: 2px solid #9EA3F5;
            border-radius: 3px;
            padding: 5px;
        }
    """)
