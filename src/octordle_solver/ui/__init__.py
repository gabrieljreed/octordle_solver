from PySide6 import QtWidgets
from PySide6.QtCore import QEvent, QObject, Qt

from ..solver import filter_words
from ..dictionary import Dictionary


class LetterWidget(QtWidgets.QLabel):
    def __init__(self, parent=None):
        """Initialize the widget."""
        super().__init__()
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
        self.current_color = "white"

    def mousePressEvent(self, event):
        """Handle the mouse press event."""
        if event.button() == Qt.LeftButton:
            self.cycle_color()

    def cycle_color(self):
        """Cycle the color so the user can set the status."""
        if not self.letter_is_set:
            return

        colors = ["gray", "yellow", "green"]
        current_index = colors.index(self.current_color)
        next_index = (current_index + 1) % len(colors)  # Get the next color index
        self.set_color(colors[next_index])

    def set_color(self, color: str):
        self.current_color = color
        self.setStyleSheet(
            f"""
            QLabel {{
                border: 2px solid #D3D6DA;
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                background-color: {self.current_color};
            }}
        """
        )


class WordleClone(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wordle Clone")
        self.setFixedSize(500, 600)

        # Main container
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(layout)

        # Wordle grid
        self.grid_layout = QtWidgets.QGridLayout()
        layout.addLayout(self.grid_layout)
        self._create_grid()

        # Remaining words list
        self.remaining_words_widget = QtWidgets.QWidget()
        self.remaining_words_widget.setLayout(QtWidgets.QVBoxLayout())

        self.remaining_words_label = QtWidgets.QLabel("(0) Remaining Words")
        self.remaining_words_widget.layout().addWidget(self.remaining_words_label)

        self.generate_remaining_words_button = QtWidgets.QPushButton("Get remaining words")
        self.generate_remaining_words_button.clicked.connect(self.get_remaining_words)
        self.remaining_words_widget.layout().addWidget(self.generate_remaining_words_button)

        self.remaining_words_list = QtWidgets.QListWidget()
        self.remaining_words_widget.layout().addWidget(self.remaining_words_list)
        layout.addWidget(self.remaining_words_widget)

        self._current_row = 0
        self._current_col = 0

        self.setFocus()

        self.remaining_words = Dictionary().words.copy()
        self.correct_letters = ["", "", "", "", ""]
        self.misplaced_letters = []
        self.incorrect_letters = []

        self.update_remaining_words_widget()

    def _create_grid(self):
        self.letter_boxes = []  # Store QLabel references
        for row in range(6):  # 6 rows
            row_boxes = []
            for col in range(5):  # 5 columns
                label = LetterWidget()
                self.grid_layout.addWidget(label, row, col)
                row_boxes.append(label)
            self.letter_boxes.append(row_boxes)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() in range(Qt.Key_A, Qt.Key_Z + 1):  # Letter keys
            self._handle_letter_input(event.text().upper())
        elif event.key() == Qt.Key_Backspace:  # Backspace key
            self._handle_backspace()
        elif event.key() == Qt.Key_Return:
            self._handle_enter()

    def _handle_letter_input(self, letter):
        """Handle a letter input."""
        if self._current_row < 6 and self._current_col < 5:  # Ensure within bounds
            current_box = self.letter_boxes[self._current_row][self._current_col]
            current_box.setText(letter)
            self._current_col += 1  # Move to the next column

    def _handle_backspace(self):
        """Handle backspace to remove a letter."""
        if self._current_col > 0:  # If there's a letter to remove
            self._current_col -= 1  # Move back a column
            current_box = self.letter_boxes[self._current_row][self._current_col]
            current_box.setText("")  # Clear the box

    def _handle_enter(self):
        """Handle enter to move to the next row."""
        if self._current_row < 6 and self._current_col == 5:
            for i in range(5):
                current_box = self.letter_boxes[self._current_row][i]
                current_box.letter_is_set = True
                current_box.set_color("gray")

            self._current_row += 1
            self._current_col = 0

        else:
            print("Word is not complete")

    def _update_game_state(self, row: int):
        """Update the game state with the results of the given row."""
        if row >= self._current_row:
            return

        for i in range(5):
            current_box = self.letter_boxes[row][i]
            letter = current_box.text()
            if current_box.current_color == "gray":
                self.incorrect_letters.append(letter)
            elif current_box.current_color == "yellow":
                self.misplaced_letters.append((letter, i))
            else:
                self.correct_letters[i] = letter

        print(self.correct_letters)
        print(self.misplaced_letters)
        print(self.incorrect_letters)

    def update_remaining_words_widget(self):
        """Update the widgets with the remaining words."""
        self.remaining_words_list.clear()
        self.remaining_words_list.addItems(self.remaining_words)
        self.remaining_words_label.setText(f"{len(self.remaining_words)} Remaining Words")

    def get_remaining_words(self):
        print("Getting remaining words")

        if self._current_row == 0:
            return

        self._update_game_state(self._current_row - 1)
        self.remaining_words = filter_words(
            self.remaining_words,
            self.correct_letters,
            self.misplaced_letters,
            self.incorrect_letters,
        )

        self.update_remaining_words_widget()
