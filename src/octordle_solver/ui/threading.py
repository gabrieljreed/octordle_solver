"""Threading UI utilities."""

import sys
import threading
import traceback
from typing import Optional

from PySide6 import QtCore


class WorkerSignals(QtCore.QObject):
    """Signals for the thread worker."""

    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    result = QtCore.Signal(object)
    progress = QtCore.Signal(int)
    canceled = QtCore.Signal()


class ThreadWorker(QtCore.QRunnable):
    """Thread worker to run in background."""

    def __init__(self, fn, cancel_flag: Optional[threading.Event] = None, *args, **kwargs):
        """Initialize the object."""
        super().__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.cancel_flag = cancel_flag

        self.signals = WorkerSignals()

    def run(self):
        """Run the thread."""
        if self.cancel_flag and self.cancel_flag.is_set():
            self.signals.canceled.emit()
            return

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
