"""License plate game."""

import re
from pathlib import Path

LETTERS = ["B", "R", "D"]
INCLUDE_Y = False


dictionary_path = Path(__file__).parent / "Collins Scrabble Words (2019).txt"
words = []
with open(dictionary_path, "r") as f:
    words = f.readlines()
words = [word.strip() for word in words]


VOWELS = "[AEIOUY]*" if INCLUDE_Y else "[AEIOU]*"
pattern = rf"^{VOWELS}{LETTERS[0]}{VOWELS}{LETTERS[1]}{VOWELS}{LETTERS[2]}{VOWELS}$"

filtered_words = []
for word in words:
    if re.match(pattern, word):
        filtered_words.append(word)


for word in filtered_words:
    print(word)
print(len(filtered_words))
