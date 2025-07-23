"""UI for solving Octordle puzzles."""

from typing import Any

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from ..solver import Puzzle
from .helpers import Color, LetterWidget


class WordleGridWidget(QtWidgets.QWidget):
    """Widget representing a single Wordle grid."""

    def __init__(self, parent: Any = None):
        """Initialize the widget."""
        super().__init__(parent)

        # TODO: Maybe the puzzle should live here? Depends on how the solver wants them

        self._current_row = 0
        self._current_col = 0

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        self.grid_layout = QtWidgets.QGridLayout()
        self.setLayout(self.grid_layout)

        self.letter_boxes = []
        for row in range(6):
            row_boxes = []
            for col in range(5):
                label = LetterWidget()
                self.grid_layout.addWidget(label, row, col)
                row_boxes.append(label)
            self.letter_boxes.append(row_boxes)

    @property
    def current_box(self):
        """Get the current box."""
        return self.letter_boxes[self._current_row][self._current_col]

    def type_letter(self, letter):
        """Handle a letter being typed."""
        if self._current_row < 6 and self._current_col < 5:
            self.current_box.setText(letter)
            self._current_col += 1

    def delete_letter(self):
        """Delete a letter."""
        if self._current_col > 0:
            self._current_col -= 1
            self.current_box.setText("")

    def handle_enter(self):
        """Handle enter being typed."""
        if self._current_row > 6 or self._current_col != 5:
            print("Word is not complete")
            return

        word = ""
        for i in range(5):
            letter = self.letter_boxes[self._current_row][i].text()
            word += letter

        for i in range(5):
            current_box = self.letter_boxes[self._current_row][i]
            current_box.letter_is_set = True
            current_box.set_color(Color.GRAY)

        self._current_row += 1
        self._current_col = 0


class OctordleSolver(QtWidgets.QMainWindow):
    """UI for solving Octordle puzzles."""

    def __init__(self):
        """Initialize the widget."""
        super().__init__()

        self.puzzles = [
            Puzzle(),
            Puzzle(),
            Puzzle(),
            Puzzle(),
            Puzzle(),
            Puzzle(),
            Puzzle(),
            Puzzle(),
        ]

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("Octordle Solver")

        # Main container
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(layout)

        # Puzzle
        self.puzzle_scroll_area = QtWidgets.QScrollArea()
        layout.addWidget(self.puzzle_scroll_area)

        # TODO: Probably rename some of these to not be so similar
        self.puzzles_widget = QtWidgets.QWidget()
        self.puzzles_layout = QtWidgets.QGridLayout()
        self.puzzles_widget.setLayout(self.puzzles_layout)
        self.puzzle_widgets: list[WordleGridWidget] = []
        # TODO: Don't hard code these numbers
        for row in range(4):
            for col in range(2):
                puzzle_widget = WordleGridWidget()
                self.puzzles_layout.addWidget(puzzle_widget, row, col)
                self.puzzle_widgets.append(puzzle_widget)
        self.puzzle_scroll_area.setWidget(self.puzzles_widget)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() in range(Qt.Key_A, Qt.Key_Z + 1):
            self._handle_letter_input(event.text().upper())
        elif event.key() == Qt.Key_Backspace:
            self._handle_backspace()
        elif event.key() == Qt.Key_Return:
            self._handle_enter()

    def _handle_letter_input(self, letter: str):
        """Handle a letter input."""
        for puzzle_widget in self.puzzle_widgets:
            puzzle_widget.type_letter(letter)

    def _handle_backspace(self):
        """Handle backspace input."""
        for puzzle_widget in self.puzzle_widgets:
            puzzle_widget.delete_letter()

    def _handle_enter(self):
        """Handle enter input."""
        for puzzle_widget in self.puzzle_widgets:
            puzzle_widget.handle_enter()
