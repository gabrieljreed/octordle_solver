"""Backend selection and factory for creating Puzzle instances.

This module centralizes the logic for choosing between Rust and Python
implementations of the Puzzle class. It provides a factory function that
creates Puzzle instances with the appropriate backend, preferring Rust
for performance while maintaining fallback to Python.
"""

from typing import Any, Optional

from .dictionary import dictionary
from .solver import Puzzle as PythonPuzzle

# Module-level references to both backends
_rust_puzzle_cls: Optional[Any] = None
_python_puzzle_cls: Optional[Any] = PythonPuzzle

# Try to import Rust bindings
try:
    import octordle_solver_rs as rs

    _rust_puzzle_cls = rs.Puzzle
    _use_rust = True
except ImportError:
    _use_rust = False


def make_puzzle() -> Any:
    """Create a backend-appropriate Puzzle instance.

    Returns a Rust Puzzle for performance if available, otherwise
    returns a Python Puzzle. Both implement the same interface.

    Returns:
        A Puzzle instance (either Rust or Python backend).
    """
    if _use_rust:
        assert _rust_puzzle_cls is not None
        return _rust_puzzle_cls(
            dictionary.valid_answers,
            dictionary.valid_guesses,
            get_best_answer=True,
        )
    assert _python_puzzle_cls is not None
    return _python_puzzle_cls(get_best_answer=True)
