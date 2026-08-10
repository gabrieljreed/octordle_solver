# octordle_solver — Agent Instructions

Python package for solving Wordle and Octordle puzzles, with a Qt GUI and an optional high-performance Rust backend.

## Build & Test

```powershell
# Install in editable mode
pip install -e .

# Install dev dependencies
pip install -r requirements/dev.txt

# Run tests (verbose + coverage)
pytest

# Build optional Rust backend (requires maturin)
python -m maturin develop --release
```

Entry points: `wordle-solver-ui`, `octordle-solver-ui`, `compute-best-second-guess`

## Architecture

```
src/octordle_solver/
  constants.py    # STARTING_GUESS = "SLATE"
  dictionary.py   # Module-level singleton: loads 3 word lists from data/ at import time
  utils.py        # clear_screen(), sanitize_words(), catchtime context manager
  solver.py       # Core solving engine: Puzzle, AnswerPossibility, Group, Guess classes
  game.py         # Playable terminal Wordle game
  backend.py      # Factory: tries Rust backend (octordle_solver_rs), falls back to Python Puzzle
  ui/             # PySide6 Qt GUI (wordle_solver_ui.py, octordle_solver_ui.py, threads.py)

crates/octordle_solver_rs/   # PyO3/Rust port of solver.py — same API, faster
  src/lib.rs      # Exports: score_guess, generate_groups, Puzzle, Group, etc.
  src/solver.rs
```

## Key Conventions

**Singleton dictionary** — `from .dictionary import dictionary` gives access to `.words`, `.valid_guesses`, `.valid_answers`. It loads once at import time; do not re-instantiate.

**Backend factory** — Always use `backend.make_puzzle()` rather than importing `Puzzle` directly. This selects Rust or Python transparently. Both backends accept identical constructor arguments.

**Feedback encoding** — Three formats used interchangeably internally; `Puzzle._sanitize_result()` converts between them:
- String: `"YMNNN"` (Y=correct, M=misplaced, N=not present)
- List of ints: `[2, 1, 0, 0, 0]`
- `PossibilityState` enum

**Caching** — `score_guess_cached()` and `generate_groups_cached()` use `@lru_cache`. Do not break call signatures — cache keys are the arguments.

**Sorting heuristic** — `AnswerPossibility` sorts by most groups first, then smallest max group size (entropy-based). `__gt__()` implements this.

**UI threading** — Solver runs on background `QThread`. Signals/slots in `threads.py` are the bridge; never call solver methods directly from the main thread.

## Code Style

- Linter: **ruff** (see [ruff.toml](ruff.toml)) — line length 119, double quotes, LF line endings
- Import order: black-compatible isort profile
- Tests use `@pytest.mark.parametrize` and class-based grouping (`TestGroup`, `TestGuess`)

## Data Files

All in `src/octordle_solver/data/`:
- `5_letter_words_spellchecked.txt` — primary word list
- `valid_answers.txt`, `valid_guesses.txt` — Wordle-specific subsets
- `best_second_guesses.json` — precomputed; regenerate with `compute-best-second-guess`

## Testing

```powershell
pytest                  # all tests with coverage
pytest tests/test_solver.py   # single module
```

`test_rust_solver.py` is skipped automatically when the Rust backend is not installed. Tests that require `octordle_solver_rs` should guard with `pytest.importorskip("octordle_solver_rs")`.
