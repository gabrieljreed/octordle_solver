"""Just say Venn game."""

from collections import defaultdict
from itertools import chain
from pathlib import Path

CIRCLE_1 = ["O", "R"]
CIRCLE_2 = ["C", "E", "H"]
CIRCLE_3 = ["B", "R", "U"]


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


get_words_for_circles([CIRCLE_1, CIRCLE_2])
get_words_for_circles([CIRCLE_2, CIRCLE_3])
get_words_for_circles([CIRCLE_1, CIRCLE_3])
get_words_for_circles([CIRCLE_1, CIRCLE_2, CIRCLE_3])
