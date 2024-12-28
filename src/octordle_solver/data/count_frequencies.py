from pprint import pprint


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


if __name__ == "__main__":
    input_file = "5_letter_words_spellchecked.txt"
    words = []
    with open(input_file, "r") as input_file:
        words = input_file.read().split()

    frequencies = count_frequencies_by_position(words)
    pprint(frequencies)
    all_sorted_frequencies = {}
    for position, frequency in frequencies.items():
        sorted_frequencies = sort_output_dict(frequency)
        pprint(sorted_frequencies)
        all_sorted_frequencies[position] = sorted_frequencies
    # sorted_frequencies = sort_output_dict(frequencies)
    # pprint(sorted_frequencies)

    output_file = "5_letter_words_spellchecked_frequencies_letter.txt"
    with open(output_file, "w") as file:
        for position, sorted_frequencies in all_sorted_frequencies.items():
            file.write(f"Position {position}:\n")
            for letter, frequency in sorted_frequencies:
                file.write(f"{letter}: {frequency}\n")
            file.write("\n")
