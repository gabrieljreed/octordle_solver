"""Launch the Wordle Solver UI."""

from PySide6 import QtWidgets

from .wordle_solver_ui import WordleSolver


def main():
    """Launch the Wordle Solver UI."""
    app = QtWidgets.QApplication([])
    window = WordleSolver()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
