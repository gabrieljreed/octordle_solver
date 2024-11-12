import itertools
import sys
from typing import Optional

from colorama import Back, Fore, Style

from .dictionary import Dictionary


class GameState:
    def __init__(self):
        self.correct_letters = ["", "", "", "", ""]
        self.misplaced_letters = []
        self.incorrect_letters = []


class Group:
    def __init__(self, words, possibility):
        self.words = words
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
        if possibility[i] == 0:  # Correct letter
            if letter != other_letter:
                return False
        elif possibility[i] == 1:  # Misplaced letter
            if letter == other_letter:
                return False
            if letter not in other_word:
                return False
        elif possibility[i] == 2:  # Incorrect letter
            if letter in other_word:
                return False

    return True


def generate_groups(given_word: str, remaining_words: list[str]) -> list[Group]:
    """Generate groups for a given word and list of words."""
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


if __name__ == "__main__":
    # word = "field"  # The word we're generating groups for
    remaining_words = [
        "BEARD",
        "BEARS",
        "DEARS",
        "DEARY",
        "FEARS",
        "GEARS",
        "HEARD",
        "HEARS",
        "HEART",
        "LEARY",
        "PEARL",
        "PEARS",
        "PEART",
        "READS",
        "READY",
        "REALM",
        "REALS",
        "REAMS",
        "REAPS",
        "TEARS",
        "TEARY",
        "WEARS",
        "WEARY",
        "YEARS",
    ]

    best_group, best_word = get_best_word_groups(remaining_words, verbose=True)

    if not best_group or not best_word:
        print("No best solution found")
        sys.exit()

    print_group_info(best_group, best_word)
