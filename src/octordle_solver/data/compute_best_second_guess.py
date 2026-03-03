"""Compute the best second guess for all answer possibilities."""

from tqdm import tqdm
import itertools
import json
import time
from pathlib import Path

from octordle_solver.solver import Puzzle
from octordle_solver.constants import STARTING_GUESS

output_file = Path(__file__).parent / "best_second_guesses.json"
output_file.touch()


def main():
    """Compute the best second guess for all answer possibilities."""
    all_possibilities = list(itertools.product([0, 1, 2], repeat=5))

    best_second_guesses = {}
    num_invalid_states = 0

    start_time = time.time()

    with tqdm(
        all_possibilities,
        total=len(all_possibilities),
        desc="Evaluating possibilities",
        unit="state",
    ) as progress_bar:
        for possibility in progress_bar:
            puzzle = Puzzle()
            puzzle.make_guess(STARTING_GUESS, list(possibility))
            guess_display = str(puzzle.guesses[0])
            remaining_words = f"{len(puzzle.remaining_words)} remaining word(s)"

            if len(puzzle.remaining_words) == 0:
                num_invalid_states += 1
                progress_bar.set_postfix_str(f"guess={guess_display} | {remaining_words} | invalid state")
                continue

            if len(puzzle.all_answers) == 0:
                progress_bar.set_postfix_str(f"guess={guess_display} | {remaining_words} | no possible words")
                continue

            possibility_key = ""
            for letter_possibility in possibility:
                possibility_key += str(letter_possibility)
            best_second_guess = puzzle.all_answers[0].word
            best_second_guesses[possibility_key] = best_second_guess

            progress_bar.set_postfix_str(
                f"guess={guess_display} | {remaining_words} | Best guess: {best_second_guess}"
            )

    print(f"{num_invalid_states=}")
    end_time = time.time()
    print(f"Ran in {end_time - start_time:02f} seconds")
    with open(output_file, "w", newline="\n") as f:
        json.dump(best_second_guesses, f, indent=4)
        f.write("\n")


if __name__ == "__main__":
    main()
