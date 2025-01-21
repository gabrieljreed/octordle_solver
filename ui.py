from octordle_solver.ui import WordleClone
from PySide6 import QtWidgets


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = WordleClone()
    window.show()
    app.exec()
