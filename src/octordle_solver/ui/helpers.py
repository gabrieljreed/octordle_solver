"""Helper UI classes and functions."""

from enum import Enum

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from ..solver import PossibilityState
from typing import Any


class Color(Enum):
    """Store the wordle colors."""

    YELLOW = "c3ae55"
    GREEN = "69ab64"
    GRAY = "767a7d"
    WHITE = "ffffff"


class LetterWidget(QtWidgets.QLabel):
    """Custom label to hold a letter."""

    def __init__(self, parent=None, dimensions=None):
        """Initialize the widget."""
        super().__init__(parent)
        if not dimensions:
            dimensions = [60, 60]
        self.setFixedSize(*dimensions)
        # TODO: Fix this for dark mode and detect when to use it
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
        text_color = "white"
        if color == Color.WHITE:
            text_color = "black"
        self.setStyleSheet(
            f"""
            QLabel {{
                border: 2px solid #D3D6DA;
                color: {text_color};
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                background-color: #{self.current_color.value};
            }}
        """
        )

    @property
    def state(self) -> PossibilityState:
        """Return the state of the tile."""
        if self.current_color == Color.GREEN:
            return PossibilityState.CORRECT
        elif self.current_color == Color.YELLOW:
            return PossibilityState.MISPLACED
        elif self.current_color == Color.GRAY:
            return PossibilityState.INCORRECT
        return PossibilityState.INVALID

    def reset(self):
        """Reset the tile to its original state."""
        self.set_color(Color.WHITE)
        self.setText("")
        self.letter_is_set = False


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

        # self.remaining_words_button = QtWidgets.QPushButton("0 Remaining Words")
        # self.remaining_words_button.clicked.connect(self.show_remaining_words)
        # self.header_layout.addWidget(self.remaining_words_button)

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

    # def show_remaining_words(self):
    #     """Display a dialog to show the remaining words."""
    #     remaining_words_dialog = RemainingWordsDialog(parent=self, words=self.remaining_words)
    #     remaining_words_dialog.show()

    def reset_game(self):
        """Reset the widget to its original state."""
        for row in self.letter_boxes:
            for letter_widget in row:
                letter_widget.reset()

        self._current_row = 0
        self._current_col = 0
