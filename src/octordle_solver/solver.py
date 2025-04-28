"""Solve Wordle puzzles."""

import concurrent.futures
import json
from collections import defaultdict
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

from colorama import Back, Style

from .dictionary import dictionary

CHUNK_SIZE = 10
PENALTY_WEIGHT = 0.1
REMAINING_WORD_BONUS = 2
SECOND_GUESS_PATH = Path(__file__).parent / "data" / "best_second_guesses.json"
with open(SECOND_GUESS_PATH, "r") as f:
    best_second_guesses = json.load(f)


class PossibilityState(Enum):
    """Enum representing the state of a letter in a Possibility."""

    INVALID = -1
    CORRECT = 0
    MISPLACED = 1
    INCORRECT = 2


class Group:
    """Class to represent a group of words for a given possibility."""

    def __init__(self, words: list[str], possibility):
        """Initialize the Group.

        Args:
            words (list[str]): List of words in the group.
            possibility (): The answer possibility
        """
        self.words: list[str] = words
        self.possibility = possibility

    def __str__(self):
        """Return the string representation of the group."""
        result = str(self.possibility)
        for word in self.words:
            result += f"\n\t{word}"
        return result

    def __repr__(self) -> str:
        """Return the string representation of the group."""
        return self.__str__()

    def __bool__(self):
        """Boolean override."""
        return bool(self.words)

    def __eq__(self, other: object) -> bool:
        """Equality override."""
        if not isinstance(other, Group):
            return False
        return self.words == other.words and self.possibility == other.possibility


class AnswerPossibility:
    """Class representing a possible answer."""

    def __init__(self, word: str, groups: list[Group]):
        """Initialize the AnswerPossibility."""
        self.word = word
        self.groups = groups

    @cached_property
    def max_group_size(self):
        """Size of the largest group in this AnswerPossibility."""
        if not self.groups:
            return -1
        return max(len(group.words) for group in self.groups)

    def __str__(self):
        """Return a string representation of the AnswerPossibility."""
        result = f"{self.word}: {len(self.groups)} groups, largest group {self.max_group_size}"
        # TODO: Improve color printout here
        for group in self.groups:
            result += f"\n\t{group}"
        return result

    def __gt__(self, other):
        """Overload > operator.

        If the number of groups is the same, favor smaller groups. Otherwise, favor more groups.
        """
        if len(self.groups) == len(other.groups):
            if len(self.groups) == 0:
                return True
            return max(len(group.words) for group in self.groups) < max(len(group.words) for group in other.groups)

        return len(self.groups) > len(other.groups)


def calculate_fitness_score(answer_possibility: AnswerPossibility, remaining_words: list[str]) -> float:
    """Return a fitness score for the given answer possibility and list of remaining words.

    Args:
        answer_possibility (AnswerPossibility): The AnswerPossibility to generate a fitness score for.
        remaining_words (list[str]): List of remaining words in the puzzle.

    Returns:
        (float): Computed score.
    """
    largest_group = max(len(group.words) for group in answer_possibility.groups)
    fitness = len(answer_possibility.groups) - (largest_group * PENALTY_WEIGHT)

    in_remaining_words = 1 if answer_possibility.word in remaining_words else 0
    remaining_words_bonus = 2 * in_remaining_words

    fitness += remaining_words_bonus

    return fitness


class Puzzle:
    """Class to hold the state of a single Wordle puzzle."""

    def __init__(self):
        """Initialize the puzzle."""
        self.remaining_words = dictionary.valid_answers.copy()
        self.valid_guesses = dictionary.valid_guesses.copy()
        self.correct_letters = ["", "", "", "", ""]
        self.misplaced_letters = []
        self.incorrect_letters = []
        self.all_answers = []
        self.all_answers_dict = {}

    def make_guess(self, word: str, result: str):
        """Guess a word.

        Args:
            word (str): Word that was guessed.
            result (str): Result of the word being guessed.
        """
        for i in range(5):
            letter = word[i]
            if result[i] == "Y":
                self.correct_letters[i] = letter
            elif result[i] == "M":
                self.misplaced_letters.append((letter, i))
            elif letter in self.correct_letters:
                continue
            else:
                self.incorrect_letters.append(letter)

        self.remaining_words = filter_words(
            self.remaining_words,
            self.correct_letters,
            self.misplaced_letters,
            self.incorrect_letters,
        )

        self.get_all_answers()

    def __str__(self):
        """Return the string representation of the state of the Puzzle."""
        result = f"Correct Letters: {self.correct_letters}\n"
        result += f"Misplaced Letters: {self.misplaced_letters}\n"
        result += f"Incorrect Letters: {self.incorrect_letters}"
        return result

    def get_all_answers(self) -> list[AnswerPossibility]:
        """Get all answers for the given state."""
        self.all_answers = get_all_answers(self.remaining_words)
        for answer in self.all_answers:
            self.all_answers_dict[answer.word] = answer
        return self.all_answers


def filter_words(
    words: list[str],
    correct_letters: list[str],
    misplaced_letters: list[tuple[str, int]],
    incorrect_letters: list[str],
) -> list:
    """Filter words.

    Args:
        words (list[str]): The words to filter.
        correct_letters (list[str]): Letters in the correct position.
        misplaced_letters (list[tuple[str, int]]): Letters that are misplaced, each entry should be the letter and the
            position it is NOT found in.
        incorrect_letters (list[str]): Letters that are incorrect (not in the word).
    """
    filtered_words = []
    for word in words:
        if len(word) != 5:
            continue

        # Check if the word contains the correct letters in the correct positions
        if any(word[i] != letter for i, letter in enumerate(correct_letters) if letter):
            continue

        # Check if the word contains the misplaced letters
        if any(letter[0] not in word for letter in misplaced_letters):
            continue

        if any(word[position] == letter for letter, position in misplaced_letters):
            continue

        # Check if the word contains any of the incorrect letters
        if any(letter in word for letter in incorrect_letters):
            continue

        filtered_words.append(word)

    return filtered_words


def get_cached_best_second_guess(answer_possibility: list[int]) -> Optional[str]:
    """Get the cached best second guess for the given answer possibility.

    Args:
        answer_possibility (list[int]): Answer Possibility
    """
    possibility_key = ""
    for i in answer_possibility:
        possibility_key += str(i)

    return best_second_guesses.get(possibility_key)


def pretty_print_group(group: Group, word: str):
    """Print a group in a nice format."""
    output_string = ""
    for i, letter in enumerate(word):
        if group.possibility[i] == 0:
            output_string += Back.GREEN + letter + Back.RESET
        elif group.possibility[i] == 1:
            output_string += Back.YELLOW + letter + Back.RESET
        else:
            output_string += Style.DIM + letter + Style.RESET_ALL
    print(output_string)

    for word in group.words:
        print(word)
    print("---")


def print_group_info(groups: Optional[list[Group]], word: Optional[str]) -> None:
    """Print information about the groups."""
    if not groups or not word:
        print("No groups found")
        return

    for group in groups:
        pretty_print_group(group, word)

    print(f"Num groups: {len(groups)}")
    print(f"Largest group: {max(len(group.words) for group in groups)}")


def get_wordle_feedback(guess: str, answer: str) -> list[int]:
    """Simulate Wordle feedback for a guess vs the real answer.

    Args:
        guess (str): The guessed word.
        answer (str): The answer.

    Returns:
        (list[int]): A list of 5 integers.
    """
    feedback = [PossibilityState.INCORRECT.value] * 5
    answer_chars: list[Union[None, str]] = list(answer)

    for i in range(5):
        if guess[i] == answer[i]:
            feedback[i] = PossibilityState.CORRECT.value
            answer_chars[i] = ""  # Mark as used

    for i in range(5):
        if feedback[i] == PossibilityState.INCORRECT.value and guess[i] in answer_chars:
            feedback[i] = PossibilityState.MISPLACED.value
            answer_chars[answer_chars.index(guess[i])] = ""  # Mark as used

    return feedback


def generate_groups(given_word: str, remaining_words: list[str]):
    """Generate groups.

    Args:
        given_word (str): The word to generate groups for.
        remaining_words (list[str]): The words that are still valid answers.

    Returns:
        (list[Group]): List of groups generated.
    """
    groups = defaultdict(list)

    for word in remaining_words:
        feedback = tuple(get_wordle_feedback(given_word, word))
        groups[feedback].append(word)

    return [Group(words, possibility) for possibility, words in groups.items()]


def create_chunks(list_to_chunk: list, chunk_size: int):
    """Create chunks from a given list."""
    for i in range(0, len(list_to_chunk), chunk_size):
        yield list_to_chunk[i : i + chunk_size]


def process_word_batch(args) -> list[tuple[str, list[Group]]]:
    """Generate groups for a given batch of words.

    Args:
        args (tuple): A tuple of the batch of words and the remaining words.

    Returns:
        list[tuple[str, list[Group]]]: List of results - tuples of the word and list of groups.
    """
    words_batch, remaining_words = args
    batch_results = []
    for word in words_batch:
        groups = generate_groups(word, remaining_words)
        batch_results.append((word, groups))
    return batch_results


def get_all_answers(remaining_words: list[str], valid_guesses: Optional[list[str]] = None) -> list[AnswerPossibility]:
    """Get all answer sorted best to worst.

    Args:
        remaining_words (list[str]): List of words words still possible given the game state.
        valid_guesses (list[str], optional): Valid guesses to use. If not provided, will use dictionary.valid_guesses.

    Returns:
        (list[AnswerPossibility]): List of AnswerPossibility objects.
    """
    if not valid_guesses:
        valid_guesses = dictionary.valid_guesses

    all_possibilities: list[AnswerPossibility] = []

    if len(remaining_words) == 1:
        word = remaining_words[0]
        groups = generate_groups(word, remaining_words)
        all_possibilities = [AnswerPossibility(word, groups)]

    words = remaining_words + dictionary.words

    batches = list(create_chunks(words, CHUNK_SIZE))

    with concurrent.futures.ProcessPoolExecutor() as executor:
        batch_args = [(batch, remaining_words) for batch in batches]
        for batch_result in executor.map(process_word_batch, batch_args):
            for word, groups in batch_result:
                all_possibilities.append(AnswerPossibility(word, groups))

    all_possibilities.sort(reverse=True)

    return all_possibilities


def get_best_guess_multiple_puzzles(puzzles: list[Puzzle]) -> str:
    """Get the best guess for a list of Puzzles.

    Args:
        puzzles (list[Puzzle]): List of Puzzles.

    Returns:
        (str): Best guess.
    """
    # If only 1 puzzle remains, return its best guess
    if len(puzzles) == 1:
        return puzzles[0].all_answers[0].word

    # If a puzzle can be solved in 1 turn (len(remaining_words) == 1), return that word
    for puzzle in puzzles:
        if len(puzzle.remaining_words) == 1:
            return puzzle.all_answers[0].word

    # If a puzzle can be solved in 2 turns (an answer possibility has max group size of 1), return that word
    for puzzle in puzzles:
        for answer in puzzle.all_answers:
            if answer.max_group_size == 1:
                return answer.word

    scored_guesses = []
    sets = [set(list(puzzle.all_answers_dict.keys())) for puzzle in puzzles]
    all_words = set.union(*sets)
    total_remaining_words = sum([len(puzzle.remaining_words) for puzzle in puzzles])
    for word in all_words:
        total_score = 0.0
        for puzzle in puzzles:
            answer_possibility = puzzle.all_answers_dict.get(word)
            if not answer_possibility:
                continue
            fitness_score = calculate_fitness_score(answer_possibility, puzzle.remaining_words)
            weight = (total_remaining_words - len(puzzle.remaining_words)) / total_remaining_words
            total_score += fitness_score * weight

        scored_guesses.append((total_score, word))
    scored_guesses.sort(reverse=True)
    best_guess = scored_guesses[0][1]
    return best_guess
