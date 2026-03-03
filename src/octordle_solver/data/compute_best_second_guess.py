"""Compute the best second guess for all answer possibilities."""

import itertools
import json
import time
from pathlib import Path

from octordle_solver.solver import Puzzle
from octordle_solver.constants import STARTING_GUESS

output_file = Path(__file__).parent / "best_second_guesses.json"
output_file.touch()


if __name__ == "__main__":
    all_possibilities = list(itertools.product([0, 1, 2], repeat=5))

    best_second_guesses = {}
    num_invalid_states = 0

    start_time = time.time()

    for possibility in all_possibilities:
        puzzle = Puzzle()
        puzzle.make_guess(STARTING_GUESS, list(possibility))
        print(puzzle.guesses[0])
        print(f"{len(puzzle.remaining_words)} remaining word(s)")
        if len(puzzle.remaining_words) == 0:
            num_invalid_states += 1
            continue
        if len(puzzle.all_answers) == 0:
            print(f"No possible words for {possibility}")
            continue
        possibility_key = ""
        for letter_possibility in possibility:
            possibility_key += str(letter_possibility)
        best_second_guesses[possibility_key] = puzzle.all_answers[0].word
        print(f"Best guess: {puzzle.all_answers[0].word}")

    print(f"{num_invalid_states=}")
    end_time = time.time()
    print(f"Ran in {end_time - start_time:02f} seconds")
    with open(output_file, "w", newline="\n") as f:
        json.dump(best_second_guesses, f, indent=4)
        f.write("\n")
