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
        Logger.print_log("[signal.run] entered")
        self.signals.started.emit(self.n)
        Logger.print_log("[signal.run] emit 'started'")
        try:
            self.process_output, self.err = self.run_internal()
            Logger.print_log("[signal.run] process output " + str(self.process_output))
            if self.err is not None and len(self.err) > 0:
                Logger.print_log(f"[signal.run] error {str(self.err)} {type(self.err)}" )
        except TimeoutError as ex:
            self.err = str(ex)
            Logger.print_error_message(self.err, ex)

        except Exception as ex1:
            self.err = str(ex1)
            Logger.print_error_message(self.err, ex1)
        try:
            self.signals.completed.emit(self.n)
            Logger.print_log("[signal.run] emit 'completed'")
        except Exception as ex2:
            Logger.print_error_message(self.err, ex2)


    def cancel_execution(self):
        self.proc.kill()
        self.signals.completed.emit(self.n)

    def run_internal(self):
        Logger.print_log("[signal.run_internal] entered")
        self.proc = subprocess.Popen(self.script_arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.proces_venv)
        Logger.print_log("[signal.run_internal] popen done")
        output, err = self.proc.communicate()
        Logger.print_log("[signal.run_internal] proc communicate done")
        return output, err
