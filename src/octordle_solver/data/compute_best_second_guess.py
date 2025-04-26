"""Compute the best second guess for all answer possibilities."""

import itertools
import json
import logging
import time
from pathlib import Path

from octordle_solver.dictionary import dictionary
from octordle_solver.generate_groups import get_all_answer_possibilities
from octordle_solver.solver import filter_words

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add a handler if there isn't one already
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

output_file = Path(__file__).parent / "best_second_guesses.json"
output_file.touch()


def compute_best_second_guess(word: str):
    """Compute best second guess for the given word.

    Args:
        word (str): The word to compute a guess for.
    """
    all_possibilities = list(itertools.product([0, 1, 2], repeat=5))

    best_second_guesses = {}
    num_invalid_states = 0

    for possibility in all_possibilities:
        logger.debug(possibility)

        correct_letters = ["", "", "", "", ""]
        incorrect_letters = []
        misplaced_letters = []

        for i, state in enumerate(possibility):
            letter = word[i]
            if state == 0:
                correct_letters[i] = letter
            elif state == 1:
                misplaced_letters.append((letter, i))
            elif state == 2:
                incorrect_letters.append(letter)
            logger.debug(f"{i}, {state}")

        logger.debug(f"{correct_letters = }")
        logger.debug(f"{incorrect_letters = }")
        logger.debug(f"{misplaced_letters = }")

        remaining_words = filter_words(
            dictionary.valid_answers.copy(),
            correct_letters,
            misplaced_letters,
            incorrect_letters,
        )
        logger.debug(f"{len(remaining_words) = }")
        if len(remaining_words) == 0:
            logger.debug(f"No remaining words for {possibility}")
            num_invalid_states += 1
            continue

        guesses = get_all_answer_possibilities(remaining_words, dictionary.valid_guesses.copy())
        if len(guesses) == 0:
            logger.debug(f"No possible words for {possibility}")
            continue
        possibility_key = ""
        for letter_possibility in possibility:
            possibility_key += str(letter_possibility)
        best_second_guesses[possibility_key] = guesses[0].word
        logger.debug(f"{possibility_key}, {guesses[0].word}")

    logger.debug(best_second_guesses)
    logger.debug(f"{num_invalid_states = }")

    return best_second_guesses


if __name__ == "__main__":
    starting_guesses = [
        "CRANE",
        "ADIEU",
        "STARE",
        "AUDIO",
        "RAISE",
        "SLATE",
        "ARISE",
        "TRAIN",
        "IRATE",
        "GREAT",
    ]
    best_second_guesses = {}
    start_time = time.time()
    for guess in starting_guesses:
        logger.debug(f"PROCESSING FOR {guess}")
        best_second_guesses[guess] = compute_best_second_guess(guess)

    end_time = time.time()
    logger.info(f"Finished in {end_time - start_time} seconds")

    with open(output_file, "w") as f:
        json.dump(best_second_guesses, f, indent=4)
