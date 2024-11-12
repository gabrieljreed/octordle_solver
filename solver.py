from wordle_solver.utils import clear_screen


STARTING_GUESS = "CRANE"


if __name__ == "__main__":
    guessed_words = []
    clear_screen()
    best_guess = STARTING_GUESS
    while True:
        clear_screen()
        print(f"Best guess: {best_guess}")
        user_input = input("Enter a word (q to quit): ")

        if user_input == "q":
            break

        if user_input == "":
            selected_word = best_guess
        else:
            selected_word = user_input.upper()

        print(f"Selected word: {selected_word}")

        user_input = input("Enter the results for the guess:")
        print(user_input)
        # TODO: Make this line up with the user's guess

        # Filter words, give a new best guess

        # Also give an option to see other good guesses

        # Give a verbose/more details option to see groups, etc.
