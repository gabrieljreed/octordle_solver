"""Solve wordle for all words in the dictionary and see how many guesses it takes."""

import json
from pathlib import Path

from colorama import Fore

from octordle_solver.dictionary import dictionary
from octordle_solver.solver import Puzzle, get_wordle_feedback_cached
from octordle_solver.utils import catchtime

STARTING_WORD = "SLATE"


def print_word(word, answer) -> None:
    """Print the word with the guessed letters highlighted."""
    word = word.upper()
    output_string = ""
    for guess_letter, actual_letter in zip(word, answer):
        if guess_letter == actual_letter:
            output_string += Fore.GREEN + guess_letter + Fore.RESET
        elif guess_letter in answer:
            output_string += Fore.YELLOW + guess_letter + Fore.RESET
        else:
            output_string += guess_letter

    print(output_string)


def play_game_for_word(answer: str, starting_word: str):
    """Play out a wordle game with a given answer and starting word."""
    guess = starting_word
    puzzle = Puzzle()
    num_guesses = 0
    guesses = []

    while True:
        guesses.append(guess)
        num_guesses += 1
        result = get_wordle_feedback_cached(guess, answer)
        print_word(guess, answer)
        if result == [0, 0, 0, 0, 0]:
            break

        puzzle.make_guess(guess, result)
        if len(puzzle.remaining_words) < 1:
            raise RuntimeError("Unable to solve puzzle")

        guess = puzzle.all_answers[0].word  # TODO: Make this a property or something

    print(f"Solved {answer} in {num_guesses} guesses")
    return num_guesses


def solve_for_all_words(starting_word: str = STARTING_WORD):
    """Solve wordle for all words in the dictionary."""
    results = []

    for word in dictionary.valid_answers:
        result = play_game_for_word(word, starting_word)
        results.append((word, result))

    return results


if __name__ == "__main__":
    with catchtime():
        results = solve_for_all_words()

    path = Path(__file__).parent / "solve_for_all_words.txt"
    path.write_text(json.dumps(results, indent=4))
