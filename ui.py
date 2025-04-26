from PySide6 import QtWidgets

from octordle_solver.ui import WordleSolver

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = WordleSolver()
    window.show()
    app.exec()
