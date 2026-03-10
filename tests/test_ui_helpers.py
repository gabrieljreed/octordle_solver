import pytest
from PySide6 import QtCore, QtTest

from octordle_solver.solver import PossibilityState
from octordle_solver.ui.helpers import (
    Color,
    LetterWidget,
    LIGHT_TILE_BORDER_COLOR,
    DARK_TILE_BORDER_COLOR,
    DARK_TILE_WHITE_BACKGROUND_COLOR,
    LIGHT_TILE_WHITE_TEXT_COLOR,
    DARK_TILE_WHITE_TEXT_COLOR,
)


class TestLetterWidget:
    def test_init(self, qtbot):
        widget = LetterWidget()
        qtbot.addWidget(widget)

        assert widget.current_color == Color.WHITE
        assert widget.text() == ""
        assert not widget.letter_is_set

    def test_init_light_mode_uses_light_white_tile_style(self, qtbot, mocker):
        mocker.patch("octordle_solver.ui.helpers.darkdetect.isDark", return_value=False)

        widget = LetterWidget()
        qtbot.addWidget(widget)

        style = widget.styleSheet()
        assert f"border: 2px solid {LIGHT_TILE_BORDER_COLOR};" in style
        assert f"background-color: #{Color.WHITE.value};" in style
        assert f"color: {LIGHT_TILE_WHITE_TEXT_COLOR};" in style

    def test_init_dark_mode_uses_dark_white_tile_style(self, qtbot, mocker):
        mocker.patch("octordle_solver.ui.helpers.darkdetect.isDark", return_value=True)

        widget = LetterWidget()
        qtbot.addWidget(widget)

        style = widget.styleSheet()
        assert f"border: 2px solid {DARK_TILE_BORDER_COLOR};" in style
        assert f"background-color: {DARK_TILE_WHITE_BACKGROUND_COLOR};" in style
        assert f"color: {DARK_TILE_WHITE_TEXT_COLOR};" in style

    def test_mouse_press(self, qtbot, mocker):
        widget = LetterWidget()
        qtbot.addWidget(widget)

        cycle_color_mock = mocker.patch.object(widget, "cycle_color")

        QtTest.QTest.mouseClick(widget, QtCore.Qt.RightButton)
        cycle_color_mock.assert_not_called()

        QtTest.QTest.mouseClick(widget, QtCore.Qt.LeftButton)
        cycle_color_mock.assert_called_once()

    def test_cycle_color(self, qtbot):
        widget = LetterWidget()
        qtbot.addWidget(widget)

        widget.letter_is_set = True
        widget.set_color(Color.GRAY)
        assert widget.current_color == Color.GRAY

        widget.cycle_color()
        assert widget.current_color == Color.YELLOW

        widget.cycle_color()
        assert widget.current_color == Color.GREEN

        widget.cycle_color()
        assert widget.current_color == Color.GRAY

    def test_cycle_color_letter_not_set(self, qtbot):
        widget = LetterWidget()
        qtbot.addWidget(widget)

        assert widget.current_color == Color.WHITE
        widget.cycle_color()
        assert widget.current_color == Color.WHITE

    @pytest.mark.parametrize(
        "color, state",
        [
            [Color.WHITE, PossibilityState.INVALID],
            [Color.GREEN, PossibilityState.CORRECT],
            [Color.YELLOW, PossibilityState.MISPLACED],
            [Color.GRAY, PossibilityState.INCORRECT],
        ],
    )
    def test_state(self, qtbot, color, state):
        widget = LetterWidget()
        qtbot.addWidget(widget)

        widget.set_color(color)
        assert widget.state == state

    def test_reset(self, qtbot):
        widget = LetterWidget()
        qtbot.addWidget(widget)

        widget.letter_is_set = True
        widget.setText("A")
        widget.set_color(Color.GREEN)

        widget.reset()

        assert widget.text() == ""
        assert widget.current_color == Color.WHITE
        assert not widget.letter_is_set
