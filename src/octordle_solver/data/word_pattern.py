"""Find words that match a vowel-consonant-vowel pattern."""

import re
from pathlib import Path

DICTIONARY_PATH = Path(__file__).parent / "Collins Scrabble Words (2019).txt"
words = DICTIONARY_PATH.read_text().split("\n")[1:]
words = [w for w in words if len(w) > 3]

PATTERN = r"^[bcdfghjklmnpqrstvwxyz]?([aeiou])(?:[bcdfghjklmnpqrstvwxyz]\1)*[bcdfghjklmnpqrstvwxyz]?$"


matched = [w for w in words if re.match(PATTERN, w.lower())]
for word in matched:
    print(word)
print(len(matched))
