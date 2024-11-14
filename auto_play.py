from utils import clear_screen
from wordle_solver.game import Game
from wordle_solver.generate_groups import get_best_word_groups, get_best_word_groups_parallel
from wordle_solver.constants import STARTING_GUESS
from wordle_solver.solver import filter_words
from time import time
import sys


if __name__ == "__main__":
    game = Game("PRIMP", clear_screen=False)
    print(game)
    print(f"Starting game with word: {game.word}")
    game.guess(STARTING_GUESS)
    game.num_tries -= 1
    game.remaining_words = filter_words(
        game.remaining_words, game.correct_letters, game.misplaced_letters, game.incorrect_letters
    )
    print(game)
    # FIXME: This filters down way too many words...?
    print(len(game.remaining_words))
    # sys.exit()
    while game.num_tries > 0:
        game.num_tries -= 1
        start_time = time()
        best_group, best_word = get_best_word_groups_parallel(game.remaining_words)
        game.guess(best_word)
        game.remaining_words = filter_words(
            game.remaining_words, game.correct_letters, game.misplaced_letters, game.incorrect_letters
        )
