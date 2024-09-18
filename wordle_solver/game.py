import os
import random
from enum import Enum
from typing import Optional, Tuple, List
from colorama import Fore, Back, Style


DICTIONARY_FILE_PATH = "5_letter_words_spellchecked.txt"


class Dictionary:
    def __init__(self):
        with open(DICTIONARY_FILE_PATH) as file:
            self.words = file.readlines()
        self.words = [word.strip() for word in self.words]


dictionary = Dictionary()


class TileState(Enum):
    UNSET = 0
    CORRECT = 1
    INCORRECT = 2


class Game:
    def __init__(self, word: Optional[str] = None) -> None:
        if word is None:
            self.word = random.choice(dictionary.words)
        else:
            self.word = word
        self.guessed_letters = set()
        self.guessed_words = []
        self.num_tries = 6

        self.correct_letters = []
        self.misplaced_letters = []
        self.incorrect_letters = []

    def guess(self, word: str) -> bool:
        """Guess a word."""
        word = word.upper()
        self.parse_guess(word)
        self.guessed_words.append(word)
        self.clear_screen()
        for word in self.guessed_words:
            self.print_word(word)

    def clear_screen(self):
        """Clear the screen."""
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    def parse_guess(self, guess: str) -> Tuple[List[str], List[str], List[str]]:
        """Parse the guess into correct, misplaced, and incorrect letters."""
        for i, (guess_letter, actual_letter) in enumerate(zip(guess, self.word)):
            if guess_letter == actual_letter:
                self.correct_letters.append(guess_letter)
            elif guess_letter in self.word:
                self.misplaced_letters.append((guess_letter, i))
            else:
                self.incorrect_letters.append(guess_letter)

    def print_word(self, word):
        """Print the word with the guessed letters highlighted."""
        word = word.upper()
        output_string = ""
        for guess_letter, actual_letter in zip(word, self.word):
            self.guessed_letters.add(guess_letter)
            if guess_letter == actual_letter:
                output_string += Back.GREEN + guess_letter + Back.RESET
            elif guess_letter in self.word:
                output_string += Back.YELLOW + guess_letter + Back.RESET
            else:
                output_string += Style.DIM + guess_letter + Style.RESET_ALL

        print(output_string)

    def play(self):
        while True:
            filtered_words = self.filter_words()
            print(f"({len(filtered_words)}) words remaining")
            guess = input("Enter a guess: ")
            self.guess(guess)
            if guess == self.word:
                print("You win!")
                break
            self.num_tries -= 1
            if self.num_tries == 0:
                print(f"You lose! The word was {self.word}")
                break

    def filter_words(self):
        """Filter the words in the dictionary based on the guessed letters."""
        filtered_words = []

        for word in dictionary.words:
            if len(word) != 5:
                continue

            # Check if the word contains the correct letters in the correct positions
            if any(word[i] != letter for i, letter in enumerate(self.correct_letters) if letter):
                continue

            # Check if the word contains the misplaced letters
            if any(letter[0] not in word for letter in self.misplaced_letters):
                continue

            if any(word[position] == letter for letter, position in self.misplaced_letters):
                continue

            # Check if the word contains any of the incorrect letters
            if any(letter in word for letter in self.incorrect_letters):
                continue

            filtered_words.append(word)

        return filtered_words

# class GamePlayer:
#     def __init__(self, num_guesses: int = 6) -> None:
#         self.game = Game()
#         self.num_guesses = num_guesses

#     def play(self) -> None:
#         while True:
#             guess = input("Enter a guess: ")
#             self.game.guess(guess)
#             if guess == self.game.word:
#                 print("You win!")
#                 break
#             self.num_guesses -= 1
#             if self.num_guesses == 0:
#                 print(f"You lose! The word was {self.game.word}")
#                 break


if __name__ == "__main__":
    game = Game()
    game.play()
