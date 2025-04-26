"""Command line Wordle solver."""

from colorama import Back, Style

from octordle_solver.dictionary import dictionary
from octordle_solver.generate_groups import (
    get_all_answer_possibilities,
    get_best_word_groups,
    get_best_word_groups_parallel,
    print_group_info,
)
from octordle_solver.solver import filter_words
from octordle_solver.utils import clear_screen

STARTING_GUESS = "CRANE"


def show_help():
    """Show help options."""
    print("q\t\t Quit the program")
    print("?\t\t Show help")
    print("g\t\t Show group information")


if __name__ == "__main__":
    clear_screen()

    guessed_words = []
    best_guess = STARTING_GUESS
    all_words = dictionary.words.copy()
    remaining_words = dictionary.words.copy()
    correct_letters = ["", "", "", "", ""]
    incorrect_letters = []
    misplaced_letters = []
    best_group = None

    while True:
        clear_screen()
        for word in guessed_words:
            print(word)

        # Input guess
        print(f"{len(remaining_words)} remaining words")
        print(f"Best guess: {best_guess}")
        user_input = input("Enter a word (q to quit): ")

        if user_input == "q":
            break

        elif user_input == "?":
            show_help()

        elif user_input == "g":
            print_group_info(best_group, best_guess)

        # FIXME: If the user selects ? or g, we need to re-prompt for a guess

        if user_input == "":
            selected_word = best_guess
        else:
            selected_word = user_input.upper()

        # Input results
        clear_screen()
        # TODO: Figure out a better way to input results
        print("Enter the results for the guess")
        print("Y - Yes (Correct letter - Green)")
        print("M - Misplaced (Misplaced letter - Yellow)")
        print("N - No (Incorrect letter - Gray)")
        print(selected_word)
        user_input = input()

        if user_input.lower() == "q":
            break

        if user_input == "?":
            show_help()

        guess_result = user_input.upper()

        colored_word = ""
        for i, letter in enumerate(selected_word):
            if guess_result[i] == "Y":
                colored_word += Back.GREEN + letter + Back.RESET
                correct_letters[i] = letter
            elif guess_result[i] == "M":
                colored_word += Back.YELLOW + letter + Back.RESET
                misplaced_letters.append((letter, i))
            else:
                colored_word += Style.DIM + letter + Style.RESET_ALL
                incorrect_letters.append(letter)

        # A letter can be correct or misplaced and also show up in the incorrect word list, filter that out
        new_incorrect_letters = []
        misplaced_letters_no_positions = [letter[0] for letter in misplaced_letters]
        for letter in incorrect_letters:
            if letter in correct_letters or letter in misplaced_letters_no_positions:
                continue
            new_incorrect_letters.append(letter)
        incorrect_letters = new_incorrect_letters

        guessed_words.append(colored_word)

        if guess_result == "YYYYY":
            clear_screen()
            for word in guessed_words:
                print(word)
            break

        # Filter words, give a new best guess
        remaining_words = filter_words(remaining_words, correct_letters, misplaced_letters, incorrect_letters)
        print(f"{correct_letters = }")
        print(f"{misplaced_letters = }")
        print(f"{incorrect_letters = }")
        print(f"{len(remaining_words)} remaining words")
        possibilities = get_all_answer_possibilities(remaining_words)
        best_possibility = possibilities[0]
        best_guess = best_possibility.word
        best_group = best_possibility.groups

        # Also give an option to see other good guesses

        # Give a verbose/more details option to see groups, etc.


"""
Basically, I think I can just have it not in a for loop, but just have two functions

def get_guess():


def get_results():

Each one can return an exit code, and based off the exit code, you call the other function, call the same function again (like if you get help or switch to verbose mode), call the other function, or exit the program.
"""
