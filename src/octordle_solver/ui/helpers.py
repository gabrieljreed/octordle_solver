"""Helper UI classes and functions."""

from enum import Enum
import darkdetect

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt

from typing import Union
from ..solver import PossibilityState

LIGHT_TILE_BORDER_COLOR = "#D3D6DA"
DARK_TILE_BORDER_COLOR = "#565758"
DARK_TILE_WHITE_BACKGROUND_COLOR = "#191a1c"
LIGHT_TILE_WHITE_TEXT_COLOR = "black"
DARK_TILE_WHITE_TEXT_COLOR = "white"
DEFAULT_TILE_TEXT_COLOR = "white"


class Color(Enum):
    """Store the wordle colors."""

    YELLOW = "c3ae55"
    GREEN = "69ab64"
    GRAY = "767a7d"
    WHITE = "ffffff"


class LetterWidget(QtWidgets.QLabel):
    """Custom label to hold a letter."""

    def __init__(self, parent=None, dimensions=None, is_dark_mode=None):
        """Initialize the widget."""
        super().__init__(parent)
        if not dimensions:
            dimensions = [60, 60]
        self.setFixedSize(*dimensions)
        self._is_dark_mode = bool(darkdetect.isDark()) if is_dark_mode is None else bool(is_dark_mode)
        self.setAlignment(Qt.AlignCenter)

        self.letter_is_set = False
        self.current_color = Color.WHITE
        self.set_color(Color.WHITE)

    def _get_stylesheet(self, color: Color, text_color: str) -> str:
        """Build the label stylesheet based on the color and current theme."""
        border_color = LIGHT_TILE_BORDER_COLOR
        background_color = f"#{color.value}"
        if self._is_dark_mode and color == Color.WHITE:
            border_color = DARK_TILE_BORDER_COLOR
            background_color = DARK_TILE_WHITE_BACKGROUND_COLOR

        return f"""
            QLabel {{
                border: 2px solid {border_color};
                color: {text_color};
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                background-color: {background_color};
            }}
        """

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
        text_color = DEFAULT_TILE_TEXT_COLOR
        if color == Color.WHITE:
            text_color = DARK_TILE_WHITE_TEXT_COLOR if self._is_dark_mode else LIGHT_TILE_WHITE_TEXT_COLOR
        self.setStyleSheet(self._get_stylesheet(color, text_color))

    def set_dark_mode(self, is_dark_mode: bool) -> None:
        """Set dark mode state and refresh current tile styling."""
        self._is_dark_mode = is_dark_mode
        self.set_color(self.current_color)

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


def get_word_colors(possibility: Union[list[int], str]) -> list[Color]:
    """Get the colors for a given answer possibility."""
    colors = []
    for result in possibility:
        if result in [2, "N"]:
            colors.append(Color.GRAY)
        elif result in [1, "M"]:
            colors.append(Color.YELLOW)
        elif result in [0, "Y"]:
            colors.append(Color.GREEN)
    return colors


def style_text(text: str, colors: list[Color]) -> str:
    """Style the text with the given colors."""
    styled_text = ""
    for letter, color in zip(text, colors):
        styled_text += f'<span style="color: #{color.value}; font-weight: bold;">{letter}</span>'
    return styled_text


def create_colored_label(text: str, colors: list[Color]) -> QtWidgets.QLabel:
    """Create a QLabel with colored letters."""
    label = QtWidgets.QLabel()
    label.setText(style_text(text, colors))
    label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    return label
