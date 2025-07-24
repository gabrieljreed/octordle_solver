"""Launch the Wordle Solver UI."""

from PySide6 import QtWidgets

from .octordle_solver_ui import OctordleSolver
from .wordle_solver_ui import WordleSolver


def wordle():
    """Launch the Wordle Solver UI."""
    app = QtWidgets.QApplication([])
    window = WordleSolver()
    window.show()
    app.exec()


def octordle():
    """Launch the Octordle Solver UI."""
    app = QtWidgets.QApplication([])
    window = OctordleSolver()
    window.show()
    app.exec()


if __name__ == "__main__":
    wordle()
