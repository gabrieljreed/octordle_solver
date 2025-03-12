from octordle_solver.solver import filter_words
import pytest


@pytest.mark.parametrize(
    "words, correct_letters, incorrect_letters, misplaced_letters, expected",
    [
        [[], [], [], [], []],
        [
            ["ABCDE", "BBCDE"],
            ["", "", "", "", ""],
            ["A"],
            [],
            ["BBCDE"],
        ],
        [
            ["ABCDE", "BBCDE"],
            ["A", "", "", "", ""],
            [],
            [],
            ["ABCDE"],
        ],
        [
            ["ABCDE", "BBCDE"],
            ["", "", "", "", ""],
            [],
            [("A", 2)],
            ["ABCDE"],
        ],
    ],
)
def test_filter(words, correct_letters, incorrect_letters, misplaced_letters, expected):
    result = filter_words(words, correct_letters, misplaced_letters, incorrect_letters)
    assert result == expected
