import itertools
from pprint import pprint


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


def evaluate_game_state(word, possibility, other_word):
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


if __name__ == "__main__":
    all_possibilities = list(itertools.product([0, 1, 2], repeat=5))
    word = "lease"  # The word we're generating groups for
    remaining_words = [
        "shade",
        "shake",
        "shame",
        "shape",
        "shave",
        "skate",
        "spate",
        "stage",
        "stake",
        "state",
        "stave",
        "usage",
        "suave",
        "spade",
        "awake",
        "image",
        "adage",
        "quake",
        "abate",
        "amaze",
        "agape",
        "agave",
        "agate",
        "phage",
        "ovate",
        "blade",
        "blame",
        "blaze",
        "flame",
        "plate",
        "whale",
        "glaze",
        "flake",
        "glade",
        "slate",
        "stale",
        "shale",
        "slake",
        "swale",
        "weave",
        "heave",
        "phase",
        "abase",
        "tease",
        "lease",
        "leave",
        "evade",
        "blase",
        "elate",
    ]

    groups = []
    for possibility in all_possibilities:
        group = Group(words=[], possibility=possibility)
        for remaining_word in remaining_words:
            if evaluate_game_state(word, possibility, remaining_word):
                group.words.append(remaining_word)

        if group:
            groups.append(group)

    # Sort groups by length
    groups.sort(key=lambda group: len(group.words), reverse=True)
    pprint(groups)

    print(f"Num groups: {len(groups)}")
    print(f"Largest group: {max(len(group.words) for group in groups)}")
