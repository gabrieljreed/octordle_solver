DICTIONARY_FILE_PATH = "5_letter_words_spellchecked.txt"


class Dictionary:
    def __init__(self):
        with open(DICTIONARY_FILE_PATH) as file:
            self.words = file.readlines()
        self.words = [word.strip() for word in self.words]


dictionary = Dictionary()
correct_letters = ["", "", "", "", ""]
misplaced_letters = [("R", 1), ("N", 3), ("E", 4), ("D", 0), ("N", 2), ("E", 3), ("R", 4)]
incorrect_letters = ["C", "A", "I"]


filtered_words = []
for word in dictionary.words:
    if len(word) != 5:
        continue

    # # Check if the word contains the correct letters in the correct positions
    # if any(word[i] != letter for i, letter in enumerate(correct_letters) if letter):
    #     continue

    # Check if the word contains the misplaced letters
    if any(letter[0] not in word for letter in misplaced_letters):
        continue

    if any(word[position] == letter for letter, position in misplaced_letters):
        continue

    # Check if the word contains any of the incorrect letters
    if any(letter in word for letter in incorrect_letters):
        continue

    filtered_words.append(word)

print(f"({len(filtered_words):04d}) filtered_words")
for obj in filtered_words:
    print(obj)
print("---")
