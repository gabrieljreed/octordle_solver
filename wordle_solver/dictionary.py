"""Module to load and store the dictionary of words."""

DICTIONARY_FILE_PATH = "data/5_letter_words_spellchecked.txt"


__all__ = ["dictionary"]


class Dictionary:
    def __init__(self):
        with open(DICTIONARY_FILE_PATH) as file:
            self.words = file.readlines()
        self.words = [word.strip() for word in self.words]


dictionary = Dictionary()
