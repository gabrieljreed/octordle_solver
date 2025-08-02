import threading

from octordle_solver.ui.threads import ThreadWorker


def true_func(*args, **kwargs):
    return True


def error_func():
    raise RuntimeError("Test Error")


class TestThreadWorker:
    def test_init(self):
        worker = ThreadWorker(true_func, kwarg_1="kwarg_1", cancel_flag=None)
        assert worker.kwargs == {"kwarg_1": "kwarg_1"}

    def test_run(self, qtbot):
        worker = ThreadWorker(true_func, kwarg_1="kwarg_1", cancel_flag=None)

        with qtbot.waitSignals([worker.signals.result, worker.signals.finished]):
            worker.run()

    def test_run_error(self, qtbot):
        worker = ThreadWorker(error_func)
        with qtbot.waitSignals([worker.signals.error, worker.signals.finished]):
            worker.run()

    def test_run_cancel(self, qtbot):
        cancel_flag = threading.Event()
        cancel_flag.set()
        worker = ThreadWorker(true_func, cancel_flag=cancel_flag)

        with qtbot.waitSignal(worker.signals.canceled):
            worker.run()
