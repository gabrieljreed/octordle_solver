from enum import Enum

from solver import STARTING_GUESS


class TileState(Enum):
    UNSET = 0
    CORRECT = 0
    INCORRECT = 2


STARTING_GUESS = "CRANE"
