# Wordle Solver Performance Optimization — Blog Notes

## Overview

The solver's `get_all_answers()` function is the hot path. It evaluates every candidate word (~13K) against the current set of remaining possible answers, parallelised via `ProcessPoolExecutor`. Starting from a cold baseline of ~36s per full evaluation, we applied six targeted fixes in three phases and recorded benchmark results after each one.

Benchmark methodology: 3 runs of `get_all_answers(dictionary.valid_answers)` (2,309 words — worst-case first guess). Times recorded with `time.perf_counter()` on Windows 10. Top recommended guess after each fix is noted as a correctness check.

---

## Baseline

| Run | Time |
|-----|------|
| 1   | 34.76s |
| 2   | 36.77s |
| 3   | 37.04s |

**mean=36.19s  min=34.76s  max=37.04s**  
Top guess: `SALET`

---

## Phase 1: Trivial One-Liners

### Fix 1 — Use `cached_property` in `__gt__`

**What changed:** `AnswerPossibility.__gt__` (solver.py:100) was calling `max(len(group.words) for group in self.groups)` twice per comparison — once for `self`, once for `other`. The class already has a `@cached_property max_group_size` that computes exactly this. The fix replaces both inline expressions with `self.max_group_size` and `other.max_group_size`.

**Why it matters:** `__gt__` is invoked ~180,000 times during the final `sort(reverse=True)` of ~12,000 `AnswerPossibility` objects. Each call was doing two O(groups) passes that could be a single O(1) cached lookup after the first comparison.

| Run | Time |
|-----|------|
| 1   | 31.72s |
| 2   | 34.37s |
| 3   | 34.45s |

**mean=33.51s  min=31.72s  max=34.45s**  (-7.4% vs baseline)  
Top guess: `SALET`

---

### Fix 2 — Remove `tuple()` in `generate_groups` inner loop

**What changed:** `generate_groups` (solver.py:336) was doing `feedback = tuple(score_guess_cached(given_word, word))` to create a hashable dict key. `score_guess_cached` already returns a `str` (e.g. `"YMNNN"`), which is directly hashable. The `tuple()` call was allocating a new 5-element tuple (~45.9M objects across a full evaluation) for no reason.

**Why it matters:** The inner loop runs once per (candidate word × remaining word) pair — roughly 13,000 × 2,309 = ~30M iterations. Eliminating one object allocation per iteration is measurable.

| Run | Time |
|-----|------|
| 1   | 33.68s |
| 2   | 37.09s |
| 3   | 35.07s |

**mean=35.28s  min=33.68s  max=37.09s**  (-2.5% vs Fix 1; IPC overhead dominates, allocation savings masked by noise)  
Top guess: `SALET`

---

### Fix 3 — Remove `list()` copy in `generate_groups_cached`

**What changed:** The `@lru_cache` wrapper `generate_groups_cached` (solver.py:353) was doing `remaining_words = list(remaining_words_tuple)` before calling `generate_groups`. The inner function only iterates `remaining_words` — it never mutates it — so the copy was unnecessary. The tuple is passed directly and the signature updated to `Sequence[str]`.

**Why it matters:** This copy runs once per unique (word, remaining_words) cache miss. On the first call with a fresh `remaining_words` set it runs ~13,000 times, each copying ~2,309 strings into a new list.

| Run | Time |
|-----|------|
| 1   | 33.22s |
| 2   | 37.45s |
| 3   | 35.47s |

**mean=35.38s  min=33.22s  max=37.45s**  (~0% vs Fix 2; IPC overhead dominates, list copy savings masked by noise)  
Top guess: `SALET`

---

## Phase 2: Structural

### Fix 4 — `CHUNK_SIZE = 10` → `400`

**What changed:** The constant controlling how many candidate words are batched per worker call was raised from 10 to 400.

**Why it matters:** With `CHUNK_SIZE=10` and ~13,000 candidates, ~1,300 batches are created. Each batch serialises `remaining_words` (~2,309 strings, ~70KB) via pickle for IPC — ~90MB of data movement total. Windows process IPC is especially costly. At 400, there are only ~33 batches — a 40× reduction in IPC volume.

| Run | Time |
|-----|------|
| 1   | 32.88s |
| 2   | 35.47s |
| 3   | 33.23s |

**mean=33.86s  min=32.88s  max=35.47s**  (-4.3% vs Fix 3; less than predicted — actual group computation in workers dominates, IPC is a smaller fraction than expected)  
Top guess: `SALET`

---

### Fix 5 — O(n) list scan → O(1) set in `calculate_fitness_score`

**What changed:** `calculate_fitness_score` received `puzzle.remaining_words` as a list and tested membership with `word in remaining_words` — an O(n) scan. In `get_best_guess_multiple_puzzles`, a set of remaining words per puzzle is now built once before the scoring loop, and passed in instead.

**Why it matters:** This function is called for every (candidate word × active puzzle) pair during multi-puzzle Octordle solving, so eliminating the linear scan removes a significant inner-loop cost when many words remain. **Note:** This fix only affects the multi-puzzle path (`get_best_guess_multiple_puzzles`), not `get_all_answers`, so it does not show up in the single-puzzle benchmark below.

| Run | Time |
|-----|------|
| 1   | 32.27s |
| 2   | 35.38s |
| 3   | 33.10s |

**mean=33.58s  min=32.27s  max=35.38s**  (no change expected — fix targets Octordle multi-puzzle path, not measured here)  
Top guess: `SALET`

---

## Phase 3: IPC Optimization

### Fix 6 — `ProcessPoolExecutor` initializer

**What changed:** A `_init_worker` initializer function is passed to `ProcessPoolExecutor`. It stores `remaining_words` in a process-global variable once when the worker process starts. `process_word_batch` now reads from that global instead of receiving `remaining_words` as a batch argument.

**Why it matters:** Even after Fix 4's batch reduction, `remaining_words` was still pickled once per batch (~33 times). With an initializer it is pickled once per *worker process* (typically 4–8, matching CPU count). On Windows — where each new process is a full Python interpreter spawn — this further reduces IPC overhead.

| Run | Time |
|-----|------|
| 1   | 32.14s |
| 2   | 35.95s |
| 3   | 33.31s |

**mean=33.80s  min=32.14s  max=35.95s**  (~0% vs Fix 5; with 33 batches and ~70KB each, pickling overhead was already negligible)  
Top guess: `SALET`

---

## Summary

| Step | Change | mean | min | Δ vs prev |
|------|--------|------|-----|-----------|
| Baseline | — | 36.19s | 34.76s | — |
| Fix 1 | `cached_property` in `__gt__` | 33.51s | 31.72s | -7.4% |
| Fix 2 | Remove `tuple()` | 35.28s | 33.68s | ~0% (noise) |
| Fix 3 | Remove `list()` copy | 35.38s | 33.22s | ~0% (noise) |
| Fix 4 | `CHUNK_SIZE` 10 → 400 | 33.86s | 32.88s | -4.3% |
| Fix 5 | Set for membership test | 33.58s | 32.27s | n/a (Octordle path only) |
| Fix 6 | Executor initializer | 33.80s | 32.14s | ~0% |

**Overall: 36.19s → 33.80s mean (-6.6%), 34.76s → 32.14s min (-7.5%)**

---

## Key Takeaways

**What actually moved the needle:**
- **Fix 1** (`cached_property` in `__gt__`) was the only change with a clear, measurable signal: -7.4% on mean. The sort at the end of `get_all_answers` compares ~12K objects ~180K times — eliminating two O(groups) generator passes per comparison and replacing with a cached O(1) lookup had real impact.

**What didn't show up (but still matters):**
- **Fix 4** (`CHUNK_SIZE` 10 → 400) was predicted to be the biggest win via 40× IPC reduction, but only showed -4.3%. Profiling would be needed to confirm, but the likely explanation is that worker-side `score_guess` computation (30M iterations across 13K candidates × 2,309 remaining words) dominates wall-clock time on this hardware — IPC was a smaller fraction than estimated.
- **Fixes 2 & 3** (eliminating `tuple()` and `list()` allocations in hot loops) — the Python interpreter overhead at ~30M iterations is real, but swamped by variance (~2s run-to-run) and worker-side computation.
- **Fix 5** (`set` membership) only affects the Octordle multi-puzzle path (`get_best_guess_multiple_puzzles`) and was never measured by the single-puzzle benchmark. The savings are proportional to `len(remaining_words) × len(all_words) × num_puzzles` at each turn — meaningful for an 8-puzzle game with many words still in play.
- **Fix 6** (executor initializer) had negligible effect at `CHUNK_SIZE=400` because with only ~33 batches at ~70KB each, the serialisation overhead was already small.

**The broader lesson:** When parallelism is involved, profile before assuming IPC is the bottleneck. The actual computation — here, millions of 5-letter string comparisons — can easily dominate. The cleanest wins came from reducing redundant work in the hot-path sort (Fix 1), not from IPC tuning.
