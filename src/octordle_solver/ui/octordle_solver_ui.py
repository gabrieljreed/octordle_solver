"""UI for solving Octordle puzzles."""

from typing import Any

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from ..constants import STARTING_GUESS
from ..solver import PossibilityState, Puzzle, get_best_guess_multiple_puzzles
from .helpers import Color, LetterWidget


class WordleGridWidget(QtWidgets.QWidget):
    """Widget representing a single Wordle grid."""

    def __init__(self, parent: Any = None, num_rows: int = 13):
        """Initialize the widget."""
        super().__init__(parent)

        # TODO: Maybe the puzzle should live here? Depends on how the solver wants them

        self._current_row = 0
        self._current_col = 0

        self.num_rows = num_rows
        self.is_solved = False

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        self.grid_layout = QtWidgets.QGridLayout()
        self.setLayout(self.grid_layout)

        self.letter_boxes = []
        for row in range(self.num_rows):
            row_boxes = []
            for col in range(5):
                label = LetterWidget(dimensions=[60, 40])
                self.grid_layout.addWidget(label, row, col)
                row_boxes.append(label)
            self.letter_boxes.append(row_boxes)

    @property
    def current_box(self):
        """Get the current box."""
        return self.letter_boxes[self._current_row][self._current_col]

    def type_letter(self, letter):
        """Handle a letter being typed."""
        if self.is_solved:
            return
        if self._current_row < self.num_rows and self._current_col < 5:
            self.current_box.setText(letter)
            self._current_col += 1

    def delete_letter(self):
        """Delete a letter."""
        if self.is_solved:
            return
        if self._current_col > 0:
            self._current_col -= 1
            self.current_box.setText("")

    def handle_enter(self):
        """Handle enter being typed."""
        if self.is_solved:
            return
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

    @property
    def word(self) -> str:
        """Return the current word."""
        word = ""
        row = self.letter_boxes[self._current_row - 1]
        for i in range(5):
            box = row[i]
            word += box.text()
        return word

    @property
    def result(self):
        """Return the current result."""
        result = ""
        row = self._current_row - 1
        for col in range(5):
            current_box = self.letter_boxes[row][col]
            if current_box.state == PossibilityState.CORRECT:
                result += "Y"
            elif current_box.state == PossibilityState.MISPLACED:
                result += "M"
            else:
                result += "N"
        return result


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

        # Best guesses
        self.best_guess_widget = QtWidgets.QWidget()
        self.best_guess_widget.setLayout(QtWidgets.QVBoxLayout())
        layout.addWidget(self.best_guess_widget)

        self.get_best_guess_button = QtWidgets.QPushButton("Get best guesses")
        self.get_best_guess_button.clicked.connect(self.get_best_guess)
        self.best_guess_widget.layout().addWidget(self.get_best_guess_button)

        self.best_guess_widget.layout().addWidget(QtWidgets.QLabel("Best guesses"))

        self.best_guess_list = QtWidgets.QListWidget()
        self.best_guess_list.addItem(STARTING_GUESS)
        # self.best_guess_list.itemSelectionChanged.connect(self.update_groups_widgets)
        self.best_guess_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # self.best_guess_list.customContextMenuRequested.connect(self.show_best_guess_context_menu)
        # self.best_guess_list.itemDoubleClicked.connect(self.handle_best_guess_double_click)
        self.best_guess_widget.layout().addWidget(self.best_guess_list)

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

    def get_best_guess(self):
        """Get the best guess for the given game state."""
        # TODO: Figure out how to exit early if the word is not complete

        for i in range(8):
            print(i)
            puzzle = self.puzzles[i]
            puzzle_widget = self.puzzle_widgets[i]
            print(f"{puzzle_widget.word = }")
            print(f"{puzzle_widget.result = }")
            # TODO: thread this
            puzzle.make_guess(puzzle_widget.word, puzzle_widget.result)
            print(puzzle)
            if puzzle.is_solved:
                puzzle_widget.is_solved = True
                continue

        best_guess = get_best_guess_multiple_puzzles([puzzle for puzzle in self.puzzles if not puzzle.is_solved])
        print(f"{best_guess = }")
