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
        self.process_venv = None

    def set_arguments(self, arguments):
        self.script_arguments = arguments

    @Slot()
    def run(self):
        logging.debug("[signal.run] entered")
        self.signals.started.emit(self.n)
        logging.debug("[signal.run] emit 'started'")
        try:
            self.process_output, self.err = self.run_internal()
            logging.debug("[signal.run] process output " + str(self.process_output))
            if self.err is not None and len(self.err) > 0:
                logging.debug(f"[signal.run] error {str(self.err)} {type(self.err)}")
        except TimeoutError as ex:
            self.err = str(ex)
            logging.error(f'Error: {ex}')

        except Exception as ex1:
            self.err = str(ex1)
            logging.error(f'Error: {ex1}')
        try:
            self.signals.completed.emit(self.n)
            Logger.print_log("[signal.run] emit 'completed'")
        except Exception as ex2:
            logging.error(f'Error: {ex2}')

    def cancel_execution(self):
        self.proc.kill()
        self.signals.completed.emit(self.n)

    def run_internal(self):
        logging.debug(f'[signal.run_internal] entered with args: {self.script_arguments}')
        if self.process_venv is None:
            logging.debug("[signal.run_internal] No venv")
            self.proc = subprocess.Popen(self.script_arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            logging.debug("[signal.run_internal] With venv")
            self.proc = subprocess.Popen(self.script_arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         env=self.process_venv)
        logging.debug("[signal.run_internal] Popen done. Starting communicate")
        try:
            output, err = self.proc.communicate()
            logging.debug("[signal.run_internal] proc communicate done")
            return output, err
        except Exception as ex1:
            logging.error(f'Error: {ex1}')
            return None ,None

