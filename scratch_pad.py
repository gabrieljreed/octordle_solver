"""Scratch pad for trying things out."""

from octordle_solver.dictionary import Dictionary
from octordle_solver.solver import filter_words

if __name__ == "__main__":
    remaining_words = Dictionary().valid_answers.copy()
    correct_letters = ["", "", "", "", ""]
    misplaced_letters = [("E", 4), ("S", 4), ("T", 3)]
    incorrect_letters = ["C", "R", "A", "N", "D", "O", "L"]
    remaining_words = filter_words(remaining_words, correct_letters, misplaced_letters, incorrect_letters)
    for word in remaining_words:
        print(word)
    print(len(remaining_words))
