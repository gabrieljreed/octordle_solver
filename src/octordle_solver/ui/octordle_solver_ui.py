"""UI for solving Octordle puzzles."""

import threading
from typing import Any, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from ..constants import STARTING_GUESS
from ..solver import PossibilityState, Puzzle, get_best_guess_multiple_puzzles
from .helpers import Color, LetterWidget
from .threads import ThreadWorker


class WordleGridWidget(QtWidgets.QWidget):
    """Widget representing a single Wordle grid."""

    def __init__(self, parent: Any = None, num_rows: int = 13):
        """Initialize the widget."""
        super().__init__(parent)

        self._current_row = 0
        self._current_col = 0

        self.num_rows = num_rows
        self.is_solved = False

        self.remaining_words: list[str] = []

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.header_widget = QtWidgets.QWidget()
        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_widget.setLayout(self.header_layout)
        self.main_layout.addWidget(self.header_widget)

        self.label = QtWidgets.QLabel("Puzzle")
        self.header_layout.addWidget(self.label)

        self.header_layout.addStretch()

        self.remaining_words_button = QtWidgets.QPushButton("0 Remaining Words")
        self.remaining_words_button.clicked.connect(self.show_remaining_words)
        self.header_layout.addWidget(self.remaining_words_button)

        self.grid_layout = QtWidgets.QGridLayout()
        self.main_layout.addLayout(self.grid_layout)

        self.letter_boxes: list[list[LetterWidget]] = []
        for row in range(self.num_rows):
            row_boxes: list[LetterWidget] = []
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
            return

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

    def set_title(self, title: str):
        """Set the title of the puzzle widget.

        Args:
            title (str): Title of the widget
        """
        self.label.setText(title)

    def set_remaining_words(self, remaining_words: list[str]):
        """Set the remaining words and update the UI."""
        self.remaining_words = remaining_words
        words_text = "Word" if len(remaining_words) == 1 else "Words"
        self.remaining_words_button.setText(f"{len(self.remaining_words)} Remaining {words_text}")

    def show_remaining_words(self):
        """Display a dialog to show the remaining words."""
        remaining_words_dialog = RemainingWordsDialog(parent=self, words=self.remaining_words)
        remaining_words_dialog.show()

    def reset_game(self):
        """Reset the widget to its original state."""
        for row in self.letter_boxes:
            for letter_widget in row:
                letter_widget.reset()

        self._current_row = 0
        self._current_col = 0


class OctordleSolver(QtWidgets.QMainWindow):
    """UI for solving Octordle puzzles."""

    def __init__(self):
        """Initialize the widget."""
        super().__init__()

        self.num_puzzles = 8
        self.num_guesses = 13

        self.puzzles = [Puzzle() for _ in range(self.num_puzzles)]

        self.best_guess = STARTING_GUESS

        self.threadpool = QtCore.QThreadPool()
        self.cancel_flag = threading.Event()
        self.remaining_tasks = 0

        self.letters_typed = 0
        self.is_first_word_guessed = False

        self.setup_ui()
        self.setup_menu()

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
        self.create_puzzle_widgets()

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

        self.update_puzzle_widgets()

    def create_puzzle_widgets(self):
        """Create puzzle widgets for the number of puzzles selected."""
        self.puzzle_widgets: list[WordleGridWidget] = []
        for i in range(self.num_puzzles):
            puzzle_widget = WordleGridWidget(num_rows=self.num_guesses)
            puzzle_widget.set_title(f"Puzzle {i + 1}")
            row = i // (self.num_puzzles // 2)
            col = i % (self.num_puzzles // 2)
            self.all_puzzles_layout.addWidget(puzzle_widget, row, col)
            self.puzzle_widgets.append(puzzle_widget)

        self.relayout_puzzles()

    def clear_puzzle_widgets(self):
        """Remove all puzzle widgets from the layout."""
        while self.all_puzzles_layout.count():
            item = self.all_puzzles_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def setup_menu(self):
        """Set up the menu bar."""
        file_menu = self.menuBar().addMenu("File")

        self.reset_action = QtGui.QAction("Reset", self)
        self.reset_action.triggered.connect(self.reset_game)
        file_menu.addAction(self.reset_action)

        self.puzzle_settings_action = QtGui.QAction("Puzzle Settings", self)
        self.puzzle_settings_action.triggered.connect(self.open_puzzle_settings)
        file_menu.addAction(self.puzzle_settings_action)

    def update_puzzle_widgets(self):
        """Update the remaining words in each puzzle widget."""
        for i in range(self.num_puzzles):
            puzzle = self.puzzles[i]
            puzzle_widget = self.puzzle_widgets[i]
            puzzle_widget.set_remaining_words(puzzle.remaining_words)

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

        self.remaining_tasks = self.num_puzzles
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

        for i in range(self.num_puzzles):
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
        done = self.num_puzzles - self.remaining_tasks
        if self.progress_dialog:
            self.progress_dialog.setValue(done)

        if self.remaining_tasks == 0:
            if self.progress_dialog:
                self.progress_dialog.setValue(self.num_puzzles)
            for i in range(self.num_puzzles):
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

        self.update_puzzle_widgets()

    def cancel_tasks(self):
        """Cancel any running tasks."""
        self.cancel_flag.set()
        if self.progress_dialog:
            self.progress_dialog.cancel()

    def reset_game(self):
        """Reset the game."""
        for puzzle_widget in self.puzzle_widgets:
            puzzle_widget.reset_game()

        for puzzle in self.puzzles:
            puzzle.reset()

        self.best_guess = STARTING_GUESS
        self.letters_typed = 0
        self.is_first_word_guessed = False

        self.update_puzzle_widgets()

    def open_puzzle_settings(self):
        """Launch a dialog to edit puzzle settings."""
        dialog = PuzzleSettingsDialog(self.num_puzzles, self.num_guesses)
        if not dialog.exec_():
            return

        self.num_puzzles = dialog.num_puzzles
        self.num_guesses = dialog.num_guesses

        self.puzzles = [Puzzle() for _ in range(self.num_puzzles)]

        self.clear_puzzle_widgets()
        self.create_puzzle_widgets()
        self.update_puzzle_widgets()


class RemainingWordsDialog(QtWidgets.QDialog):
    """Dialog to display remaining words."""

    def __init__(self, words: list[str], parent: Any = None):
        """Dialog to display remaining words.

        Args:
            words (list[str]): List of remaining words to display
            parent (Any): Parent of the widget
        """
        super().__init__(parent)
        self.words = words

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("Remaining Words")

        layout = QtWidgets.QVBoxLayout(self)

        self.words_list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.words_list_widget)
        self.words_list_widget.addItems(self.words)


class PuzzleSettingsDialog(QtWidgets.QDialog):
    """Dialog to display puzzle settings."""

    def __init__(self, num_puzzles: int, num_guesses: int, parent: Any = None):
        """Dialog to display puzzle settings."""
        super().__init__(parent)

        self._num_puzzles = num_puzzles
        self._num_guesses = num_guesses

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("Puzzle Settings")

        layout = QtWidgets.QVBoxLayout(self)

        int_validator = QtGui.QIntValidator(1, 1000, self)

        # Number of puzzles
        puzzles_layout = QtWidgets.QHBoxLayout()
        puzzles_label = QtWidgets.QLabel("Number of puzzles:")
        self.puzzles_edit = QtWidgets.QLineEdit(str(self._num_puzzles))
        self.puzzles_edit.setValidator(int_validator)
        puzzles_layout.addWidget(puzzles_label)
        puzzles_layout.addWidget(self.puzzles_edit)
        layout.addLayout(puzzles_layout)

        # Number of guesses
        guesses_layout = QtWidgets.QHBoxLayout()
        guesses_label = QtWidgets.QLabel("Number of guesses:")
        self.guesses_edit = QtWidgets.QLineEdit(str(self._num_guesses))
        self.guesses_edit.setValidator(int_validator)
        guesses_layout.addWidget(guesses_label)
        guesses_layout.addWidget(self.guesses_edit)
        layout.addLayout(guesses_layout)

        # Ok / Cancel buttons
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    @property
    def num_puzzles(self) -> int:
        """Get the number of puzzles entered."""
        return int(self.puzzles_edit.text())

    @property
    def num_guesses(self) -> int:
        """Get the number of guesses entered."""
        return int(self.guesses_edit.text())
