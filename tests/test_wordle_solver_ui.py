from octordle_solver.ui.wordle_solver_ui import CompareToWordleBotDialog, DiffDialog, HelpDialog, WordleSolver
from octordle_solver.ui.helpers import Color
from octordle_solver.solver import get_cached_best_second_guess, AnswerPossibility, Group
from octordle_solver.constants import STARTING_GUESS
from PySide6.QtCore import Qt


class TestWordleSolverUI:
    def test_init(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        assert len(widget.letter_boxes) == 6
        for row in widget.letter_boxes:
            assert len(row) == 5
        assert widget._current_row == 0
        assert widget._current_col == 0

    def test_type_letter(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        qtbot.keyClicks(widget, "A")
        assert widget.letter_boxes[0][0].text() == "A"
        assert widget._current_col == 1

    def test_type_letter_at_end(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        qtbot.keyClicks(widget, "ABCDE")
        qtbot.keyClicks(widget, "F")  # Should not be added since we're at the end of the row
        assert widget.letter_boxes[0][0].text() == "A"
        assert widget.letter_boxes[0][1].text() == "B"
        assert widget.letter_boxes[0][2].text() == "C"
        assert widget.letter_boxes[0][3].text() == "D"
        assert widget.letter_boxes[0][4].text() == "E"
        assert widget._current_col == 5

    def test_delete_letter(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        qtbot.keyClicks(widget, "A")
        qtbot.keyClick(widget, Qt.Key_Backspace)
        assert widget.letter_boxes[0][0].text() == ""
        assert widget._current_col == 0

    def test_delete_letter_at_start(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        qtbot.keyClick(widget, Qt.Key_Backspace)
        # Should not delete anything since we're at the start, nor should it error
        assert widget.letter_boxes[0][0].text() == ""
        assert widget._current_col == 0

    def test_make_guess_word_incomplete(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        qtbot.keyClicks(widget, "A")
        qtbot.keyClick(widget, Qt.Key_Return)
        # Should not make a guess since the word is incomplete
        assert widget._current_row == 0
        assert widget._current_col == 1

    def test_make_guess_word_complete(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        qtbot.keyClicks(widget, "ABCDE")
        qtbot.keyClick(widget, Qt.Key_Return)
        # Should make a guess and move to the next row
        assert widget._current_row == 1
        assert widget._current_col == 0
        # Letter boxes in the first row should be gray since they are now guesses
        for col in range(5):
            assert widget.letter_boxes[0][col].current_color == Color.GRAY

    def test_get_best_guesses_no_guesses(self, qtbot, mocker):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        mock_threadpool = mocker.patch.object(widget, "threadpool")
        widget.get_best_guesses()
        mock_threadpool.start.assert_not_called()

    def test_get_best_guesses(self, qtbot, mocker):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        mock_threadpool = mocker.patch.object(widget, "threadpool")
        widget.use_selected_guess("CRANE")
        qtbot.keyClick(widget, Qt.Key_Return)
        widget.get_best_guesses()
        mock_threadpool.start.assert_called_once()

        # Mock the puzzle's all_answers with some dummy data
        widget.puzzle.all_answers = [
            AnswerPossibility(
                word="WORD1",
                groups=[Group(["AAAAA", "BBBBB", "CCCCC"], "YNMYN")],
            ),
            AnswerPossibility(
                word="WORD2",
                groups=[Group(["XXXXX", "YYYYY", "ZZZZZ"], "NMYNM")],
            ),
        ]
        widget.puzzle.remaining_words = ["AAAAA", "BBBBB", "CCCCC", "XXXXX", "YYYYY", "ZZZZZ"]
        widget._on_get_answer_possibilities_finished()
        # The best guess list should now contain the words from the all_answers
        assert widget.best_guess_list.count() == 2
        assert widget.best_guess_list.item(0).text() == "WORD1"
        assert widget.best_guess_list.item(1).text() == "WORD2"

        # The remaining words label should show the correct count
        assert widget.remaining_words_label.text() == "6 Remaining Word(s)"
        assert widget.remaining_words_list.count() == 6
        remaining_words_in_list = [
            widget.remaining_words_list.item(i).text() for i in range(widget.remaining_words_list.count())
        ]
        assert set(remaining_words_in_list) == set(["AAAAA", "BBBBB", "CCCCC", "XXXXX", "YYYYY", "ZZZZZ"])

    def test_get_cached_second_guess(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        widget.use_selected_guess(STARTING_GUESS)
        qtbot.keyClick(widget, Qt.Key_Return)
        widget.best_guess_list.clear()
        widget._get_cached_second_guess()
        # The cached second guess for the starting guess should be in the best guess list
        assert widget.best_guess_list.count() == 1
        assert widget.best_guess_list.item(0).text() == get_cached_best_second_guess([2, 2, 2, 2, 2])

    def test_display_groups(self, qtbot): ...

    def test_reset(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        qtbot.keyClicks(widget, "ABCDE")
        qtbot.keyClick(widget, Qt.Key_Return)
        widget.reset_game()
        assert widget._current_row == 0
        assert widget._current_col == 0
        for row in widget.letter_boxes:
            for box in row:
                assert box.text() == ""
                assert box.current_color == Color.WHITE

    def test_word(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        assert widget.word == ""
        qtbot.keyClicks(widget, "CRANE")
        qtbot.keyClick(widget, Qt.Key_Return)
        assert widget.word == "CRANE"

    def test_result(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        assert widget.result == ""
        qtbot.keyClicks(widget, "CRANE")
        qtbot.keyClick(widget, Qt.Key_Return)
        assert widget.result == "NNNNN"
        # Click the first letter box to change it to yellow
        qtbot.mouseClick(widget.letter_boxes[0][0], Qt.LeftButton)
        assert widget.result == "MNNNN"
        # Click the first letter box again to change it to green
        qtbot.mouseClick(widget.letter_boxes[0][0], Qt.LeftButton)
        assert widget.result == "YNNNN"

    def test_diff_remaining_words(self, qtbot): ...

    def test_use_selected_guess(self, qtbot):
        widget = WordleSolver()
        qtbot.addWidget(widget)
        widget.use_selected_guess("CRANE")
        assert widget._current_row == 0
        assert widget._current_col == 5
        row = widget.letter_boxes[0]
        for i in range(5):
            assert row[i].text() == "CRANE"[i]
            assert not row[i].letter_is_set
            assert row[i].current_color == Color.WHITE


class TestHelpDialog:
    def test_init(self, qtbot):
        dialog = HelpDialog()
        qtbot.addWidget(dialog)
        assert hasattr(dialog, "instructions_label")


class TestCompareDialog:
    def test_init(self, qtbot):
        dialog = CompareToWordleBotDialog()
        qtbot.addWidget(dialog)
        assert hasattr(dialog, "text_edit")

    def test_get_words(self, qtbot):
        dialog = CompareToWordleBotDialog()
        qtbot.addWidget(dialog)
        # Add some text to the text edit
        dialog.text_edit.setPlainText("WORD1\nWORD2\nWORD3")
        words = dialog.get_words()
        assert words == ["WORD1", "WORD2", "WORD3"]


class TestDiffDialog:
    def test_init(self, qtbot):
        extra_words = ["EXTRA", "WORDS"]
        missing_words = ["MISSING", "WORDS"]
        dialog = DiffDialog(extra_words, missing_words)
        qtbot.addWidget(dialog)
        assert hasattr(dialog, "extra_words_list")
        for i in range(dialog.extra_words_list.count()):
            item = dialog.extra_words_list.item(i)
            assert item.text() in extra_words
        assert hasattr(dialog, "missing_words_list")
        for i in range(dialog.missing_words_list.count()):
            item = dialog.missing_words_list.item(i)
            assert item.text() in missing_words
