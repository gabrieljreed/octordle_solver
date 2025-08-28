import pytest

from octordle_solver.dictionary import dictionary
from octordle_solver.solver import (
    AnswerPossibility,
    Group,
    Puzzle,
    calculate_fitness_score,
    create_chunks,
    filter_words,
    generate_groups,
    get_best_guess_multiple_puzzles,
    get_wordle_feedback,
)

GROUP_1 = Group(["DATER"], (2, 2, 2, 0, 1))
GROUP_2 = Group(["EATER"], (2, 1, 2, 0, 2))
GROUP_3 = Group(["HATER"], (0, 2, 2, 0, 2))
GROUP_4 = Group(["RATED"], (2, 2, 2, 0, 0))
GROUP_5 = Group(["RATER"], (2, 2, 2, 0, 2))
GROUP_6 = Group(["WATER"], (2, 2, 1, 0, 2))


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


class TestAnswerPossibility:
    demo_groups = [GROUP_1, GROUP_2, GROUP_3, GROUP_4, GROUP_5, GROUP_6]

    def test_init(self):
        answer_possibility = AnswerPossibility("CRANE", self.demo_groups)
        assert answer_possibility.word == "CRANE"
        assert answer_possibility.groups == self.demo_groups

    def test_max_group_size(self):
        answer_possibility = AnswerPossibility("CRANE", self.demo_groups)
        assert answer_possibility.max_group_size == 1

        answer_possibility = AnswerPossibility("CRANE", [])
        assert answer_possibility.max_group_size == -1

    @pytest.mark.parametrize(
        "p1, p2",
        [
            [AnswerPossibility("CRANE", []), AnswerPossibility("SLATE", [])],
            [
                AnswerPossibility(
                    "CRANE",
                    [
                        Group(["AAAAA"], (2, 2, 0, 2, 1)),
                        Group(["BBBBB"], (2, 1, 0, 2, 2)),
                        Group(["CCCCC"], (2, 2, 0, 2, 2)),
                    ],
                ),
                AnswerPossibility(
                    "SLATE",
                    [Group(["AAAAA"], (1, 2, 2, 0, 2)), Group(["BBBBB", "CCCCC"], (1, 2, 2, 2, 2))],
                ),
            ],
            [
                AnswerPossibility(
                    "CRANE",
                    [Group(["AAAAA", "BBBBB"], (1, 1, 1, 1, 1)), Group(["CCCCC", "DDDDD", "EEEEE"], (2, 2, 2, 2, 2))],
                ),
                AnswerPossibility(
                    "SLATE",
                    [Group(["AAAAA", "BBBBB", "CCCCC", "DDDDD"], (2, 2, 2, 2, 2)), Group(["EEEEE"], (2, 2, 2, 2, 2))],
                ),
            ],
        ],
        ids=["no words in groups", "more groups", "same number of groups, different sizes"],
    )
    def test_greater_than(self, p1, p2):
        assert p1 > p2


@pytest.mark.parametrize(
    "p1, p2",
    [
        [
            AnswerPossibility(
                "CRANE",
                [Group(["AAAAA", "BBBBB"], (1, 1, 1, 1, 1)), Group(["CCCCC", "DDDDD", "EEEEE"], (2, 2, 2, 2, 2))],
            ),
            AnswerPossibility(
                "SLATE",
                [Group(["AAAAA", "BBBBB"], (1, 1, 1, 1, 1)), Group(["CCCCC", "DDDDD", "EEEEE"], (2, 2, 2, 2, 2))],
            ),
        ],
        [
            AnswerPossibility(
                "ADIEU",
                [Group(["AAAAA", "BBBBB"], (1, 1, 1, 1, 1)), Group(["CCCCC", "DDDDD", "EEEEE"], (2, 2, 2, 2, 2))],
            ),
            AnswerPossibility(
                "SLATE",
                [Group(["AAAAA", "BBBBB", "CCCCC", "DDDDD"], (2, 2, 2, 2, 2)), Group(["EEEEE"], (2, 2, 2, 2, 2))],
            ),
        ],
    ],
    ids=["has remaining word", "smaller groups"],
)
def test_calculate_fitness_score(p1, p2):
    remaining_words = ["CRANE", "AAAAA", "BBBBB"]

    score_1 = calculate_fitness_score(p1, remaining_words)
    score_2 = calculate_fitness_score(p2, remaining_words)
    assert score_1 > score_2


class TestPuzzle:
    def test_init(self):
        puzzle = Puzzle()
        assert puzzle.correct_letters == ["", "", "", "", ""]
        assert puzzle.misplaced_letters == []
        assert puzzle.incorrect_letters == []
        assert puzzle.all_answers == []
        assert puzzle.all_answers_dict == {}

    def test_update_game_state_duplicate_letters(self):
        puzzle = Puzzle()
        puzzle.remaining_words = [
            "ABBEY",
            "ANNEX",
            "APNEA",
            "BEGAN",
            "CHEAP",
        ]
        puzzle._update_game_state("DAMAR", "NMNNN")
        assert puzzle.correct_letters == ["", "", "", "", ""]
        assert puzzle.misplaced_letters == [("A", 1), ("A", 3)]
        assert puzzle.incorrect_letters == ["D", "M", "R"]

    def test_make_guess(self, mocker):
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
        puzzle.valid_guesses = puzzle.remaining_words.copy()
        mock_dictionary = mocker.patch("octordle_solver.solver.dictionary")
        mock_dictionary.words = []

        puzzle.make_guess("TREED", "MMNYN")
        assert "WATER" in puzzle.remaining_words
        assert puzzle.correct_letters == ["", "", "", "E", ""]
        assert puzzle.misplaced_letters == [("T", 0), ("R", 1), ("E", 2)]
        assert puzzle.incorrect_letters == ["D"]

    def test_is_solved(self, mocker):
        puzzle = Puzzle()

        # Mocks to make the test run faster - we're don't care about solving functionality for this test
        puzzle.remaining_words = ["CRANE", "ABAFT", "CRAFT"]
        puzzle.valid_guesses = puzzle.remaining_words.copy()
        mock_dictionary = mocker.patch("octordle_solver.solver.dictionary")
        mock_dictionary.words = []

        assert not puzzle.is_solved

        puzzle.make_guess("CRANE", "YYYNN")
        assert not puzzle.is_solved

        puzzle.make_guess("ABAFT", "NNYYY")
        assert not puzzle.is_solved

        puzzle.make_guess("CRAFT", "YYYYY")
        assert puzzle.is_solved

    def test_reset(self, mocker):
        puzzle = Puzzle()
        puzzle.remaining_words = [
            "AFTER",
            "CARET",
            "CATER",
            "GATER",
            "HATER",
            "MATEY",
            "WATER",
        ]
        puzzle.valid_guesses = puzzle.remaining_words.copy()
        mock_dictionary = mocker.patch("octordle_solver.solver.dictionary")
        mock_dictionary.words = []

        puzzle.make_guess("TREED", "MMNYN")
        assert puzzle.correct_letters == ["", "", "", "E", ""]
        assert puzzle.misplaced_letters == [("T", 0), ("R", 1), ("E", 2)]
        assert puzzle.incorrect_letters == ["D"]

        puzzle.reset()
        assert puzzle.correct_letters == ["", "", "", "", ""]
        assert puzzle.misplaced_letters == []
        assert puzzle.incorrect_letters == []


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
def test_filter_words(words, correct_letters, incorrect_letters, misplaced_letters, expected):
    result = filter_words(words, correct_letters, misplaced_letters, incorrect_letters)
    assert result == expected


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
def test_get_wordle_feedback(guess, answer, expected):
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
def test_generate_groups(given_word, remaining_words, expected):
    assert generate_groups(given_word, remaining_words) == expected


def test_create_chunks():
    in_list = [f"{i:02d}" for i in range(23)]
    chunks = list(create_chunks(in_list, 10))
    assert chunks[0] == ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]
    assert chunks[1] == ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]
    assert chunks[2] == ["20", "21", "22"]


class TestGetBestGuessMultiplePuzzles:
    # TODO: Figure out what takes so long

    def test_one_puzzle(self, mocker):
        mock_dictionary = mocker.patch("octordle_solver.solver.dictionary")
        mock_dictionary.words = []
        puzzle = Puzzle()
        puzzle.remaining_words = [
            "AFTER",
            "CARET",
            "CATER",
            "GATER",
            "HATER",
            "MATEY",
            "WATER",
        ]
        puzzle.valid_guesses = ["WATCH", "AAAAA", "BBBBB"]
        puzzle.make_guess("TREED", "MMNYN")
        best_guess = get_best_guess_multiple_puzzles([puzzle])
        assert best_guess == "CARET"

    def test_solve_in_one_turn(self, mocker):
        mock_dictionary = mocker.patch("octordle_solver.solver.dictionary")
        mock_dictionary.words = []
        puzzle_1 = Puzzle()
        puzzle_1.remaining_words = [
            "AFTER",
            "CARET",
            "CATER",
            "GATER",
            "HATER",
            "MATEY",
            "WATER",
        ]
        puzzle_1.valid_guesses = ["WATCH", "AAAAA", "BBBBB"]
        puzzle_1.make_guess("TREED", "MMNYN")

        puzzle_2 = Puzzle()
        puzzle_2.remaining_words = [
            "INANE",
        ]
        puzzle_2.valid_guesses = ["INANE", "CCCCC", "DDDDD"]
        puzzle_2.make_guess("CRANE", "NNYYY")

        best_guess = get_best_guess_multiple_puzzles([puzzle_1, puzzle_2])
        assert best_guess == "INANE"

    def test_solve_in_two_turns(self, mocker):
        mock_dictionary = mocker.patch("octordle_solver.solver.dictionary")
        mock_dictionary.words = []
        puzzle_1 = Puzzle()
        puzzle_1.remaining_words = [
            "AFTER",
            "CARET",
            "CATER",
            "GATER",
            "HATER",
            "MATEY",
            "WATER",
        ]
        puzzle_1.valid_guesses = ["HATER"]
        puzzle_1.make_guess("TREED", "MMNYN")

        puzzle_2 = Puzzle()
        puzzle_2.remaining_words = [
            "INANE",
            "PLANE",
        ]
        puzzle_2.valid_guesses = ["INANE", "CCCCC", "DDDDD"]
        puzzle_2.make_guess("CRANE", "NNYYY")

        best_guess = get_best_guess_multiple_puzzles([puzzle_1, puzzle_2])
        assert best_guess == "INANE"

    def test_solve_scoring(self, mocker):
        mock_dictionary = mocker.patch("octordle_solver.solver.dictionary")
        mock_dictionary.words = []
        puzzle_1 = Puzzle()
        puzzle_1.remaining_words = [
            "BEECH",
            "BELCH",
            "BICEP",
            "DECOY",
            "DICED",
            "DICEY",
            "EDICT",
            "EJECT",
        ]
        puzzle_1.valid_guesses = puzzle_1.remaining_words.copy()
        puzzle_1.make_guess("CRANE", "MNNNM")

        puzzle_2 = Puzzle()
        puzzle_2.remaining_words = [
            "ADMIN",
            "ALIGN",
            "ANGST",
            "ANNOY",
            "BASIN",
            "BATON",
            "KINDA",
            "NAPPY",
            "TITAN",
            "WOMAN",
        ]
        puzzle_2.valid_guesses = puzzle_2.remaining_words.copy()
        puzzle_2.make_guess("CRANE", "NNMMN")
        best_guess = get_best_guess_multiple_puzzles([puzzle_2, puzzle_1])
        assert best_guess == "DECOY"
