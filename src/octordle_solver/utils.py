"""Utility functions."""

import os


def clear_screen():
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
