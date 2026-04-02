"""Benchmark get_all_answers() across solver optimization iterations."""

import sys
import time
from pathlib import Path

# Ensure the package is importable when run directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from octordle_solver.dictionary import dictionary
from octordle_solver.solver import get_all_answers

ITERATIONS = 3


def run_benchmark(label: str) -> list[float]:
    remaining_words = dictionary.valid_answers.copy()
    times = []
    for i in range(ITERATIONS):
        start = time.perf_counter()
        results = get_all_answers(remaining_words)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  [{label}] run {i + 1}/{ITERATIONS}: {elapsed:.2f}s  (top guess: {results[0].word})")
    return times


def summarize(label: str, times: list[float]) -> None:
    mean = sum(times) / len(times)
    print(f"\n{label}: mean={mean:.2f}s  min={min(times):.2f}s  max={max(times):.2f}s\n")


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "benchmark"
    print(f"Running {ITERATIONS} iterations (label: {label}) ...\n")
    times = run_benchmark(label)
    summarize(label, times)
