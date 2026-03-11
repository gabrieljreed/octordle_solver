"""Compute the best second guess for all answer possibilities."""

import itertools
import json
from pathlib import Path
from typing import Callable, Iterable, Sequence

from tqdm import tqdm

from octordle_solver.solver import Puzzle
from octordle_solver.constants import STARTING_GUESS

output_file = Path(__file__).parent / "best_second_guesses.json"


def get_all_possibilities() -> list[tuple[int, ...]]:
    """Generate all possible response patterns for a 5-letter guess."""
    return list(itertools.product([0, 1, 2], repeat=5))


def possibility_to_key(possibility: Sequence[int]) -> str:
    """Convert a possibility tuple/list to the persisted dictionary key."""
    return "".join(str(letter_possibility) for letter_possibility in possibility)


def compute_best_second_guesses(
    possibilities: Iterable[Sequence[int]],
    *,
    puzzle_cls=Puzzle,
    starting_guess: str = STARTING_GUESS,
    status_callback: Callable[[str], None],
) -> tuple[dict[str, str], int]:
    """Compute best second guesses and return mapping + invalid state count."""
    best_second_guesses: dict[str, str] = {}
    num_invalid_states = 0

    for possibility in possibilities:
        puzzle = puzzle_cls()
        puzzle.make_guess(starting_guess, list(possibility))
        guess_display = str(puzzle.guesses[0])
        remaining_words_count = len(puzzle.remaining_words)
        remaining_words_str = f"{remaining_words_count:03d} remaining word(s)"

        if remaining_words_count == 0:
            num_invalid_states += 1
            status_message = f"guess={guess_display} | {remaining_words_str} | Best guess: -----"
            status_callback(status_message)
            continue

        if len(puzzle.all_answers) == 0:
            status_message = f"guess={guess_display} | {remaining_words_str} | Best guess: -----"
            status_callback(status_message)
            continue

        possibility_key = possibility_to_key(possibility)
        best_second_guess = puzzle.all_answers[0].word
        best_second_guesses[possibility_key] = best_second_guess

        status_message = f"guess={guess_display} | {remaining_words_str} | Best guess: {best_second_guess}"
        status_callback(status_message)

    return best_second_guesses, num_invalid_states


def write_best_second_guesses(results: dict[str, str], output_path: Path) -> None:
    """Write computed best second guesses to disk."""
    with open(output_path, "w", newline="\n") as file_handle:
        json.dump(results, file_handle, indent=4)
        file_handle.write("\n")


def main():
    """Compute the best second guess for all answer possibilities."""
    all_possibilities = get_all_possibilities()

    with tqdm(
        total=len(all_possibilities),
        desc="Evaluating possibilities",
        unit="state",
    ) as progress_bar:

        def update_progress(status_message: str) -> None:
            progress_bar.set_postfix_str(status_message)
            progress_bar.update()

        best_second_guesses, num_invalid_states = compute_best_second_guesses(
            all_possibilities,
            status_callback=update_progress,
        )

    print(f"{num_invalid_states} invalid states found.")
    write_best_second_guesses(best_second_guesses, output_file)


if __name__ == "__main__":
    main()
