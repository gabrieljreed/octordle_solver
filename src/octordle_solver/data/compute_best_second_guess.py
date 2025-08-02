"""Compute the best second guess for all answer possibilities."""

import itertools
import json
import time
from pathlib import Path

from octordle_solver.dictionary import dictionary
from octordle_solver.solver import filter_words, get_all_answers

output_file = Path(__file__).parent / "best_second_guesses.json"
output_file.touch()


if __name__ == "__main__":
    all_possibilities = list(itertools.product([0, 1, 2], repeat=5))
    starting_guess = "CRANE"

    best_second_guesses = {}
    num_invalid_states = 0

    start_time = time.time()

    for possibility in all_possibilities:

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

        print(f"{correct_letters=}")
        print(f"{incorrect_letters=}")
        print(f"{misplaced_letters=}")

        remaining_words = filter_words(
            dictionary.valid_answers.copy(),
            correct_letters,
            misplaced_letters,
            incorrect_letters,
        )
        print(f"{len(remaining_words)=}")
        if len(remaining_words) == 0:
            print(f"No remaining words for {possibility}")
            num_invalid_states += 1
            continue

        guesses = get_all_answers(remaining_words, dictionary.valid_guesses.copy())
        if len(guesses) == 0:
            print(f"No possible words for {possibility}")
            continue
        possibility_key = ""
        for letter_possibility in possibility:
            possibility_key += str(letter_possibility)
        best_second_guesses[possibility_key] = guesses[0].word
        print(possibility_key, guesses[0].word)

    print(best_second_guesses)
    print(f"{num_invalid_states=}")

    end_time = time.time()

    print(f"Ran in {end_time - start_time:02f} seconds")

    with open(output_file, "w") as f:
        json.dump(best_second_guesses, f, indent=4)
