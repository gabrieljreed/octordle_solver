from wordle_solver.dictionary import Dictionary
from wordle_solver.generate_groups import (
    get_best_word_groups,
    print_group_info,
    get_best_word_groups_parallel,
    get_all_answer_possibilities,
)
from wordle_solver.solver import filter_words
from wordle_solver.utils import clear_screen


if __name__ == "__main__":
    remaining_words = Dictionary().words.copy()
    correct_letters = ["", "", "A", "", ""]
    misplaced_letters = [("R", 1), ("E", 4)]
    incorrect_letters = ["C", "N"]
    remaining_words = filter_words(remaining_words, correct_letters, misplaced_letters, incorrect_letters)
    for word in remaining_words:
        print(word)
    print(len(remaining_words))

    possibilities = get_all_answer_possibilities(remaining_words)
    for possibility in possibilities:
        print(possibility)
    print(len(possibilities))
    # best_group, best_word = get_best_word_groups_parallel(remaining_words)
    # print_group_info(best_group, best_word)
