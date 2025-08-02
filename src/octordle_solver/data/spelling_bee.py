"""Spelling bee solver."""

from pathlib import Path

import enchant

# PUZZLE INPUT
CENTER_LETTER = "O"
OTHER_LETTERS = ["T", "I", "M", "A", "R", "V"]

dictionary = enchant.Dict("en_US")
dictionary_path = Path(__file__).parent / "Collins Scrabble Words (2019).txt"

words = []
with open(dictionary_path, "r") as f:
    words = f.readlines()
words = [word.strip() for word in words]

print(f"{len(words)=}")
filtered_words = []
short_words = 0
center_letter_missing = 0
using_other_letters = 0
misspelled_words = 0
for word in words:
    if len(word) < 4:
        short_words += 1
        continue

    if CENTER_LETTER not in word:
        center_letter_missing += 1
        continue

    valid = True
    for letter in word:
        if letter not in OTHER_LETTERS and letter != CENTER_LETTER:
            valid = False
            break

    if not valid:
        using_other_letters += 1
        continue

    if not dictionary.check(word.strip()):
        misspelled_words += 1
        continue

    filtered_words.append(word)

print(f"{short_words=}")
print(f"{center_letter_missing=}")
print(f"{using_other_letters=}")
print(f"{misspelled_words=}")
print(f"{len(filtered_words)=}")

for word in filtered_words:
    print(word)

panagrams = []
for word in filtered_words:
    valid = True
    for letter in OTHER_LETTERS:
        if letter not in word:
            valid = False
            break
    if not valid:
        continue
    panagrams.append(word)

print(f"{panagrams=}")
