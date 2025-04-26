"""Threading UI utilities."""

from PySide6 import QtCore

import traceback
import sys


class WorkerSignals(QtCore.QObject):
    """Signals for the thread worker."""

    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    result = QtCore.Signal(object)
    progress = QtCore.Signal(int)


class ThreadWorker(QtCore.QRunnable):
    """Thread worker to run in background."""

    def __init__(self, fn, *args, **kwargs):
        """Initialize the object."""
        super().__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        self.signals = WorkerSignals()

    def run(self):
        """Run the thread."""
        try:
            result = self.fn(*self.args, **self.kwargs)

        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
