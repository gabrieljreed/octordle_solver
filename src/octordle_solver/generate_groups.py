"""Utils to generate groups of words."""

import concurrent.futures
import itertools
import json
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from colorama import Back, Style

from .dictionary import dictionary

CHUNK_SIZE = 10
SECOND_GUESS_PATH = Path(__file__).parent / "data" / "best_second_guesses.json"
with open(SECOND_GUESS_PATH, "r") as f:
    best_second_guesses = json.load(f)


def get_cached_best_second_guess(answer_possibility: list[int]) -> Optional[str]:
    """Get the cached best second guess for the given answer possibility.

    Args:
        answer_possibility (list[int]): Answer Possibility
    """
    possibility_key = ""
    for i in answer_possibility:
        possibility_key += str(i)

    return best_second_guesses.get(possibility_key)


class PossibilityState(Enum):
    """Enum representing the state of a letter in a Possibility."""

    INVALID = -1
    CORRECT = 0
    MISPLACED = 1
    INCORRECT = 2


class Possibility:
    """A class to represent the possibility of each letter in a word."""

    def __init__(self, p1: int, p2: int, p3: int, p4: int, p5: int):
        """Initialize the possibility.

        Args:
            p1 (int): The possibility of the first letter.
            p2 (int): The possibility of the second letter.
            p3 (int): The possibility of the third letter.
            p4 (int): The possibility of the fourth letter.
            p5 (int): The possibility of the fifth letter.
        """
        self.positions = [p1, p2, p3, p4, p5]

    def __getitem__(self, index: int) -> int:
        """Get the item."""
        return self.positions[index]


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


def evaluate_game_state(word, possibility, other_word) -> bool:
    """Evaluate the game state based on the possibility.

    Args:
        word (str): The actual word represented by possibility.
        possibility (list[int]): The possibility of each letter.
        other_word (str): The other word to compare with.
    """
    for i, letter in enumerate(other_word):
        letter = word[i]
        other_letter = other_word[i]
        if possibility[i] == PossibilityState.CORRECT.value:
            if letter != other_letter:
                return False
        elif possibility[i] == PossibilityState.MISPLACED.value:
            if letter == other_letter:
                return False
            if letter not in other_word:
                return False
        else:  # PossibilityState.INCORRECT
            if letter in other_word:
                return False

    return True


def generate_groups(given_word: str, remaining_words: list[str]) -> list[Group]:
    """Generate groups for a given word and list of words.

    Args:
        given_word (str): The given word.
        remaining_words (list[str]): The list of remaining words.
    """
    all_possibilities = list(itertools.product([0, 1, 2], repeat=5))
    groups = []
    for possibility in all_possibilities:
        group = Group(words=[], possibility=possibility)
        for remaining_word in remaining_words:
            if evaluate_game_state(given_word, possibility, remaining_word):
                group.words.append(remaining_word)

        if group:
            groups.append(group)

    groups.sort(key=lambda group: len(group.words), reverse=True)

    return groups


def generate_true_feedback(guess: str, answer: str) -> list[int]:
    """Simulate Wordle feedback for a guess vs the real answer.

    Args:
        guess (str): The guessed word.
        answer (str): The answer.

    Returns:
        (list[int]): A list of 5 integers.
    """
    feedback = [PossibilityState.INCORRECT.value] * 5
    answer_chars: list[Union[None, str]] = list(answer)

    # TODO: See if I can combine this into one pass
    # TODO: Maybe this is the best way to do it, but this should be part of the filter function
    # TODO: Chunking
    for i in range(5):
        if guess[i] == answer[i]:
            feedback[i] = PossibilityState.CORRECT.value
            answer_chars[i] = ""  # Mark as used

    for i in range(5):
        if feedback[i] == PossibilityState.INCORRECT.value and guess[i] in answer_chars:
            feedback[i] = PossibilityState.MISPLACED.value
            answer_chars[answer_chars.index(guess[i])] = ""  # Mark as used

    return feedback


def generate_groups_real_possibilities_only(given_word: str, remaining_words: list[str]):
    """Generate groups.

    Args:
        given_word (str): The word to generate groups for.
        remaining_words (list[str]): The words that are still valid answers.

    Returns:
        (list[Group]): List of groups generated.
    """
    groups = defaultdict(list)

    for word in remaining_words:
        feedback = tuple(generate_true_feedback(given_word, word))
        groups[feedback].append(word)

    return [Group(words, possibility) for possibility, words in groups.items()]


def get_best_word_groups(remaining_words: list[str], verbose=False) -> tuple[Optional[list[Group]], Optional[str]]:
    """Get the best word to guess by generating groups.

    Args:
        remaining_words (list[str]): The list of remaining words.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        tuple[list[Group], str]: The best group of words and the best word to use.
    """
    max_num_groups = 0
    best_group = None
    best_word = None
    for word in dictionary.words.copy():
        groups = generate_groups(word, remaining_words)
        if best_group is None:
            best_group = groups
            best_word = word

        elif len(groups) > max_num_groups:
            max_num_groups = len(groups)
            best_group = groups
            best_word = word
            if verbose:
                largest_group = max(len(group.words) for group in groups)
                print(f"New best word: {best_word} ({max_num_groups} groups, largest group {largest_group})")

        elif len(groups) == max_num_groups:
            if verbose:
                print(f"Tied best word: {word}")
            largest_group_best = max(len(group.words) for group in best_group)
            largest_group_current = max(len(group.words) for group in groups)
            if largest_group_current < largest_group_best:
                max_num_groups = len(groups)
                best_group = groups
                best_word = word
                if verbose:
                    print(
                        f"\tNew best word: {best_word} ({max_num_groups} groups, largest group {largest_group_current})"
                    )

    return best_group, best_word


def process_word(word, remaining_words) -> tuple[str, list[Group]]:
    """Generate groups for a given word and list of remaining words."""
    groups = generate_groups_real_possibilities_only(word, remaining_words)
    return word, groups


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
        groups = generate_groups_real_possibilities_only(word, remaining_words)
        batch_results.append((word, groups))
    return batch_results


class AnswerPossibility:
    """Class representing a possible answer."""

    def __init__(self, word: str, groups: list[Group]):
        """Initialize the AnswerPossibility."""
        self.word = word
        self.groups = groups

    def __str__(self):
        """Return a string representation of the AnswerPossibility."""
        result = (
            f"{self.word}: {len(self.groups)} groups, largest group {max(len(group.words) for group in self.groups)}"
        )
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


def get_best_word_groups_parallel(remaining_words: list[str], verbose=False):
    """Get the best word to guess by generating groups.

    Args:
        remaining_words (list[str]): The list of remaining words.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        tuple[list[Group], str]: The best group of words and the best word to use.
    """
    words = dictionary.words.copy()
    max_num_groups = 0
    best_group = None
    best_word = None

    if len(remaining_words) == 1:
        return [Group(remaining_words, [0, 0, 0, 0, 0])], remaining_words[0]

    # TODO: if there are 2 or fewer words, just return the first word

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_word, word, remaining_words): word for word in words}
        for future in concurrent.futures.as_completed(futures):
            word, groups = future.result()
            if best_group is None:
                best_group = groups
                best_word = word
                max_num_groups = len(groups)
            elif len(groups) > max_num_groups:
                max_num_groups = len(groups)
                best_group = groups
                best_word = word
                if verbose:
                    largest_group = max(len(group.words) for group in groups)
                    print(f"New best word: {best_word} ({max_num_groups} groups, largest group {largest_group})")
            elif len(groups) == max_num_groups:
                if verbose:
                    print(f"Tied best word: {word}")
                largest_group_best = max(len(group.words) for group in best_group)
                largest_group_current = max(len(group.words) for group in groups)
                if largest_group_current < largest_group_best:
                    max_num_groups = len(groups)
                    best_group = groups
                    best_word = word
                    if verbose:
                        print(
                            f"\tNew best word: {best_word} ({max_num_groups} groups, largest group {largest_group_current})"
                        )

    if len(remaining_words) > 100:
        print(f"Too many remaining words {len(remaining_words)}, returning now")
        return best_group, best_word

    # Rerun over the remaining words and favor them if there's a tie
    print("Rerunning over remaining words")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_word, word, remaining_words): word for word in remaining_words}
        for future in concurrent.futures.as_completed(futures):
            word, groups = future.result()
            if best_group is None:
                best_group = groups
                best_word = word
                max_num_groups = len(groups)
            elif len(groups) > max_num_groups:
                max_num_groups = len(groups)
                best_group = groups
                best_word = word
                if verbose:
                    largest_group = max(len(group.words) for group in groups)
                    print(f"New best word: {best_word} ({max_num_groups} groups, largest group {largest_group})")
            elif len(groups) == max_num_groups:
                if verbose:
                    print(f"Tied best word: {word}")
                largest_group_best = max(len(group.words) for group in best_group)
                largest_group_current = max(len(group.words) for group in groups)
                if largest_group_current <= largest_group_best:
                    max_num_groups = len(groups)
                    best_group = groups
                    best_word = word
                    if verbose:
                        print(
                            f"\tNew best word: {best_word} ({max_num_groups} groups, largest group {largest_group_current})"
                        )

    return best_group, best_word


def get_all_answer_possibilities(remaining_words: list[str], valid_guesses: Optional[list[str]] = None):
    """Like get_best_word_groups_parallel, but returns all possibilities."""
    if not valid_guesses:
        valid_guesses = dictionary.valid_guesses

    all_possibilities: list[AnswerPossibility] = []

    if len(remaining_words) == 1:
        word, groups = process_word(remaining_words[0], remaining_words)
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
