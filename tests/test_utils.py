import pytest

from octordle_solver.utils import sanitize_words


@pytest.mark.parametrize(
    "input_words, expected",
    [
        [[], []],
        [["abcde"], ["ABCDE"]],
        [["abcde", "vwxyz"], ["ABCDE", "VWXYZ"]],
    ],
)
def test_sanitize_words(input_words, expected):
    assert sanitize_words(input_words) == expected
