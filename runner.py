from pprint import pprint

from wordle_solver.dictionary import Dictionary
from wordle_solver.generate_groups import get_best_word_groups, print_group_info
from wordle_solver.solver import filter_plurals, filter_words

if __name__ == "__main__":
    dictionary = Dictionary()
    correct_letters = ["", "", "", "", ""]
    misplaced_letters = []
    incorrect_letters = []

    no_plurals = filter_plurals(dictionary.words)

    remaining_words = filter_words(no_plurals, correct_letters, misplaced_letters, incorrect_letters)

    pprint(remaining_words)

    best_groups, best_word = get_best_word_groups(remaining_words, verbose=False)
    print_group_info(best_groups, best_word)
