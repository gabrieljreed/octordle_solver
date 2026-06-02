# Octordle and Wordle Solver

## UI

```bash
pip install -e .
wordle-solver-ui
octordle-solver-ui
```

## Running tests

```bash
pip install -r requirements/dev.txt
pytest
```

## Writeups

Check out the writeups I made for the [Wordle solver](https://www.gabrieljreed.com/projects/wordle-solver/) and [Octordle solver](https://www.gabrieljreed.com/projects/octordle-solver/) on my dev blog!

## Rust

The project has a Rust backend for performance, with Python bindings for compatibility. To build the Rust extension, you can use `maturin`:

```bash
pip install maturin
cd crates/octordle_solver_rs
python -m maturin develop --release
```

If you do not build the Rust extension, the Python solver will be used as a fallback. The UI and compute scripts will automatically prefer the Rust backend when available.
