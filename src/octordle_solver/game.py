"""Wordle Clone."""

import random
from typing import Optional, Set

from colorama import Back, Style

from .dictionary import Dictionary
from .solver import filter_words
from .utils import clear_screen


class Game:
    """Game class for Wordle Clone."""

    def __init__(self, word: Optional[str] = None, clear_screen: bool = True) -> None:
        """Initialize the game.

        Args:
            word (Optional[str], optional): The word to use for the game, if None, a random word is chosen.
        """
        self.dictionary = Dictionary()
        if word is None:
            self.word = random.choice(self.dictionary.words)
        else:
            self.word = word

        self.guessed_letters: Set[str] = set()
        self.guessed_words: list[str] = []
        self.num_tries = 6

        self.correct_letters: list[str] = ["", "", "", "", ""]
        self.misplaced_letters: list[tuple[str, int]] = []
        self.incorrect_letters: list[str] = []

        self.remaining_words = self.dictionary.words.copy()

        # Settings
        self._clear_screen = clear_screen

    def __str__(self) -> str:
        """Return a string representation of the game state."""
        result = [
            f"Word: {self.word}",
            f"Correct: {self.correct_letters}",
            f"Misplaced: {self.misplaced_letters}",
            f"Incorrect: {self.incorrect_letters}",
            f"Remaining words: {len(self.remaining_words)}",
        ]
        return "\n".join(result)

    def guess(self, word: str) -> None:
        """Guess a word.

        Args:
            word (str): The word to guess.
        """
        word = word.upper()
        self.parse_guess(word)
        self.guessed_words.append(word)
        if self._clear_screen:
            clear_screen()
        for word in self.guessed_words:
            self.print_word(word)

    def parse_guess(self, guess: str) -> None:
        """Parse the guess into correct, misplaced, and incorrect letters.

        Args:
            guess (str): The word to parse.
        """
        for i, (guess_letter, actual_letter) in enumerate(zip(guess, self.word)):
            if guess_letter == actual_letter:
                self.correct_letters[i] = guess_letter
            elif guess_letter in self.word:
                self.misplaced_letters.append((guess_letter, i))
            else:
                self.incorrect_letters.append(guess_letter)

    def print_word(self, word) -> None:
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

    def play(self) -> None:
        """Play the game."""
        while True:
            self.remaining_words = filter_words(
                self.remaining_words, self.correct_letters, self.misplaced_letters, self.incorrect_letters
            )
            print(f"({len(self.remaining_words)}) words remaining")
            guess = input("Enter a guess: ")
            self.guess(guess)
            if guess == self.word:
                print("You win!")
                break
            self.num_tries -= 1
            if self.num_tries == 0:
                print(f"You lose! The word was {self.word}")
                break
