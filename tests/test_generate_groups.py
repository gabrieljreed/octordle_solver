import pytest

from octordle_solver.generate_groups import (
    Group,
    Possibility,
    PossibilityState,
    create_chunks,
    evaluate_game_state,
    generate_groups,
    generate_groups_real_possibilities_only,
    generate_true_feedback,
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
    assert generate_true_feedback(guess, answer) == expected


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
    assert generate_groups_real_possibilities_only(given_word, remaining_words) == expected


def test_create_chunks():
    in_list = [f"{i:02d}" for i in range(23)]
    chunks = list(create_chunks(in_list, 10))
    assert chunks[0] == ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]
    assert chunks[1] == ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]
    assert chunks[2] == ["20", "21", "22"]
