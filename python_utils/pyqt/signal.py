import logging
import subprocess

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal as Signal, pyqtSlot as Slot

from python_utils.logger import Logger


class Signals(QObject):
    started = Signal(int)
    completed = Signal(int)


class Worker(QRunnable):
    def __init__(self, n):
        super().__init__()
        self.n = n
        self.signals = Signals()
        self.script_arguments = []
        self.process_output = []
        self.err = []
        self.use_python_class = False
        self.proc = None
        self.process_root = None
        self.proces_venv = None

    def set_arguments(self, arguments):
        self.script_arguments = arguments

    @Slot()
    def run(self):
        logging.log(logging.DEBUG, "entered")
        self.signals.started.emit(self.n)
        logging.log(logging.DEBUG, "emit 'started'")
        try:
            self.process_output, self.err = self.run_internal()
            logging.log(logging.DEBUG, "process output " + str(self.process_output))
            if self.err is not None and len(self.err) > 0:
                logging.log(logging.ERORR, f"error {str(self.err)} {type(self.err)}" )
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


    def cancel_execution(self):
        self.proc.kill()
        self.signals.completed.emit(self.n)

    def run_internal(self):
        logging.log(logging.DEBUG, "entered")
        self.proc = subprocess.Popen(self.script_arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.proces_venv)
        logging.log(logging.DEBUG, "popen done")
        output, err = self.proc.communicate()
        logging.log(logging.DEBUG, "proc communicate done")
        return output, err
