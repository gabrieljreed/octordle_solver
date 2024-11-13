from wordle_solver.utils import clear_screen
from wordle_solver.solver import filter_words
from wordle_solver.dictionary import Dictionary
from wordle_solver.generate_groups import get_best_word_groups, print_group_info

from colorama import Back, Style


STARTING_GUESS = "CRANE"


def show_help():
    print("Press q to quit")
    print("Press ? for help")


if __name__ == "__main__":
    guessed_words = []
    clear_screen()
    best_guess = STARTING_GUESS
    all_words = Dictionary().words.copy()
    remaining_words = Dictionary().words.copy()
    correct_letters = ["", "", "", "", ""]
    incorrect_letters = []
    misplaced_letters = []
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

        if user_input == "?":
            show_help()

        if user_input == "":
            selected_word = best_guess
        else:
            selected_word = user_input.upper()

        # Input results
        clear_screen()
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

        guessed_words.append(colored_word)

        # Filter words, give a new best guess
        remaining_words = filter_words(remaining_words, correct_letters, misplaced_letters, incorrect_letters)
        best_group, best_guess = get_best_word_groups(remaining_words, verbose=True)
        print_group_info(best_group, best_guess)

        # Also give an option to see other good guesses

        # Give a verbose/more details option to see groups, etc.
