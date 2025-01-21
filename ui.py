from octordle_solver.ui import WordleSolver
from PySide6 import QtWidgets


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = WordleSolver()
    window.show()
    app.exec()
