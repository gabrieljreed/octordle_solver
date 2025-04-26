"""Process all words."""

import re
from pathlib import Path

import enchant

words_file = Path("wordle_answers.txt")
output_file = Path("wordle_answers_processed.txt")

with words_file.open() as file:
    lines = file.readlines()

words = []
for line in lines:
    words += line.split()

dictionary = enchant.Dict("en_US")

with output_file.open("w") as file:
    for word in words:
        if not dictionary.check(word.strip()):
            continue
        file.write(word + "\n")
