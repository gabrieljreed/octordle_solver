import pytest

from octordle_solver.dictionary import dictionary
from octordle_solver.solver import (
    Group,
    Puzzle,
    create_chunks,
    filter_words,
    generate_groups,
    get_wordle_feedback,
)


class TestGroup:
    def test_str(self):
        group = Group(["ABCDE"], (0, 0, 0, 0, 0))

        assert str(group) == "(0, 0, 0, 0, 0)\n\tABCDE"
        assert bool(Group) is True

    @pytest.mark.parametrize(
        "words, possibility, expected",
        [
            [[], (0, 0, 0, 0, 0), False],
            [["ABCDE"], (0, 0, 0, 0, 0), True],
            [["ABCDE", "VWXYZ"], (0, 0, 0, 0, 0), True],
        ],
    )
    def test_bool(self, words, possibility, expected):
        assert bool(Group(words, possibility)) is expected

    def test_eq(self):
        group_1 = Group(["ABCDE"], (0, 0, 0, 0, 0))
        group_2 = Group(["ABCDE"], (0, 0, 0, 0, 0))
        assert group_1 == group_2

        group_1 = Group(["ABCDE"], (0, 0, 0, 0, 1))
        group_2 = Group(["ABCDE"], (0, 0, 0, 0, 0))
        assert group_1 != group_2

        group_1 = Group(["ABCDE"], (0, 0, 0, 0, 0))
        group_2 = Group(["VWXYZ"], (0, 0, 0, 0, 0))
        assert group_1 != group_2

        assert group_1 != {"words": ["ABCDE"], "possibility": (0, 0, 0, 0, 0)}


@pytest.mark.parametrize(
    "guess, answer, expected",
    [
        ["ABCDE", "ABCDE", [0, 0, 0, 0, 0]],
        ["ABCDE", "ABCED", [0, 0, 0, 1, 1]],
        ["ABCDE", "ABCDZ", [0, 0, 0, 0, 2]],
        ["ABCDE", "VWXYZ", [2, 2, 2, 2, 2]],
        ["APPLE", "PPLAE", [1, 0, 1, 1, 0]],
    ],
)
def test_generate_true_feedback(guess, answer, expected):
    assert get_wordle_feedback(guess, answer) == expected


@pytest.mark.parametrize(
    "given_word, remaining_words, expected",
    [
        ["ABCDE", [], []],
        [
            "ABCDE",
            ["ABCDE", "ABCED", "EDCBA"],
            [
                Group(["ABCDE"], (0, 0, 0, 0, 0)),
                Group(["ABCED"], (0, 0, 0, 1, 1)),
                Group(["EDCBA"], (1, 1, 0, 1, 1)),
            ],
        ],
    ],
)
def test_generate_groups_real_possibilities_only(given_word, remaining_words, expected):
    assert generate_groups(given_word, remaining_words) == expected


def test_create_chunks():
    in_list = [f"{i:02d}" for i in range(23)]
    chunks = list(create_chunks(in_list, 10))
    assert chunks[0] == ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]
    assert chunks[1] == ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]
    assert chunks[2] == ["20", "21", "22"]


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


class TestPuzzle:
    def test_init(self):
        puzzle = Puzzle()
        assert puzzle.correct_letters == ["", "", "", "", ""]
        assert puzzle.misplaced_letters == []
        assert puzzle.incorrect_letters == []
        assert puzzle.all_answers == []
        assert puzzle.all_answers_dict == {}

    def test_make_guess(self):
        puzzle = Puzzle()
        # Pare down the list of remaining words so the test doesn't take as long
        puzzle.remaining_words = [
            "AFTER",
            "CARET",
            "CATER",
            "GATER",
            "HATER",
            "MATEY",
            "WATER",
        ]
        puzzle.make_guess("TREED", "MMNYN")
        assert "WATER" in puzzle.remaining_words
        assert puzzle.correct_letters == ["", "", "", "E", ""]
        assert puzzle.misplaced_letters == [("T", 0), ("R", 1)]
        assert puzzle.incorrect_letters == ["D"]
