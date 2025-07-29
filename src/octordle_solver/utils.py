"""Utility functions."""

import os
from contextlib import contextmanager
from time import perf_counter


def clear_screen():  # pragma: no cover
    """Clear the screen."""
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def sanitize_words(words: list[str]) -> list[str]:
    """Capitalize and sort words.

    Args:
        list[str]: The words to sanitize.

    Returns:
        list[str]: The sanitized words
    """
    sanitized_words = []

    for word in words:
        sanitized_words.append(word.upper())
    sanitized_words.sort()

    return sanitized_words


class catchtime:
    """Context manager for simple timing."""

    def __init__(self, title: str = "Time"):
        """Initialize the context manager.

        Args:
            title (str): Title to use for the printout.
        """
        self.title = title

    def __enter__(self):
        """Enter the context manager."""
        self.start = perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        """Exit the context manager."""
        self.time = perf_counter() - self.start
        self.readout = f"{self.title}: {self.time:3f} seconds"
        print(self.readout)
