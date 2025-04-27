import pytest

from octordle_solver.generate_groups import (
    Possibility,
    evaluate_game_state,
    generate_groups,
)


def test_possibility():
    possibility = Possibility(0, 1, 2, 0, 0)
    assert possibility[0] == 0
    assert possibility[1] == 1
    assert possibility[2] == 2


@pytest.mark.parametrize(
    "word, possibility, other_word, expected",
    [
        [
            "ABCDE",
            [0, 0, 0, 0, 0],
            "ABCDE",
            True,
        ],
        [
            "ABCDE",
            [0, 0, 0, 0, 2],
            "ABCDZ",
            True,
        ],
        [
            "ABCDE",
            [2, 0, 0, 0, 0],
            "ABCDE",
            False,
        ],
        [
            "ABCDE",
            [2, 0, 0, 0, 0],
            "ZBCDE",
            True,
        ],
        [
            "ABCDE",
            [0, 0, 0, 0, 0],
            "ZBCDE",
            False,
        ],
        [
            "ABCDE",
            [1, 2, 2, 2, 2],
            "WXYZA",
            True,
        ],
        [
            "ABCDE",
            [1, 2, 2, 2, 2],
            "VWXYZ",
            False,
        ],
        [
            "ABCDE",
            [1, 2, 2, 2, 2],
            "AWXYZ",
            False,
        ],
    ],
    ids=[
        "words are identical",
        "word has incorrect letter",
        "word has incorrect letter, other word matches",
        "word has incorrect letter, other word does not match",
        "word is correct, other word has incorrect letter",
        "word has misplaced letter, other word has letter",
        "word has misplaced letter, other word does not have letter",
        "word has misplaced letter, other word has letter in same position",
    ],
)
def test_evaluate_game_state(word, possibility, other_word, expected):
    assert evaluate_game_state(word, possibility, other_word) == expected


@pytest.mark.parametrize(
    "word, remaining_words, expected",
    [],
)
def test_generate_groups(word, remaining_words, expected):
    assert generate_groups(word, remaining_words) == expected
