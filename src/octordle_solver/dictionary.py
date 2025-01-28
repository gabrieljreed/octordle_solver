"""Module to load and store the dictionary of words."""

from pathlib import Path

DATA_PATH = Path(__file__).parent / "data"
DICTIONARY_FILE_PATH = DATA_PATH / "5_letter_words_spellchecked.txt"
VALID_GUESSES_FILE_PATH = DATA_PATH / "valid_guesses.txt"
VALID_ANSWERS_FILE_PATH = DATA_PATH / "valid_answers.txt"


__all__ = ["dictionary"]


class Dictionary:
    def __init__(self):
        with open(DICTIONARY_FILE_PATH) as file:
            self.words = file.readlines()
        self.words = [word.strip() for word in self.words]

        with open(VALID_GUESSES_FILE_PATH) as file:
            self.valid_guesses = file.readlines()
        self.valid_guesses = [word.strip() for word in self.valid_guesses]

        with open(VALID_ANSWERS_FILE_PATH) as file:
            self.valid_answers = file.readlines()
        self.valid_answers = [word.strip() for word in self.valid_answers]


dictionary = Dictionary()
