import traceback

from PyQt6.QtCore import QThreadPool

from signal import Worker


class ThreadRunner:
    def __init__(self):
        self.thread_pool = QThreadPool.globalInstance()
        self.worker = None

    def run_command(self, process_input, on_complete, on_start, new_venv):
        try:
            self.worker = Worker(1)
            self.worker.process_venv = new_venv
            self.worker.signals.completed.connect(on_complete)
            self.worker.signals.started.connect(on_start)
            self.worker.set_arguments(process_input)
            self.thread_pool.start(self.worker)
        except IOError:
            traceback.print_exc()
            
    def stop_command(self):
        self.worker.cancel_execution()

    def get_run_result(self):
        return self.worker.process_output, self.worker.err
