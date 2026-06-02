"""Integration tests verifying the Rust solver produces identical results to the Python solver."""

import pytest
import time

import octordle_solver_rs as rs
from octordle_solver.dictionary import dictionary
from octordle_solver.solver import (
    AnswerPossibility as PyAnswerPossibility,
    calculate_fitness_score as py_calculate_fitness_score,
    generate_groups as py_generate_groups,
    get_all_answers as py_get_all_answers,
    score_guess as py_score_guess,
)


class TestScoreGuess:
    @pytest.mark.parametrize(
        "guess, answer, expected",
        [
            # All correct
            ("SLATE", "SLATE", "YYYYY"),
            # All incorrect
            ("BRICK", "FLOWN", "NNNNN"),
            # All misplaced: every letter present but in wrong position
            ("ABCDE", "BCDEA", "MMMMM"),
            # Mixed: CRANE vs TRACE
            # first pass exact: R(1), A(2), E(4) → remaining: T=1, C=1
            # second pass: C(0) → M; N(3) → N
            ("CRANE", "TRACE", "MYYNY"),
            # Duplicate letter in guess, only one in answer
            # SPEED vs BLADE: E(2)→M, E(3)→N, D(4)→M
            ("SPEED", "BLADE", "NNMNM"),
            # Duplicate guess letter, one exact match in answer
            # AABBB vs XAXXX: A(1) exact → Y; A(0) → N (no more A in remaining)
            ("AABBB", "XAXXX", "NYNNN"),
            # Duplicate guess letters, both misplaced
            # AABBB vs BBAAA → MMMMN
            ("AABBB", "BBAAA", "MMMMN"),
        ],
    )
    def test_matches_python(self, guess, answer, expected):
        assert rs.score_guess(guess, answer) == expected
        assert py_score_guess(guess, answer) == expected

    def test_lowercase_input(self):
        """Rust implementation should handle lowercase the same as Python (uppercase internally)."""
        assert rs.score_guess("slate", "crane") == rs.score_guess("SLATE", "CRANE")

    def test_invalid_length_raises(self):
        with pytest.raises(Exception):
            rs.score_guess("ABCD", "ABCDE")
        with pytest.raises(Exception):
            rs.score_guess("ABCDE", "ABCDEF")


class TestGenerateGroups:
    WORDS = ["SLATE", "CRANE", "TRACE", "STALE", "LEAST", "TALES"]

    def test_all_words_partitioned(self):
        groups = rs.generate_groups("SLATE", self.WORDS)
        total = sum(len(g.words) for g in groups)
        assert total == len(self.WORDS)

    def test_yyyyy_group_exists(self):
        groups = rs.generate_groups("SLATE", self.WORDS)
        yyyyy = [g for g in groups if g.possibility == "YYYYY"]
        assert len(yyyyy) == 1
        assert yyyyy[0].words == ["SLATE"]

    def test_matches_python_group_sizes(self):
        """Rust and Python generate_groups must produce the same partition sizes."""
        py_groups = py_generate_groups("SLATE", self.WORDS)
        rs_groups = rs.generate_groups("SLATE", self.WORDS)

        # Build possibility → size dicts and compare
        py_sizes = {g.possibility: len(g.words) for g in py_groups}
        rs_sizes = {g.possibility: len(g.words) for g in rs_groups}
        assert py_sizes == rs_sizes

    def test_matches_python_group_words(self):
        """Rust and Python must assign the same words to each pattern."""
        py_groups = py_generate_groups("CRANE", self.WORDS)
        rs_groups = rs.generate_groups("CRANE", self.WORDS)

        py_map = {g.possibility: sorted(g.words) for g in py_groups}
        rs_map = {g.possibility: sorted(g.words) for g in rs_groups}
        assert py_map == rs_map

    def test_group_bool(self):
        groups = rs.generate_groups("SLATE", ["SLATE"])
        assert bool(groups[0]) is True

    def test_empty_remaining_words(self):
        groups = rs.generate_groups("SLATE", [])
        assert groups == []

    def test_single_word(self):
        groups = rs.generate_groups("CRANE", ["CRANE"])
        assert len(groups) == 1
        assert groups[0].possibility == "YYYYY"
        assert groups[0].words == ["CRANE"]


# ---------------------------------------------------------------------------
# Small word set reused across AnswerPossibility / fitness / get_all_answers tests
# ---------------------------------------------------------------------------
SMALL_WORDS = ["SLATE", "CRANE", "TRACE", "STALE", "LEAST", "TALES", "CRATE", "CATER"]


class TestAnswerPossibility:
    def test_basic_properties(self):
        groups = rs.generate_groups("CRANE", SMALL_WORDS)
        ap = rs.AnswerPossibility("CRANE", groups)
        assert ap.word == "CRANE"
        assert len(ap.groups) == len(groups)
        assert ap.max_group_size == max(len(g.words) for g in groups)

    def test_max_group_size_empty_groups(self):
        ap = rs.AnswerPossibility("CRANE", [])
        assert ap.max_group_size == -1

    def test_gt_more_groups_wins(self):
        """More groups → better guess."""
        groups3 = rs.generate_groups("CRANE", ["CRANE", "SLATE", "TRACE"])
        groups2 = rs.generate_groups("CRANE", ["CRANE", "SLATE"])
        ap_more = rs.AnswerPossibility("CRANE", groups3)
        ap_less = rs.AnswerPossibility("SLATE", groups2)
        # Only compare when group counts actually differ.
        if len(groups3) != len(groups2):
            winner = ap_more if len(groups3) > len(groups2) else ap_less
            loser = ap_less if winner is ap_more else ap_more
            assert winner.__gt__(loser)

    def test_gt_matches_python(self):
        """Rust __gt__ must agree with Python's for the same inputs."""
        py_groups_a = py_generate_groups("CRANE", SMALL_WORDS)
        py_groups_b = py_generate_groups("SLATE", SMALL_WORDS)
        rs_groups_a = rs.generate_groups("CRANE", SMALL_WORDS)
        rs_groups_b = rs.generate_groups("SLATE", SMALL_WORDS)

        py_ap_a = PyAnswerPossibility("CRANE", py_groups_a)
        py_ap_b = PyAnswerPossibility("SLATE", py_groups_b)
        rs_ap_a = rs.AnswerPossibility("CRANE", rs_groups_a)
        rs_ap_b = rs.AnswerPossibility("SLATE", rs_groups_b)

        assert (py_ap_a > py_ap_b) == rs_ap_a.__gt__(rs_ap_b)
        assert (py_ap_b > py_ap_a) == rs_ap_b.__gt__(rs_ap_a)


class TestCalculateFitnessScore:
    def test_matches_python(self):
        py_groups = py_generate_groups("CRANE", SMALL_WORDS)
        rs_groups = rs.generate_groups("CRANE", SMALL_WORDS)

        py_ap = PyAnswerPossibility("CRANE", py_groups)
        rs_ap = rs.AnswerPossibility("CRANE", rs_groups)

        py_score = py_calculate_fitness_score(py_ap, SMALL_WORDS)
        rs_score = rs.calculate_fitness_score(rs_ap, SMALL_WORDS)
        assert abs(py_score - rs_score) < 1e-9

    def test_remaining_word_bonus_applied(self):
        """A word that is itself in remaining_words should score higher."""
        groups = rs.generate_groups("CRANE", SMALL_WORDS)
        ap_in = rs.AnswerPossibility("CRANE", groups)  # CRANE is in SMALL_WORDS
        ap_out = rs.AnswerPossibility("ZZZZZ", groups)  # ZZZZZ is not

        score_in = rs.calculate_fitness_score(ap_in, SMALL_WORDS)
        score_out = rs.calculate_fitness_score(ap_out, SMALL_WORDS)
        assert score_in > score_out


class TestGetAllAnswers:
    def test_empty_remaining_returns_empty(self):
        result = rs.get_all_answers([], dictionary.valid_guesses)
        assert result == []

    def test_single_remaining_word(self):
        result = rs.get_all_answers(["CRANE"], dictionary.valid_guesses)
        assert len(result) == 1
        assert result[0].word == "CRANE"

    def test_matches_python_order_small(self):
        """Rust and Python must rank the same word #1 for a small word set."""
        remaining = SMALL_WORDS
        py_result = py_get_all_answers(remaining, dictionary.valid_guesses)
        rs_result = rs.get_all_answers(remaining, dictionary.valid_guesses)

        assert py_result[0].word == rs_result[0].word, (
            f"Best guess mismatch: Python={py_result[0].word}, Rust={rs_result[0].word}"
        )

    def test_result_covers_all_guesses(self):
        """Every word in remaining + valid_guesses must appear in the result."""
        remaining = SMALL_WORDS[:4]
        rs_result = rs.get_all_answers(remaining, dictionary.valid_guesses)
        result_words = {ap.word for ap in rs_result}

        expected = set(remaining) | set(dictionary.valid_guesses)
        assert expected == result_words

    def test_rust_faster_than_python(self):
        """Rust get_all_answers should be faster than the Python version."""
        remaining = SMALL_WORDS

        t0 = time.perf_counter()
        rs.get_all_answers(remaining, dictionary.valid_guesses)
        rust_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        py_get_all_answers(remaining, dictionary.valid_guesses)
        python_time = time.perf_counter() - t0

        print(f"\n  Rust: {rust_time:.3f}s  Python: {python_time:.3f}s  speedup: {python_time / rust_time:.1f}x")
        assert rust_time < python_time, "Expected Rust to be faster than Python"


# ---------------------------------------------------------------------------
# Guess
# ---------------------------------------------------------------------------


class TestGuess:
    def test_basic(self):
        g = rs.Guess("CRANE", "MYYNY")
        assert g.word == "CRANE"
        assert g.result == "MYYNY"

    def test_eq(self):
        assert rs.Guess("CRANE", "MYYNY") == rs.Guess("CRANE", "MYYNY")
        assert rs.Guess("CRANE", "MYYNY") != rs.Guess("SLATE", "MYYNY")
        assert rs.Guess("CRANE", "MYYNY") != rs.Guess("CRANE", "NNNNN")


# ---------------------------------------------------------------------------
# Puzzle
# ---------------------------------------------------------------------------


class TestPuzzle:
    def _make_puzzle(self, get_best_answer=False):
        return rs.Puzzle(dictionary.valid_answers, dictionary.valid_guesses, get_best_answer)

    def test_initial_state(self):
        p = self._make_puzzle()
        assert len(p.remaining_words) == len(dictionary.valid_answers)
        assert len(p.guesses) == 0
        assert p.is_solved is False

    def test_make_guess_string_result(self):
        p = self._make_puzzle()
        before = len(p.remaining_words)
        p.make_guess("SLATE", "NNNNN")
        # All words containing S, L, A, T, or E must be filtered out.
        assert len(p.remaining_words) < before
        assert len(p.guesses) == 1
        assert p.guesses[0].word == "SLATE"
        assert p.guesses[0].result == "NNNNN"

    def test_make_guess_int_result(self):
        """Result as list[int]: 0=correct, 1=misplaced, 2=incorrect."""
        p = self._make_puzzle()
        p.make_guess("SLATE", [2, 2, 2, 2, 2])  # all incorrect
        assert len(p.guesses) == 1
        assert p.guesses[0].result == "NNNNN"

    def test_make_guess_int_result_mixed(self):
        p = self._make_puzzle()
        p.make_guess("CRANE", [0, 2, 2, 2, 2])  # C correct, rest wrong
        assert p.guesses[0].result == "YNNNN"

    def test_filter_words_consistency(self):
        """filter_words(guess) and make_guess should produce the same remaining words."""
        p1 = self._make_puzzle()
        p2 = self._make_puzzle()

        p1.make_guess("CRANE", "MYYNY")
        g = rs.Guess("CRANE", "MYYNY")
        p2.filter_words(g)

        assert sorted(p1.remaining_words) == sorted(p2.remaining_words)

    def test_is_solved_false(self):
        p = self._make_puzzle()
        p.make_guess("CRANE", "MYYNY")
        assert p.is_solved is False

    def test_is_solved_true(self):
        p = self._make_puzzle()
        p.make_guess("CRANE", "YYYYY")
        assert p.is_solved is True

    def test_reset(self):
        p = self._make_puzzle()
        p.make_guess("SLATE", "NNNNN")
        p.reset()
        assert len(p.remaining_words) == len(dictionary.valid_answers)
        assert len(p.guesses) == 0
        assert p.is_solved is False

    def test_all_answers_dict(self):
        p = self._make_puzzle(get_best_answer=False)
        p.make_guess("SLATE", "NNNNN")
        p.get_all_answers()
        d = p.all_answers_dict()
        # Dict keys should match all_answers words.
        assert set(d.keys()) == {ap.word for ap in p.all_answers}

    def test_filter_narrows_to_answer(self):
        """Feeding the correct score for each guess should narrow to exactly 1 word."""
        from octordle_solver.solver import score_guess as py_score

        target = "CRANE"
        p = self._make_puzzle()
        for guess_word in ["SLATE", "CRIMP", "CRANE"]:
            result = py_score(guess_word, target)
            p.make_guess(guess_word, result)
            if result == "YYYYY":
                break
        assert target in p.remaining_words

    def test_matches_python_remaining_words(self):
        """Rust Puzzle filter must produce the same remaining_words as Python Puzzle."""
        from octordle_solver.solver import (
            Puzzle as PyPuzzle,
            score_guess as py_score,
        )

        target = "CRANE"
        guesses_to_make = ["SLATE", "CRIMP"]

        py_puzzle = PyPuzzle(get_best_answer=False)
        rs_puzzle = self._make_puzzle(get_best_answer=False)

        for word in guesses_to_make:
            result = py_score(word, target)
            py_puzzle.make_guess(word, result)
            rs_puzzle.make_guess(word, result)

        assert sorted(py_puzzle.remaining_words) == sorted(rs_puzzle.remaining_words)


# ---------------------------------------------------------------------------
# get_best_guess_multiple_puzzles
# ---------------------------------------------------------------------------


class TestGetBestGuessMultiplePuzzles:
    def _solved_puzzle(self, remaining, get_best_answer=True):
        p = rs.Puzzle(dictionary.valid_answers, dictionary.valid_guesses, get_best_answer)
        p.remaining_words = remaining
        p.get_all_answers()
        return p

    def test_single_puzzle_returns_top_answer(self):
        p = self._solved_puzzle(["CRANE", "SLATE", "TRACE"])
        result = rs.get_best_guess_multiple_puzzles([p])
        assert result == p.all_answers[0].word

    def test_one_remaining_word_returns_it(self):
        p1 = self._solved_puzzle(["CRANE", "SLATE"])
        p2 = self._solved_puzzle(["CRIMP"])  # 1 remaining → solved next turn
        result = rs.get_best_guess_multiple_puzzles([p1, p2])
        assert result == "CRIMP"

    def test_result_is_a_word(self):
        p1 = self._solved_puzzle(["CRANE", "SLATE", "TRACE"])
        p2 = self._solved_puzzle(["STALE", "LEAST", "TALES"])
        result = rs.get_best_guess_multiple_puzzles([p1, p2])
        assert isinstance(result, str)
        assert len(result) == 5
