from octordle_solver.dictionary import Dictionary
from octordle_solver.generate_groups import (
    get_best_word_groups,
    get_best_word_groups_parallel,
    print_group_info,
)
from octordle_solver.solver import filter_words
from octordle_solver.utils import clear_screen

if __name__ == "__main__":
    remaining_words = Dictionary().words.copy()
    correct_letters = ["", "", "I", "N", "E"]
    misplaced_letters = [("S", 3)]
    incorrect_letters = ["C", "R", "A", "H", "O", "T"]
    remaining_words = filter_words(remaining_words, correct_letters, misplaced_letters, incorrect_letters)
    for word in remaining_words:
        print(word)
    print(len(remaining_words))

    best_group, best_word = get_best_word_groups_parallel(remaining_words)
    print_group_info(best_group, best_word)

    """I think the problem is that once we get to the last few words, we need to start guessing actual remaining words - or at least prioritizing them heavily over words it couldn't possibly be. I need a cutoff value where I start guessing actual words.

    I think I could store all the groups and then sort them, that way you could see other possible good guesses

    """
