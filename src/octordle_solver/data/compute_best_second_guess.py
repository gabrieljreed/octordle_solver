from octordle_solver.generate_groups import get_all_answer_possibilities
from octordle_solver.solver import filter_words
from octordle_solver.dictionary import dictionary
import itertools
from pathlib import Path
import json


output_file = Path(__file__).parent / "best_second_guesses.json"
output_file.touch()


if __name__ == "__main__":
    all_possibilities = list(itertools.product([0, 1, 2], repeat=5))
    starting_guess = "CRANE"

    best_second_guesses = {}
    num_invalid_states = 0

    for possibility in all_possibilities:
        print(possibility)

        correct_letters = ["", "", "", "", ""]
        incorrect_letters = []
        misplaced_letters = []

        for i, state in enumerate(possibility):
            letter = starting_guess[i]
            if state == 0:
                correct_letters[i] = letter
            elif state == 1:
                misplaced_letters.append((letter, i))
            elif state == 2:
                incorrect_letters.append(letter)
            print(i, state)

        print(f"{correct_letters = }")
        print(f"{incorrect_letters = }")
        print(f"{misplaced_letters = }")

        remaining_words = filter_words(
            dictionary.valid_answers.copy(),
            correct_letters,
            misplaced_letters,
            incorrect_letters,
        )
        print(f"{len(remaining_words) = }")
        if len(remaining_words) == 0:
            print(f"No remaining words for {possibility}")
            num_invalid_states += 1
            continue

        guesses = get_all_answer_possibilities(remaining_words, dictionary.valid_guesses.copy())
        if len(guesses) == 0:
            print(f"No possible words for {possibility}")
            continue
        possibility_key = ""
        for letter in possibility:
            possibility_key += str(letter)
        best_second_guesses[possibility_key] = guesses[0].word
        print(possibility_key, guesses[0].word)

    print(best_second_guesses)
    print(f"{num_invalid_states = }")

    with open(output_file, "w") as f:
        json.dump(best_second_guesses, f, indent=4)
