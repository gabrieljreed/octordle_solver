from octordle_solver.ui.helpers import Color
from octordle_solver.ui.octordle_solver_ui import (
    PuzzleSettingsDialog,
    RemainingWordsDialog,
    WordleGridWidget,
)


class TestWordleGridWidget:
    def test_init(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        assert not widget.is_solved
        assert widget.num_rows == 13
        assert len(widget.letter_boxes) == 13
        assert widget.remaining_words_button.text() == "0 Remaining Words"

        assert widget._current_row == 0
        assert widget._current_col == 0

    def test_type_letter(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        widget.type_letter("A")

        assert widget._current_row == 0
        assert widget._current_col == 1
        assert widget.letter_boxes[0][0].text() == "A"

    def test_type_letter_solved(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        widget.is_solved = True

        widget.type_letter("A")

        assert widget._current_row == 0
        assert widget._current_col == 0
        assert widget.letter_boxes[0][0].text() == ""

    def test_delete_letter(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        widget.type_letter("A")

        assert widget._current_row == 0
        assert widget._current_col == 1
        assert widget.letter_boxes[0][0].text() == "A"

        widget.delete_letter()

        assert widget._current_row == 0
        assert widget._current_col == 0
        assert widget.letter_boxes[0][0].text() == ""

    def test_delete_letter_solved(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        widget.type_letter("A")

        assert widget._current_row == 0
        assert widget._current_col == 1
        assert widget.letter_boxes[0][0].text() == "A"

        widget.is_solved = True

        widget.delete_letter()

        assert widget._current_row == 0
        assert widget._current_col == 1
        assert widget.letter_boxes[0][0].text() == "A"

    def test_delete_letter_no_letters_typed(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        widget.delete_letter()

        assert widget._current_row == 0
        assert widget._current_col == 0
        assert widget.letter_boxes[0][0].text() == ""

    def test_handle_enter(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        for letter in "CRANE":
            widget.type_letter(letter)

        widget.handle_enter()

        assert widget._current_row == 1
        assert widget._current_col == 0
        assert widget.word == "CRANE"

        row = widget.letter_boxes[0]
        for i in range(5):
            assert row[i].letter_is_set
            assert row[i].current_color == Color.GRAY

    def test_handle_enter_solved(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        for letter in "CRANE":
            widget.type_letter(letter)

        widget.is_solved = True

        widget.handle_enter()

        assert widget._current_row == 0
        assert widget._current_col == 5
        assert widget.word == ""

    def test_handle_enter_word_not_complete(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        for letter in "CRA":
            widget.type_letter(letter)

        widget.handle_enter()

        assert widget._current_row == 0
        assert widget._current_col == 3
        assert widget.word == ""

    def test_result(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        for letter in "CRANE":
            widget.type_letter(letter)

        widget.handle_enter()

        assert widget.result == "NNNNN"

        row = widget.letter_boxes[0]
        row[0].cycle_color()
        row[0].cycle_color()
        row[1].cycle_color()
        assert widget.result == "YMNNN"

    def test_set_title(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        widget.set_title("Hello World")

        assert widget.label.text() == "Hello World"

    def test_set_remaining_words(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        widget.set_remaining_words(["CRANE", "SLATE"])
        assert widget.remaining_words_button.text() == "2 Remaining Words"

        widget.set_remaining_words(["CRANE"])
        assert widget.remaining_words_button.text() == "1 Remaining Word"

    def test_show_remaining_words(self, qtbot, mocker):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        remaining_words = ["CRANE", "SLATE"]
        widget.set_remaining_words(remaining_words)
        mock_dialog = mocker.patch("octordle_solver.ui.octordle_solver_ui.RemainingWordsDialog")

        widget.show_remaining_words()

        mock_dialog.assert_called_once_with(parent=widget, words=remaining_words)

    def test_reset(self, qtbot):
        widget = WordleGridWidget()
        qtbot.addWidget(widget)

        for letter in "CRANE":
            widget.type_letter(letter)

        widget.handle_enter()

        row = widget.letter_boxes[0]
        row[0].cycle_color()
        row[0].cycle_color()
        row[1].cycle_color()

        assert widget._current_row == 1
        assert widget._current_col == 0

        assert row[0].current_color == Color.GREEN
        assert row[1].current_color == Color.YELLOW
        assert row[2].current_color == Color.GRAY
        assert row[3].current_color == Color.GRAY
        assert row[4].current_color == Color.GRAY

        widget.reset_game()

        assert widget._current_row == 0
        assert widget._current_col == 0
        row = widget.letter_boxes[0]
        for box in row:
            assert box.current_color == Color.WHITE


class TestOctordleSolver: ...


class TestRemainingWordsDialog:
    def test_init(self, qtbot):
        dialog = RemainingWordsDialog(words=["CRANE", "SLATE"])
        qtbot.addWidget(dialog)

        assert dialog.words_list_widget.count() == 2


class TestPuzzleSettingsDialog:
    def test_init(self, qtbot):
        dialog = PuzzleSettingsDialog(8, 13)
        qtbot.addWidget(dialog)

        assert dialog.puzzles_edit.text() == "8"
        assert dialog.guesses_edit.text() == "13"

    def test_properties(self, qtbot):
        dialog = PuzzleSettingsDialog(8, 13)
        qtbot.addWidget(dialog)

        dialog.puzzles_edit.setText("10")
        dialog.guesses_edit.setText("20")

        assert dialog.num_puzzles == 10
        assert dialog.num_guesses == 20
