import itertools
from typing import Optional
import numpy as np
import concurrent.futures

from colorama import Back, Style

from .dictionary import Dictionary


class GameState:
    def __init__(self):
        self.correct_letters = ["", "", "", "", ""]
        self.misplaced_letters = []
        self.incorrect_letters = []


class Possibility:
    """A class to represent the possibility of each letter in a word."""

    CORRECT = 0
    MISPLACED = 1
    INCORRECT = 2

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
        return self.positions[index]


class Group:
    def __init__(self, words: list[str], possibility):
        self.words: list[str] = words
        self.possibility = possibility

    def __str__(self):
        result = str(self.possibility)
        for word in self.words:
            result += f"\n\t{word}"
        return result

    def __repr__(self) -> str:
        return self.__str__()

    def __bool__(self):
        return bool(self.words)


def pretty_print_group(group: Group, word: str):
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
        if possibility[i] == Possibility.CORRECT:
            if letter != other_letter:
                return False
        elif possibility[i] == Possibility.MISPLACED:
            if letter == other_letter:
                return False
            if letter not in other_word:
                return False
        elif possibility[i] == Possibility.INCORRECT:
            if letter in other_word:
                return False

    return True


def _generate_all_possibilities() -> list[Possibility]:
    """Generate all possibilities.

    Returns:
        list[Possibility]: The list of all possibilities.
    """
    possibilities = []
    for possibility in itertools.product([0, 1, 2], repeat=5):
        possibilities.append(Possibility(*possibility))

    return possibilities


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


def generate_groups_np(given_word: str, remaining_words: list[str]) -> list[Group]:
    all_possibilities = np.array(list(itertools.product([0, 1, 2], repeat=5)))
    remaining_words = np.array(remaining_words)
    groups = []

    for possibility in all_possibilities:
        mask = np.array([evaluate_game_state(given_word, possibility, word) for word in remaining_words])
        group_words = remaining_words[mask]
        if len(group_words) > 0:
            groups.append(Group(group_words, possibility))

    groups.sort(key=lambda group: len(group.words), reverse=True)

    return groups


def get_best_word_groups(remaining_words: list[str], verbose=False) -> tuple[Optional[list[Group]], Optional[str]]:
    """Get the best word to guess by generating groups.

    Args:
        remaining_words (list[str]): The list of remaining words.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        tuple[list[Group], str]: The best group of words and the best word to use.
    """
    dictionary = Dictionary()
    max_num_groups = 0
    best_group = None
    best_word = None
    for word in dictionary.words:
        groups = generate_groups(word, remaining_words)
        # groups = generate_groups_np(word, remaining_words)
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


def process_word(word, remaining_words):
    groups = generate_groups(word, remaining_words)
    return word, groups


class AnswerPossibility:
    def __init__(self, word: str, groups: list[Group]):
        self.word = word
        self.groups = groups

    def __str__(self):
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
            return max(len(group.words) for group in self.groups) > max(len(group.words) for group in other.groups)

        return len(self.groups) > len(other.groups)


def get_best_word_groups_parallel(remaining_words: list[str], verbose=False):
    """Get the best word to guess by generating groups.

    Args:
        remaining_words (list[str]): The list of remaining words.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        tuple[list[Group], str]: The best group of words and the best word to use.
    """
    dictionary = Dictionary()
    max_num_groups = 0
    best_group = None
    best_word = None

    if len(remaining_words) == 1:
        return [Group(remaining_words, Possibility(0, 0, 0, 0, 0))], remaining_words[0]

    # TODO: if there are 2 or fewer words, just return the first word

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_word, word, remaining_words): word for word in dictionary.words}
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


def get_all_answer_possibilities(remaining_words: list[str], verbose=False):
    """Like get_best_word_groups_parallel, but returns all possibilities."""
    all_possibilities: list[AnswerPossibility] = []

    if len(remaining_words) == 1:
        word, groups = process_word(remaining_words[0], remaining_words)
        all_possibilities = [AnswerPossibility(word, groups)]

    dictionary = Dictionary()
    words = remaining_words + dictionary.words

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_word, word, remaining_words): word for word in words}
        for future in concurrent.futures.as_completed(futures):
            word, groups = future.result()
            all_possibilities.append(AnswerPossibility(word, groups))

    all_possibilities.sort(reverse=True)

    return all_possibilities
