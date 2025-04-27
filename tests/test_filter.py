import pytest

from octordle_solver.dictionary import dictionary
from octordle_solver.solver import filter_words


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
        [
            ["ABCDE", "BBCDE"],
            ["", "", "", "", ""],
            [],
            [("B", 0)],
            ["ABCDE"],
        ],
        [
            ["ABCDE", "BCDE"],
            ["", "", "", "", ""],
            [],
            [],
            ["ABCDE"],
        ],
        [
            dictionary.words.copy(),
            ["C", "L", "A", "", ""],
            ["R", "N", "E", "F", "O", "P"],
            [("S", 4)],
            ["CLASH"],
        ],
    ],
    ids=[
        "all empty",
        "incorrect letters",
        "correct letters",
        "misplaced letters",
        "misplaced letters 2",
        "word too short",
        "full",
    ],
)
def test_filter(words, correct_letters, incorrect_letters, misplaced_letters, expected):
    result = filter_words(words, correct_letters, misplaced_letters, incorrect_letters)
    assert result == expected
