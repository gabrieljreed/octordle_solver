"""Just say Venn game."""

from collections import defaultdict
from itertools import chain
from pathlib import Path

CIRCLE_1 = "IR"
CIRCLE_2 = "ALT"
CIRCLE_3 = "ENM"

_CIRCLE_1 = [char for char in CIRCLE_1]
_CIRCLE_2 = [char for char in CIRCLE_2]
_CIRCLE_3 = [char for char in CIRCLE_3]


dictionary_path = Path(__file__).parent / "Collins Scrabble Words (2019).txt"

words = []
with open(dictionary_path, "r") as f:
    words = f.readlines()
words = [word.strip() for word in words[1:]]  # Strip the first line

word_hash = defaultdict(list)
for word in words:
    letters = sorted(word)
    word_hash["".join(letters)].append(word)


def get_words_for_circles(circles: list[list[str]]):
    """Get words for the given circles."""
    all_letters = list(chain.from_iterable(circles))
    print("".join(all_letters))
    all_letters.sort()
    words = word_hash.get("".join(all_letters), [])
    for word in words:
        print(f"\t{word}")
    return words


get_words_for_circles([_CIRCLE_1, _CIRCLE_2])
get_words_for_circles([_CIRCLE_2, _CIRCLE_3])
get_words_for_circles([_CIRCLE_1, _CIRCLE_3])
get_words_for_circles([_CIRCLE_1, _CIRCLE_2, _CIRCLE_3])
