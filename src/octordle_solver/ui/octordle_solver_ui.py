"""UI for solving Octordle puzzles."""

import threading
from typing import Any, Optional

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt

from ..constants import STARTING_GUESS
from ..solver import PossibilityState, Puzzle, get_best_guess_multiple_puzzles
from .helpers import Color, LetterWidget
from .threading import ThreadWorker


class WordleGridWidget(QtWidgets.QWidget):
    """Widget representing a single Wordle grid."""

    def __init__(self, parent: Any = None, num_rows: int = 13):
        """Initialize the widget."""
        super().__init__(parent)

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
        if self._current_row > self.num_rows or self._current_col != 5:
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

        self.best_guess = STARTING_GUESS

        self.threadpool = QtCore.QThreadPool()
        self.remaining_tasks = 0

        self.letters_typed = 0
        self.is_first_word_guessed = False

        self.cancel_flag = threading.Event()

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("Octordle Solver")

        # Main container
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(layout)

        # Splitter
        splitter = QtWidgets.QSplitter(Qt.Horizontal)
        splitter.splitterMoved.connect(self.relayout_puzzles)
        layout.addWidget(splitter)

        # Puzzle
        self.puzzle_scroll_area = QtWidgets.QScrollArea()
        self.puzzle_scroll_area.setWidgetResizable(True)
        splitter.addWidget(self.puzzle_scroll_area)

        self.all_puzzles_widget = QtWidgets.QWidget()
        self.all_puzzles_layout = QtWidgets.QGridLayout()
        self.all_puzzles_widget.setLayout(self.all_puzzles_layout)
        self.puzzle_widgets: list[WordleGridWidget] = []
        for i in range(8):
            puzzle_widget = WordleGridWidget()
            row = i // 4
            col = i % 4
            self.all_puzzles_layout.addWidget(puzzle_widget, row, col)
            self.puzzle_widgets.append(puzzle_widget)

        self.puzzle_scroll_area.setWidget(self.all_puzzles_widget)

        # Best guess
        self.best_guess_widget = QtWidgets.QWidget()
        self.best_guess_widget.setLayout(QtWidgets.QVBoxLayout())
        splitter.addWidget(self.best_guess_widget)

        self.get_best_guess_button = QtWidgets.QPushButton("Get best guesses")
        self.get_best_guess_button.clicked.connect(self.get_best_guess)
        self.best_guess_widget.layout().addWidget(self.get_best_guess_button)

        self.best_guess_label = QtWidgets.QLabel(f"Best guess: {self.best_guess}")
        self.best_guess_widget.layout().addWidget(self.best_guess_label)

        self.use_best_guess_button = QtWidgets.QPushButton("Use best guess")
        self.use_best_guess_button.clicked.connect(self.use_best_guess)
        self.best_guess_widget.layout().addWidget(self.use_best_guess_button)

        self.best_guess_widget.layout().addStretch()

        self.progress_dialog: Optional[QtWidgets.QProgressDialog] = None

    def resizeEvent(self, event):
        """Override resize event."""
        super().resizeEvent(event)
        self.relayout_puzzles()

    def relayout_puzzles(self):
        """Lay out puzzles to fit available width."""
        for i in reversed(range(self.all_puzzles_layout.count())):
            widget = self.all_puzzles_layout.itemAt(i).widget()
            self.all_puzzles_layout.removeWidget(widget)

        if not self.puzzle_widgets:
            return

        available_width = self.puzzle_scroll_area.viewport().width()
        sample_widget = self.puzzle_widgets[0]
        widget_width = sample_widget.sizeHint().width() + self.all_puzzles_layout.spacing()
        if widget_width == 0:
            widget_width = 150

        max_cols = max(1, available_width // widget_width)

        for index, widget in enumerate(self.puzzle_widgets):
            row = index // max_cols
            col = index % max_cols
            self.all_puzzles_layout.addWidget(widget, row, col)

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

        self.letters_typed += 1

    def _handle_backspace(self):
        """Handle backspace input."""
        for puzzle_widget in self.puzzle_widgets:
            puzzle_widget.delete_letter()

        self.letters_typed -= 1

    def _handle_enter(self):
        """Handle enter input."""
        for puzzle_widget in self.puzzle_widgets:
            puzzle_widget.handle_enter()

        if self.letters_typed == 5:
            self.letters_typed = 0
            if not self.is_first_word_guessed:
                self.is_first_word_guessed = True

    def use_best_guess(self):
        """Enter the best guess in each puzzle."""
        for letter in self.best_guess:
            for puzzle_widget in self.puzzle_widgets:
                puzzle_widget.type_letter(letter)

        self.letters_typed = 5

    def get_best_guess(self):
        """Get the best guess for the given game state."""
        if self.letters_typed != 0 or not self.is_first_word_guessed:
            return

        self.cancel_flag.clear()

        self.remaining_tasks = 8
        self.progress_dialog = QtWidgets.QProgressDialog(
            "",
            "Cancel",
            0,
            self.remaining_tasks + 1,
            self,
        )
        self.progress_dialog.setWindowTitle("Getting best guess...")
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        self.progress_dialog.setValue(0)
        self.progress_dialog.canceled.connect(self.cancel_tasks)
        self.progress_dialog.show()

        for i in range(8):
            puzzle = self.puzzles[i]
            puzzle_widget = self.puzzle_widgets[i]
            thread_worker = ThreadWorker(
                fn=puzzle.make_guess,
                word=puzzle_widget.word,
                result=puzzle_widget.result,
                cancel_flag=self.cancel_flag,
            )
            thread_worker.signals.result.connect(self._on_make_guess_done)
            self.threadpool.start(thread_worker)

    def _on_make_guess_done(self):
        """Handle a guess thread worker finishing.

        Once all puzzle guess workers finish, start the get_best_guess_multiple_puzzles worker.
        """
        if self.cancel_flag.is_set():
            return

        self.remaining_tasks -= 1
        done = 8 - self.remaining_tasks
        if self.progress_dialog:
            self.progress_dialog.setValue(done)

        if self.remaining_tasks == 0:
            if self.progress_dialog:
                self.progress_dialog.setValue(8)
            for i in range(8):
                puzzle = self.puzzles[i]
                puzzle_widget = self.puzzle_widgets[i]
                if puzzle.is_solved:
                    puzzle_widget.is_solved = True
            puzzles = [p for p in self.puzzles if not p.is_solved]
            thread_worker = ThreadWorker(
                fn=get_best_guess_multiple_puzzles,
                puzzles=puzzles,
            )
            thread_worker.signals.result.connect(self._on_get_best_guess_done)
            self.threadpool.start(thread_worker)

    def _on_get_best_guess_done(self, best_guess: str):
        """Handle the get_best_guess_multiple_puzzles thread worker finishing.

        Args:
            best_guess (str): The best guess returned by the function
        """
        if self.cancel_flag.is_set():
            return

        if self.progress_dialog:
            self.progress_dialog.close()
        self.best_guess = best_guess
        self.best_guess_label.setText(f"Best guess: {self.best_guess}")

    def cancel_tasks(self):
        """Cancel any running tasks."""
        print("Cancelling tasks")
        self.cancel_flag.set()
        if self.progress_dialog:
            self.progress_dialog.cancel()
