dictionary_file_path = "data/5_letter_words_spellchecked.txt"


__all__ = ["dictionary"]


class Dictionary:
    def __init__(self):
        with open(dictionary_file_path) as file:
            self.words = file.readlines()
        self.words = [word.strip() for word in self.words]


dictionary = Dictionary()
