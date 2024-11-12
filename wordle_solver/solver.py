from pprint import pprint

DICTIONARY_FILE_PATH = "data/5_letter_words_spellchecked.txt"


def generate_alphabet_count_dict() -> dict:
    return {
        "a": 0,
        "b": 0,
        "c": 0,
        "d": 0,
        "e": 0,
        "f": 0,
        "g": 0,
        "h": 0,
        "i": 0,
        "j": 0,
        "k": 0,
        "l": 0,
        "m": 0,
        "n": 0,
        "o": 0,
        "p": 0,
        "q": 0,
        "r": 0,
        "s": 0,
        "t": 0,
        "u": 0,
        "v": 0,
        "w": 0,
        "x": 0,
        "y": 0,
        "z": 0,
    }


def count_frequencies_overall(words: list) -> dict:
    """Count the frequency of each letter in the words."""
    output_dict = generate_alphabet_count_dict()
    for word in words:
        for letter in word:
            if letter.isalpha():
                output_dict[letter.lower()] += 1

    return output_dict


def count_frequencies_by_position(words: list) -> dict:
    """Count the frequency of each letter in each position of the words."""
    output_dict = {
        0: generate_alphabet_count_dict(),
        1: generate_alphabet_count_dict(),
        2: generate_alphabet_count_dict(),
        3: generate_alphabet_count_dict(),
        4: generate_alphabet_count_dict(),
    }
    for word in words:
        for i, letter in enumerate(word):
            if letter.isalpha():
                output_dict[i][letter.lower()] += 1

    return output_dict


def sort_output_dict(output_dict: dict) -> list[tuple]:
    return [(k, v) for k, v in sorted(output_dict.items(), key=lambda item: item[1], reverse=True)]


class GameState:
    def __init__(self):
        self.correct_letters = ["", "", "", "", ""]
        self.misplaced_letters = []
        self.incorrect_letters = []


def generate_game_states(word):
    states = []

    for i in range(5):
        state = GameState()
        state.correct_letters[i] = word[i]
        states.append(state)

    return states


def get_groups_for_word(word: str, remaining_words: list[str]) -> list[list[str]]:
    """Split the remaining words into groups based on the similarity to the word."""
    groups = []

    for letter in word:
        group = []
        for remaining_word in remaining_words:
            pass

        if group:
            groups.append(group)

    return groups


class Dictionary:
    def __init__(self):
        with open(DICTIONARY_FILE_PATH) as file:
            self.words = file.readlines()
        self.words = [word.strip() for word in self.words]


dictionary = Dictionary()
correct_letters = ["", "", "A", "", ""]
misplaced_letters = [("E", 4), ("R", 1), ("Y", 1)]
incorrect_letters = ["C", "N", "S", "L", "P", "H"]


filtered_words = []
for word in dictionary.words:
    if len(word) != 5:
        continue

    # # Check if the word contains the correct letters in the correct positions
    if any(word[i] != letter for i, letter in enumerate(correct_letters) if letter):
        continue

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

# frequencies = count_frequencies_by_position(filtered_words)
# pprint(frequencies)
# all_sorted_frequencies = {}
# for position, frequency in frequencies.items():
#     sorted_frequencies = sort_output_dict(frequency)
#     pprint(sorted_frequencies)
#     all_sorted_frequencies[position] = sorted_frequencies

frequencies = count_frequencies_overall(filtered_words)
result = sort_output_dict(frequencies)
# pprint(result)

scored_words = {word: 0 for word in filtered_words}
i = 0
CUTOFF_VALUE = 100
for word in filtered_words:
    i += 1
    if i > CUTOFF_VALUE:
        break
    for letter in word:
        scored_words[word] += frequencies[letter.lower()]

result = sort_output_dict(scored_words)

pprint(result)

# Prune all words from the list that have duplicate letters
pruned_words = []
for word in filtered_words:
    if len(set(word)) == 5:
        pruned_words.append(word)

print(f"({len(pruned_words):04d}) pruned_words")
for obj in pruned_words:
    print(obj)
print("---")
