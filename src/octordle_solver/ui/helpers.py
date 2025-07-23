"""Helper UI classes and functions."""

from enum import Enum

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from ..solver import PossibilityState


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
