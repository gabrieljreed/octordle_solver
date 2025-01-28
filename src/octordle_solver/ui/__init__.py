from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
from functools import partial

from octordle_solver.generate_groups import get_all_answer_possibilities, get_best_second_guess

from ..solver import filter_words
from ..dictionary import dictionary
from .threading import ThreadWorker

from enum import Enum


class Color(Enum):
    """Store the wordle colors."""

    YELLOW = "c3ae55"
    GREEN = "69ab64"
    GRAY = "767a7d"
    WHITE = "ffffff"


class LetterWidget(QtWidgets.QLabel):
    """Custom label to hold a letter."""

    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet(
            """
            QLabel {
                border: 2px solid #D3D6DA;
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                background-color: white;
            }
        """
        )
        self.setAlignment(Qt.AlignCenter)

        self.letter_is_set = False
        self.current_color = Color.WHITE

    def mousePressEvent(self, event):
        """Handle the mouse press event."""
        if event.button() == Qt.LeftButton:
            self.cycle_color()

    def cycle_color(self):
        """Cycle the color so the user can set the status."""
        if not self.letter_is_set:
            return

        colors = [Color.GRAY, Color.YELLOW, Color.GREEN]
        current_index = colors.index(self.current_color)
        next_index = (current_index + 1) % len(colors)  # Get the next color index
        self.set_color(colors[next_index])

    def set_color(self, color: Color):
        """Set the specified color.

        Args:
            color (Color): The color to set.
        """
        self.current_color = color
        self.setStyleSheet(
            f"""
            QLabel {{
                border: 2px solid #D3D6DA;
                color: white;
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                background-color: #{self.current_color.value};
            }}
        """
        )


class WordleSolver(QtWidgets.QMainWindow):
    """UI to solve Wordle puzzles."""

    def __init__(self):
        """Initialize the window."""
        super().__init__()
        self.setWindowTitle("Wordle Solver")
        self.setFixedSize(1000, 600)

        # Main container
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(layout)

        # Wordle grid
        self.grid_layout = QtWidgets.QGridLayout()
        layout.addLayout(self.grid_layout)
        self._create_grid()

        # Best guesses
        self.best_guess_widget = QtWidgets.QWidget()
        self.best_guess_widget.setLayout(QtWidgets.QVBoxLayout())
        layout.addWidget(self.best_guess_widget)

        self.get_best_guess_button = QtWidgets.QPushButton("Get best guesses")
        self.get_best_guess_button.clicked.connect(self.get_best_guesses)
        self.best_guess_widget.layout().addWidget(self.get_best_guess_button)

        self.best_guess_widget.layout().addWidget(QtWidgets.QLabel("Best guesses"))

        self.best_guess_list = QtWidgets.QListWidget()
        self.best_guess_list.addItem("CRANE")
        self.best_guess_list.itemSelectionChanged.connect(self.update_groups_widgets)
        self.best_guess_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.best_guess_list.customContextMenuRequested.connect(self.show_best_guess_context_menu)
        self.best_guess_list.itemDoubleClicked.connect(self.handle_best_guess_double_click)
        self.best_guess_widget.layout().addWidget(self.best_guess_list)

        # Groups
        self.groups_widget = QtWidgets.QWidget()
        self.groups_widget.setLayout(QtWidgets.QVBoxLayout())
        layout.addWidget(self.groups_widget)

        self.groups_widget.layout().addWidget(QtWidgets.QLabel("Group Information"))

        self.total_groups_label = QtWidgets.QLabel("Total Groups: 0")
        self.groups_widget.layout().addWidget(self.total_groups_label)
        self.largest_group_label = QtWidgets.QLabel("Largest Group Size: 0")
        self.groups_widget.layout().addWidget(self.largest_group_label)
        self.average_group_label = QtWidgets.QLabel("Average Group Size: 0")
        self.groups_widget.layout().addWidget(self.average_group_label)

        self.groups_tree_widget = QtWidgets.QTreeWidget()
        self.groups_tree_widget.header().hide()
        self.groups_widget.layout().addWidget(self.groups_tree_widget)

        # Remaining words
        self.remaining_words_widget = QtWidgets.QWidget()
        self.remaining_words_widget.setLayout(QtWidgets.QVBoxLayout())
        layout.addWidget(self.remaining_words_widget)

        self.remaining_words_label = QtWidgets.QLabel("(0) Remaining Word(s)")
        self.remaining_words_widget.layout().addWidget(self.remaining_words_label)

        self.remaining_words_list = QtWidgets.QListWidget()
        self.remaining_words_widget.layout().addWidget(self.remaining_words_list)

        # Setup menu
        file_menu = self.menuBar().addMenu("File")

        self.reset_action = QtGui.QAction("Reset", self)
        self.reset_action.triggered.connect(self.reset_game)
        file_menu.addAction(self.reset_action)

        self.help_action = QtGui.QAction("Help", self)
        file_menu.addAction(self.help_action)

        self.debug_action = QtGui.QAction("Debug", self)
        self.debug_action.triggered.connect(self.debug)
        file_menu.addAction(self.debug_action)

        # Setup variables
        self._current_row = 0
        self._current_col = 0

        self.guessed_word = ""
        self.remaining_words = dictionary.valid_answers.copy()
        self.valid_guesses = dictionary.valid_guesses.copy()
        self.correct_letters = ["", "", "", "", ""]
        self.misplaced_letters = []
        self.incorrect_letters = []
        self.possibilities = []

        self.computed_guesses = [False, False, False, False, False, False]

        self.update_remaining_words_widget()

        self.threadpool = QtCore.QThreadPool()
        self.original_style_sheet = self.styleSheet()

        self.setFocus()

    def reset_game(self):
        """Reset the game back to its initial state."""
        self.remaining_words = dictionary.valid_answers.copy()
        self.valid_guesses = dictionary.valid_guesses.copy()
        self.correct_letters = ["", "", "", "", ""]
        self.misplaced_letters = []
        self.incorrect_letters = []
        self.possibilities = []

        self._current_row = 0
        self._current_col = 0

        for i in range(5):
            for j in range(5):
                current_box = self.letter_boxes[i][j]
                current_box.setText("")
                current_box.set_color(Color.WHITE)
                current_box.letter_is_set = False

        self.best_guess_list.clear()
        self.groups_tree_widget.clear()

        self.update_remaining_words_widget()
        self.setFocus()

    def debug(self):
        print(f"{self._current_row = }")
        print(f"{self._current_col = }")

    def _create_grid(self):
        """Create the grid of letter boxes."""
        self.letter_boxes = []
        for row in range(6):
            row_boxes = []
            for col in range(5):
                label = LetterWidget()
                self.grid_layout.addWidget(label, row, col)
                row_boxes.append(label)
            self.letter_boxes.append(row_boxes)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() in range(Qt.Key_A, Qt.Key_Z + 1):
            self._handle_letter_input(event.text().upper())
        elif event.key() == Qt.Key_Backspace:
            self._handle_backspace()
        elif event.key() == Qt.Key_Return:
            self._handle_enter()

    def _handle_letter_input(self, letter):
        """Handle a letter input."""
        if self._current_row < 6 and self._current_col < 5:
            current_box = self.letter_boxes[self._current_row][self._current_col]
            current_box.setText(letter)
            self._current_col += 1

    def _handle_backspace(self):
        """Handle backspace to remove a letter."""
        if self._current_col > 0:
            self._current_col -= 1
            current_box = self.letter_boxes[self._current_row][self._current_col]
            current_box.setText("")

    def _handle_enter(self):
        """Handle enter to move to the next row if the word is valid."""
        if self._current_row > 6 or self._current_col != 5:
            print("Word is not complete")
            return

        word = ""
        for i in range(5):
            letter = self.letter_boxes[self._current_row][i].text()
            word += letter

        if word not in self.valid_guesses:
            print("Word is not valid, try again")
            return

        for i in range(5):
            current_box = self.letter_boxes[self._current_row][i]
            current_box.letter_is_set = True
            current_box.set_color(Color.GRAY)

        self._current_row += 1
        self._current_col = 0

    def _update_game_state(self):
        """Update the game state with the results of the given row."""
        word = ""
        for row in range(6):
            if row == self._current_row:
                break

            if self.computed_guesses[row]:
                continue

            for col in range(5):
                current_box = self.letter_boxes[row][col]
                letter = current_box.text()
                word += letter
                if current_box.current_color == Color.GRAY:
                    self.incorrect_letters.append(letter)
                elif current_box.current_color == Color.YELLOW:
                    self.misplaced_letters.append((letter, col))
                else:
                    self.correct_letters[col] = letter

                self.guessed_word = word

            self.computed_guesses[row] = True

    def update_remaining_words_widget(self):
        """Update the widgets with the remaining words."""
        self.remaining_words_list.clear()
        self.remaining_words_list.addItems(self.remaining_words)
        self.remaining_words_label.setText(f"{len(self.remaining_words)} Remaining Word(s)")

    def get_best_guesses(self):
        """Get the best guesses for the given game state.

        This function is threaded, and will call _on_get_answer_possibilities_finished when done.
        """
        if self._current_row == 0:
            return

        self._update_game_state()
        self.remaining_words = filter_words(
            self.remaining_words,
            self.correct_letters,
            self.misplaced_letters,
            self.incorrect_letters,
        )

        self.update_remaining_words_widget()
        self.best_guess_list.clear()
        self.groups_tree_widget.clear()

        # If it's the first guess, get the cached best second guess (if the first guess was "CRANE")
        if self._current_row == 1 and self.guessed_word == "CRANE":
            answer_possibility = []
            for i in range(5):
                current_box = self.letter_boxes[0][i]
                if current_box.current_color == Color.GREEN:
                    answer_possibility.append(0)
                elif current_box.current_color == Color.YELLOW:
                    answer_possibility.append(1)
                elif current_box.current_color == Color.GRAY:
                    answer_possibility.append(2)

            best_second_guess = get_best_second_guess(answer_possibility)
            if best_second_guess:
                self.best_guess_list.addItem(best_second_guess)

        thread_worker = ThreadWorker(
            fn=get_all_answer_possibilities,
            remaining_words=self.remaining_words,
            valid_guesses=self.valid_guesses,
        )
        thread_worker.signals.result.connect(self._on_get_answer_possibilities_finished)

        self.get_best_guess_button.setText("Calculating best guesses...")
        self.get_best_guess_button.setDisabled(True)
        self.original_style_sheet = self.styleSheet()

        self.threadpool.start(thread_worker)

    def _on_get_answer_possibilities_finished(self, possibilities):
        """Update the UI when the thread worker from get_best_guesses finishes."""
        self.possibilities = possibilities

        self.get_best_guess_button.setText("Get best guesses")
        self.get_best_guess_button.setDisabled(False)

        for possibility in self.possibilities:
            if not self.best_guess_list.findItems(possibility.word, Qt.MatchFlag.MatchExactly):
                self.best_guess_list.addItem(possibility.word)

    def update_groups_widgets(self):
        """Update the group widgets when the user picks an answer possibility."""
        if not self.possibilities:
            return

        word = self.best_guess_list.currentItem().text()
        index = self.best_guess_list.currentRow()
        groups = self.possibilities[index].groups

        def get_word_colors(possibility) -> list[str]:
            colors = []

            for result in possibility:
                if result == 2:
                    colors.append(Color.GRAY)
                elif result == 1:
                    colors.append(Color.YELLOW)
                elif result == 0:
                    colors.append(Color.GREEN)

            return colors

        def style_text(text, colors) -> str:
            styled_text = ""
            for letter, color in zip(text, colors):
                styled_text += f'<span style="color: #{color.value}; font-weight: bold;">{letter}</span>'
            return styled_text

        def create_colored_label(text, colors):
            """Create a QLabel with colored letters."""
            label = QtWidgets.QLabel()
            label.setText(style_text(text, colors))
            label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            return label

        self.groups_tree_widget.clear()
        for group in groups:
            item = QtWidgets.QTreeWidgetItem(self.groups_tree_widget)
            colors = get_word_colors(group.possibility)
            self.groups_tree_widget.setItemWidget(item, 0, create_colored_label(word, colors))
            self.groups_tree_widget.addTopLevelItem(item)
            for sorted_word in group.words:
                child_item = QtWidgets.QTreeWidgetItem()
                child_item.setText(0, sorted_word)
                item.addChild(child_item)
            item.setExpanded(True)

        total_groups = len(groups)
        largest_group = max(len(group.words) for group in groups)
        sum_groups = sum(len(group.words) for group in groups)
        average_size = sum_groups / total_groups

        self.total_groups_label.setText(f"Total Groups: {total_groups}")
        self.largest_group_label.setText(f"Largest Group Size: {largest_group}")
        self.average_group_label.setText(f"Average Group Size: {average_size:.1f}")

        self.setFocus()

    def show_best_guess_context_menu(self, point):
        """Show a context menu for the best guess list widget."""
        menu = QtWidgets.QMenu(self)

        current_word = self.best_guess_list.currentItem().text()

        use_guess_action = QtGui.QAction(f"Use {current_word} as next guess")
        use_guess_action.triggered.connect(partial(self.use_selected_guess, current_word))
        menu.addAction(use_guess_action)

        menu.exec(self.best_guess_list.mapToGlobal(point))

    def handle_best_guess_double_click(self, item):
        self.use_selected_guess(item.text())

    def use_selected_guess(self, guess):
        """Use the selected word from the best guess list as the next guess."""
        for letter in guess:
            current_box = self.letter_boxes[self._current_row][self._current_col]
            current_box.setText(letter)
            self._current_col += 1
