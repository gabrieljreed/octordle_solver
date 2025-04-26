"""Scratch pad for trying things out."""

import time

from octordle_solver.dictionary import Dictionary, dictionary
from octordle_solver.generate_groups import get_all_answer_possibilities
from octordle_solver.solver import filter_words

if __name__ == "__main__":
    remaining_words = Dictionary().valid_answers.copy()
    correct_letters = ["", "", "", "", ""]
    misplaced_letters = [("E", 4)]
    incorrect_letters = ["C", "R", "A", "N"]
    remaining_words = filter_words(remaining_words, correct_letters, misplaced_letters, incorrect_letters)
    start_time = time.time()

    possibilities = get_all_answer_possibilities(remaining_words, dictionary.valid_guesses.copy())
    end_time = time.time()
    print(end_time - start_time)
