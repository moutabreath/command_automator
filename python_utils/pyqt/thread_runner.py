import logging
from PyQt6.QtCore import QThreadPool

from python_utils.pyqt.runnable_worker import RunnableWorker


class ThreadRunner:
    def __init__(self):
        self.thread_pool = QThreadPool.globalInstance()
        self.runnable_worker = None

    def run_command(self, process_input, on_complete, on_start, new_venv):
        try:
            self.runnable_worker = RunnableWorker(1)
            self.runnable_worker.process_venv = new_venv
            self.runnable_worker.signals.completed.connect(on_complete)
            self.runnable_worker.signals.started.connect(on_start)
            self.runnable_worker.set_arguments(process_input)
            self.thread_pool.start(self.runnable_worker)
        except IOError as e:
            logging.log(logging.ERROR, "run_command: error", e)
            
    def stop_command(self):
        self.runnable_worker.cancel_execution()

    def get_run_result(self):
        return self.runnable_worker.process_output, self.runnable_worker.err
