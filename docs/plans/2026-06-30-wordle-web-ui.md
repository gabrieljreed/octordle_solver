# Wordle Solver Web UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static web page version of the Wordle solver that mirrors the Qt desktop UI — 6×5 tile grid, ranked best-guesses list, group breakdown panel, remaining words panel, dark mode, and copy-to-clipboard.

**Architecture:** TypeScript + Vite (no framework). The solver logic is a direct port of `src/octordle_solver/solver.py` pure functions. Heavy computation (`getAllAnswers`) runs in a Web Worker to keep the UI responsive. Word-list data files are served as static assets and fetched at startup.

**Tech Stack:** TypeScript, Vite, Vitest (tests), vanilla CSS with custom properties for dark mode.

---

## Reference: Porting Notes

Before touching code, internalize these behavioral details from the Python source:

**`scoreGuess(guess, answer) → string`** (`solver.py:282`)
Returns a 5-char string of `"Y"` (correct), `"M"` (misplaced), `"N"` (absent).
Two-pass algorithm: first mark all exact matches; then use a frequency counter on unmatched answer letters to mark misplaced letters (avoids double-counting duplicate letters).

**`generateGroups(word, remainingWords) → Group[]`** (`solver.py:320`)
Scores `word` against every entry in `remainingWords`; buckets them by their score string. Returns one `Group` per unique score.

**`getAllAnswers(remainingWords, validGuesses) → AnswerPossibility[]`** (`solver.py:388`)
1. Build candidate list: `[...new Set([...remainingWords, ...validGuesses])]` (remaining words first, deduped).
2. Call `generateGroups` for each candidate.
3. Sort descending: primary = more groups wins; tie = smaller `maxGroupSize` wins.
Single-word edge case: return that word immediately without scanning all guesses.

**`filterWords(remainingWords, guess, result) → string[]`** (`solver.py:231`)
Keep only words where `scoreGuess(guess, word) === result`.

**Second-guess cache** (`solver.py:305`)
`best_second_guesses.json` keys are 5-char strings like `"22000"` where `2=N`, `1=M`, `0=Y` (maps from `PossibilityState` int values). Apply only when the current row is 1 and the first guess was exactly `"SLATE"`.

**Tile color cycle** (`helpers.py:47`)
Once a letter is committed (Enter pressed), clicking a tile cycles: GRAY → YELLOW → GREEN → GRAY.
Colors: GREEN `#69ab64`, YELLOW `#c3ae55`, GRAY `#767a7d`.

**Fitness sort** (`solver.py:95–101` `__gt__`)
```
if groupsA.length === groupsB.length:
    return maxGroupSizeA < maxGroupSizeB   // smaller max wins
return groupsA.length > groupsB.length     // more groups wins
```

---

## File Structure

```
web/                              ← all web-app code lives here
  package.json
  tsconfig.json
  vite.config.ts                  ← base path + outDir → ../docs
  index.html
  style.css                       ← layout, tiles, dark mode CSS vars
  src/
    types.ts                      ← TileState, Group, AnswerPossibility, WorkerMessage
    solver.ts                     ← scoreGuess, generateGroups, getAllAnswers, filterWords
    data.ts                       ← loadData(): fetches word lists + best_second_guesses.json
    worker.ts                     ← Web Worker: receives state, runs getAllAnswers, posts back
    grid.ts                       ← Grid class: 6×5 DOM tiles, keyboard input, color cycling
    panels.ts                     ← BestGuessList, GroupsPanel, RemainingWordsPanel
    app.ts                        ← App: state, wires grid + panels + worker + dark mode
  public/
    data/
      valid_answers.txt           ← copy of src/octordle_solver/data/valid_answers.txt
      valid_guesses.txt           ← copy of src/octordle_solver/data/valid_guesses.txt
      best_second_guesses.json    ← copy of src/octordle_solver/data/best_second_guesses.json
  tests/
    solver.test.ts                ← unit tests for all pure solver functions
```

**GitHub Pages output:** Vite builds to `../docs/` (repo-root `docs/`). Enable GH Pages on `main` branch, source = `docs/` folder.

---

## Task 1 — Scaffold the Project

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/vite.config.ts`
- Create: `web/index.html`

- [ ] In a terminal, from repo root:
  ```powershell
  mkdir web; cd web
  npm init -y
  npm install --save-dev vite typescript vitest @vitest/coverage-v8
  ```

- [ ] Create `web/tsconfig.json`:
  ```json
  {
    "compilerOptions": {
      "target": "ES2020",
      "module": "ESNext",
      "moduleResolution": "bundler",
      "strict": true,
      "lib": ["ES2020", "DOM", "DOM.Iterable"],
      "outDir": "./dist",
      "noEmit": true
    },
    "include": ["src", "tests"]
  }
  ```

- [ ] Create `web/vite.config.ts`:
  ```ts
  import { defineConfig } from "vite";

  export default defineConfig({
    // Replace 'octordle_solver' with your actual GitHub repo name
    base: "/octordle_solver/",
    build: {
      outDir: "../docs",
      emptyOutDir: true,
    },
    worker: {
      format: "es",
    },
    test: {
      environment: "node",
    },
  });
  ```

- [ ] Create minimal `web/index.html`:
  ```html
  <!doctype html>
  <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Wordle Solver</title>
      <link rel="stylesheet" href="/style.css" />
    </head>
    <body>
      <div id="app"></div>
      <script type="module" src="/src/app.ts"></script>
    </body>
  </html>
  ```

- [ ] Add scripts to `web/package.json`:
  ```json
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  }
  ```

- [ ] Run `npm run dev` and confirm a blank page loads at `http://localhost:5173/octordle_solver/`. Stop the dev server.

- [ ] Commit: `git add web/ && git commit -m "feat(web): scaffold Vite+TS project"`

---

## Task 2 — Copy Data Files

**Files:**
- Create: `web/public/data/valid_answers.txt`
- Create: `web/public/data/valid_guesses.txt`
- Create: `web/public/data/best_second_guesses.json`

- [ ] From repo root:
  ```powershell
  New-Item -ItemType Directory -Force web/public/data
  Copy-Item src/octordle_solver/data/valid_answers.txt     web/public/data/
  Copy-Item src/octordle_solver/data/valid_guesses.txt     web/public/data/
  Copy-Item src/octordle_solver/data/best_second_guesses.json web/public/data/
  ```

- [ ] Verify counts in browser: after `npm run dev`, open DevTools Network tab and confirm the files load (don't 404). Check sizes: `valid_answers.txt` ~33KB, `valid_guesses.txt` ~130KB, `best_second_guesses.json` ~16KB.

- [ ] Commit: `git add web/public && git commit -m "feat(web): add word-list data files"`

---

## Task 3 — Types

**Files:**
- Create: `web/src/types.ts`

- [ ] Create `web/src/types.ts`:
  ```ts
  /** Feedback state for a single tile. */
  export enum TileState {
    Empty = "empty",       // no letter yet
    Pending = "pending",   // letter typed, Enter not pressed
    Absent = "absent",     // gray  (N)
    Misplaced = "misplaced", // yellow (M)
    Correct = "correct",   // green  (Y)
  }

  /** Maps a TileState to the score character used by scoreGuess. */
  export const TILE_STATE_TO_SCORE: Record<string, string> = {
    [TileState.Correct]: "Y",
    [TileState.Misplaced]: "M",
    [TileState.Absent]: "N",
  };

  export interface Group {
    possibility: string; // 5-char score string e.g. "YMNNN"
    words: string[];
  }

  export interface AnswerPossibility {
    word: string;
    groups: Group[];
    maxGroupSize: number;
  }

  export interface Guess {
    word: string;   // uppercase 5-letter word
    result: string; // 5-char score string
  }

  // Messages to/from the Web Worker
  export interface WorkerRequest {
    remainingWords: string[];
    validGuesses: string[];
  }

  export interface WorkerResponse {
    possibilities: AnswerPossibility[];
    remainingWords: string[];  // echoed back (unchanged)
  }

  export interface AppData {
    validAnswers: string[];
    validGuesses: string[];
    bestSecondGuesses: Record<string, string>;
  }
  ```

- [ ] Commit: `git add web/src/types.ts && git commit -m "feat(web): add shared types"`

---

## Task 4 — Solver Logic + Tests

**Files:**
- Create: `web/src/solver.ts`
- Create: `web/tests/solver.test.ts`

- [ ] Write the failing tests first (`web/tests/solver.test.ts`):
  ```ts
  import { describe, it, expect } from "vitest";
  import { scoreGuess, generateGroups, getAllAnswers, filterWords } from "../src/solver";

  describe("scoreGuess", () => {
    it("all correct", () => {
      expect(scoreGuess("CRANE", "CRANE")).toBe("YYYYY");
    });
    it("all absent", () => {
      expect(scoreGuess("ZZZZZ", "CRANE")).toBe("NNNNN");
    });
    it("mixed correct/misplaced/absent", () => {
      // s=Y(0vs0), l=M(in remaining [t,l]), a=Y(2vs2), t=M(in remaining [t]), e=Y(4vs4)
      expect(scoreGuess("SLATE", "STALE")).toBe("YMYMY");
    });
    it("handles duplicate letters — only marks as many as exist in answer", () => {
      // guess "SPEED", answer "CREEP": no s, p=M(one p in answer), e=M(one e at pos3 remaining), e=Y(pos3 correct), d=N
      expect(scoreGuess("SPEED", "CREEP")).toBe("NMMYN");
    });
    it("misplaced then correct duplicate", () => {
      expect(scoreGuess("LLAMA", "HELLO")).toBe("NNMNN");
    });
  });

  describe("generateGroups", () => {
    it("returns one group when all words score the same", () => {
      const groups = generateGroups("CRANE", ["CRANE"]);
      expect(groups).toHaveLength(1);
      expect(groups[0].possibility).toBe("YYYYY");
      expect(groups[0].words).toEqual(["CRANE"]);
    });
    it("buckets words by their score string", () => {
      const groups = generateGroups("CRANE", ["CRANE", "AUDIO"]);
      expect(groups).toHaveLength(2);
    });
  });

  describe("getAllAnswers", () => {
    const words = ["CRANE", "AUDIO", "STALE", "SUITE"];
    it("returns one entry per candidate word", () => {
      const results = getAllAnswers(words, []);
      expect(results).toHaveLength(4);
    });
    it("sorts: more groups first", () => {
      const results = getAllAnswers(words, []);
      for (let i = 1; i < results.length; i++) {
        const prev = results[i - 1];
        const curr = results[i];
        const prevBetter =
          prev.groups.length > curr.groups.length ||
          (prev.groups.length === curr.groups.length &&
            prev.maxGroupSize <= curr.maxGroupSize);
        expect(prevBetter).toBe(true);
      }
    });
    it("single remaining word returns immediately", () => {
      const results = getAllAnswers(["CRANE"], []);
      expect(results).toHaveLength(1);
      expect(results[0].word).toBe("CRANE");
    });
  });

  describe("filterWords", () => {
    it("keeps only words consistent with the guess/result", () => {
      const remaining = ["CRANE", "STALE", "AUDIO"];
      const filtered = filterWords(remaining, "CRANE", "YYYYY");
      expect(filtered).toEqual(["CRANE"]);
    });
    it("all filtered out when no words match", () => {
      const filtered = filterWords(["AUDIO"], "CRANE", "YYYYY");
      expect(filtered).toEqual([]);
    });
  });
  ```

- [ ] Run `npm test` from `web/` — confirm all tests **fail** (solver.ts doesn't exist yet).

- [ ] Create `web/src/solver.ts`:
  ```ts
  import type { AnswerPossibility, Group } from "./types";

  /** Simulate Wordle feedback for a guess vs. the real answer.
   *  Returns a 5-char string: Y=correct, M=misplaced, N=absent. */
  export function scoreGuess(guess: string, answer: string): string {
    const feedback: string[] = ["N", "N", "N", "N", "N"];
    const remainingCounts: Record<string, number> = {};

    // First pass: mark correct letters
    for (let i = 0; i < 5; i++) {
      if (guess[i] === answer[i]) {
        feedback[i] = "Y";
      } else {
        remainingCounts[answer[i]] = (remainingCounts[answer[i]] ?? 0) + 1;
      }
    }

    // Second pass: mark misplaced letters
    for (let i = 0; i < 5; i++) {
      if (feedback[i] === "Y") continue;
      const letter = guess[i];
      if ((remainingCounts[letter] ?? 0) > 0) {
        feedback[i] = "M";
        remainingCounts[letter]--;
      }
    }

    return feedback.join("");
  }

  const scoreCache = new Map<string, string>();

  function scoreGuessCached(guess: string, answer: string): string {
    const key = `${guess}|${answer}`;
    let result = scoreCache.get(key);
    if (result === undefined) {
      result = scoreGuess(guess, answer);
      scoreCache.set(key, result);
    }
    return result;
  }

  /** Group `remainingWords` by how they score against `word`. */
  export function generateGroups(word: string, remainingWords: string[]): Group[] {
    const buckets = new Map<string, string[]>();
    for (const answer of remainingWords) {
      const score = scoreGuessCached(word, answer);
      const bucket = buckets.get(score);
      if (bucket) {
        bucket.push(answer);
      } else {
        buckets.set(score, [answer]);
      }
    }
    return Array.from(buckets.entries()).map(([possibility, words]) => ({ possibility, words }));
  }

  function makeAnswerPossibility(word: string, groups: Group[]): AnswerPossibility {
    const maxGroupSize = groups.length === 0 ? -1 : Math.max(...groups.map((g) => g.words.length));
    return { word, groups, maxGroupSize };
  }

  /** Compare two AnswerPossibility objects: more groups wins; tie → smaller maxGroupSize wins. */
  function isFirstBetter(a: AnswerPossibility, b: AnswerPossibility): boolean {
    if (a.groups.length === b.groups.length) {
      if (a.groups.length === 0) return true;
      return a.maxGroupSize < b.maxGroupSize;
    }
    return a.groups.length > b.groups.length;
  }

  /** Get all answer possibilities, sorted best-first.
   *  Mirrors Python's get_all_answers(). */
  export function getAllAnswers(
    remainingWords: string[],
    validGuesses: string[],
  ): AnswerPossibility[] {
    if (remainingWords.length === 1) {
      const word = remainingWords[0];
      return [makeAnswerPossibility(word, generateGroups(word, remainingWords))];
    }

    // Remaining words first (deduped), then extra valid guesses
    const seen = new Set<string>();
    const candidates: string[] = [];
    for (const w of [...remainingWords, ...validGuesses]) {
      if (!seen.has(w)) {
        seen.add(w);
        candidates.push(w);
      }
    }

    const possibilities = candidates.map((word) =>
      makeAnswerPossibility(word, generateGroups(word, remainingWords)),
    );

    possibilities.sort((a, b) => (isFirstBetter(a, b) ? -1 : 1));
    return possibilities;
  }

  /** Return only words where scoreGuess(guess, word) === result. */
  export function filterWords(remainingWords: string[], guess: string, result: string): string[] {
    return remainingWords.filter((word) => scoreGuessCached(guess, word) === result);
  }
  ```

- [ ] Run `npm test` — all tests must pass.

- [ ] Commit: `git add web/src/solver.ts web/tests/solver.test.ts && git commit -m "feat(web): port solver logic with tests"`

---

## Task 5 — Data Loading

**Files:**
- Create: `web/src/data.ts`

- [ ] Create `web/src/data.ts`:
  ```ts
  import type { AppData } from "./types";

  function parseWordList(text: string): string[] {
    return text
      .split("\n")
      .map((w) => w.trim().toUpperCase())
      .filter((w) => w.length === 5);
  }

  /** Fetch word lists and precomputed data. Call once at app startup. */
  export async function loadData(base: string): Promise<AppData> {
    const [answersText, guessesText, secondGuessesJson] = await Promise.all([
      fetch(`${base}data/valid_answers.txt`).then((r) => r.text()),
      fetch(`${base}data/valid_guesses.txt`).then((r) => r.text()),
      fetch(`${base}data/best_second_guesses.json`).then((r) => r.json()),
    ]);

    return {
      validAnswers: parseWordList(answersText),
      validGuesses: parseWordList(guessesText),
      bestSecondGuesses: secondGuessesJson as Record<string, string>,
    };
  }
  ```
  > **Note:** `base` is `import.meta.env.BASE_URL` from Vite (set to `/octordle_solver/` by `vite.config.ts`). Pass it from `app.ts` rather than reading it in `data.ts` so the module stays testable.

- [ ] Commit: `git add web/src/data.ts && git commit -m "feat(web): add data loader"`

---

## Task 6 — Web Worker

**Files:**
- Create: `web/src/worker.ts`

The worker receives a `WorkerRequest` and posts back a `WorkerResponse`.

- [ ] Create `web/src/worker.ts`:
  ```ts
  import { getAllAnswers } from "./solver";
  import type { WorkerRequest, WorkerResponse } from "./types";

  self.onmessage = (event: MessageEvent<WorkerRequest>) => {
    const { remainingWords, validGuesses } = event.data;
    const possibilities = getAllAnswers(remainingWords, validGuesses);
    const response: WorkerResponse = { possibilities, remainingWords };
    self.postMessage(response);
  };
  ```

- [ ] Verify Vite resolves the worker correctly by importing it in `app.ts` (in a later task) with:
  ```ts
  const worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
  ```
  This is the Vite-recommended pattern for Web Workers.

- [ ] Commit: `git add web/src/worker.ts && git commit -m "feat(web): add solver Web Worker"`

---

## Task 7 — Tile Grid

**Files:**
- Create: `web/src/grid.ts`
- Modify: `web/style.css` (add tile styles)
- Modify: `web/index.html` (add `<div id="grid">`)

The `Grid` class manages the 6×5 tile DOM, keyboard input, and color cycling.

**Tile state machine per row:**
1. User types letters (A–Z): fills `Pending` tiles left-to-right.
2. Backspace: clears rightmost `Pending` tile.
3. Enter (when 5 letters filled): commits the row — all tiles become `Absent` (gray), `letter_is_set = true`.
4. User clicks committed tiles: cycles Absent → Misplaced → Correct → Absent.

- [ ] Add to `web/index.html` inside `<div id="app">`:
  ```html
  <header>
    <h1>Wordle Solver</h1>
    <button id="dark-mode-toggle" aria-label="Toggle dark mode">🌙</button>
  </header>
  <main>
    <div id="grid"></div>
    <div id="sidebar">
      <section id="best-guesses-section">
        <h2>Best Guesses</h2>
        <button id="get-guesses-btn">Get best guesses</button>
        <ul id="best-guesses-list"></ul>
      </section>
      <section id="groups-section">
        <h2>Group Info</h2>
        <p id="groups-stats"></p>
        <ul id="groups-list"></ul>
      </section>
      <section id="remaining-section">
        <h2>Remaining Words (<span id="remaining-count">0</span>)</h2>
        <button id="copy-remaining-btn">Copy</button>
        <ul id="remaining-list"></ul>
      </section>
    </div>
  </main>
  ```

- [ ] Create `web/src/grid.ts`:
  ```ts
  import { TileState } from "./types";

  const CYCLE_ORDER = [TileState.Absent, TileState.Misplaced, TileState.Correct];

  interface Tile {
    el: HTMLElement;
    letter: string;
    state: TileState;
  }

  export class Grid {
    private tiles: Tile[][] = [];
    private currentRow = 0;
    private currentCol = 0;
    private container: HTMLElement;

    constructor(container: HTMLElement) {
      this.container = container;
      this.build();
    }

    private build(): void {
      this.container.innerHTML = "";
      this.tiles = [];
      for (let r = 0; r < 6; r++) {
        const row: Tile[] = [];
        const rowEl = document.createElement("div");
        rowEl.className = "tile-row";
        for (let c = 0; c < 5; c++) {
          const el = document.createElement("div");
          el.className = "tile";
          el.dataset["state"] = TileState.Empty;
          el.addEventListener("click", () => this.onTileClick(r, c));
          rowEl.appendChild(el);
          row.push({ el, letter: "", state: TileState.Empty });
        }
        this.container.appendChild(rowEl);
        this.tiles.push(row);
      }
    }

    private setTileState(r: number, c: number, state: TileState, letter?: string): void {
      const tile = this.tiles[r][c];
      if (letter !== undefined) tile.letter = letter;
      tile.state = state;
      tile.el.dataset["state"] = state;
      tile.el.textContent = tile.letter;
    }

    private onTileClick(r: number, c: number): void {
      const tile = this.tiles[r][c];
      if (!CYCLE_ORDER.includes(tile.state)) return; // not yet committed
      const idx = CYCLE_ORDER.indexOf(tile.state);
      const next = CYCLE_ORDER[(idx + 1) % CYCLE_ORDER.length];
      this.setTileState(r, c, next);
    }

    handleKey(key: string): void {
      if (this.currentRow >= 6) return;
      if (key === "Backspace") {
        if (this.currentCol > 0) {
          this.currentCol--;
          this.setTileState(this.currentRow, this.currentCol, TileState.Empty, "");
        }
      } else if (key === "Enter") {
        if (this.currentCol === 5) {
          for (let c = 0; c < 5; c++) {
            this.setTileState(this.currentRow, c, TileState.Absent);
          }
          this.currentRow++;
          this.currentCol = 0;
        }
      } else if (/^[A-Za-z]$/.test(key) && this.currentCol < 5) {
        this.setTileState(this.currentRow, this.currentCol, TileState.Pending, key.toUpperCase());
        this.currentCol++;
      }
    }

    /** Word from the last committed row. */
    get currentWord(): string {
      const row = this.currentRow - 1;
      if (row < 0) return "";
      return this.tiles[row].map((t) => t.letter).join("");
    }

    /** Score string from the last committed row (Y/M/N). */
    get currentResult(): string {
      const row = this.currentRow - 1;
      if (row < 0) return "";
      return this.tiles[row]
        .map((t) => {
          if (t.state === TileState.Correct) return "Y";
          if (t.state === TileState.Misplaced) return "M";
          return "N";
        })
        .join("");
    }

    /** How many rows have been committed. */
    get committedRows(): number {
      return this.currentRow;
    }

    reset(): void {
      this.currentRow = 0;
      this.currentCol = 0;
      this.build();
    }

    /** Fill the next empty row with the given word. */
    setWord(word: string): void {
      if (this.currentRow >= 6) return;
      for (let c = 0; c < 5; c++) {
        this.setTileState(this.currentRow, c, TileState.Pending, word[c]);
      }
      this.currentCol = 5;
    }
  }
  ```

- [ ] Add tile CSS to `web/style.css`:
  ```css
  :root {
    --color-bg: #ffffff;
    --color-text: #111111;
    --color-border: #d3d6da;
    --color-tile-empty: #ffffff;
    --color-tile-pending: #ffffff;
    --tile-correct: #69ab64;
    --tile-misplaced: #c3ae55;
    --tile-absent: #767a7d;
  }

  [data-theme="dark"] {
    --color-bg: #1f1f1f;
    --color-text: #f2f2f2;
    --color-border: #565758;
    --color-tile-empty: #191a1c;
    --color-tile-pending: #191a1c;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--color-bg); color: var(--color-text); font-family: sans-serif; }
  header { display: flex; align-items: center; gap: 1rem; padding: 1rem; }
  h1 { font-size: 1.4rem; }
  main { display: flex; gap: 1.5rem; padding: 1rem; flex-wrap: wrap; }

  #grid { display: flex; flex-direction: column; gap: 4px; }
  .tile-row { display: flex; gap: 4px; }
  .tile {
    width: 56px; height: 56px;
    border: 2px solid var(--color-border);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; font-weight: bold; text-transform: uppercase;
    background: var(--color-tile-empty); color: var(--color-text);
    cursor: default; user-select: none;
  }
  .tile[data-state="pending"] { background: var(--color-tile-pending); }
  .tile[data-state="absent"]    { background: var(--tile-absent);    color: white; cursor: pointer; }
  .tile[data-state="misplaced"] { background: var(--tile-misplaced); color: white; cursor: pointer; }
  .tile[data-state="correct"]   { background: var(--tile-correct);   color: white; cursor: pointer; }

  #sidebar { display: flex; gap: 1rem; flex-wrap: wrap; }
  section { min-width: 160px; max-width: 220px; }
  h2 { font-size: 0.9rem; margin-bottom: 0.4rem; }
  ul { list-style: none; max-height: 320px; overflow-y: auto; border: 1px solid var(--color-border); }
  li { padding: 2px 6px; cursor: pointer; font-size: 0.85rem; }
  li:hover { background: rgba(128,128,128,0.15); }
  li.selected { background: rgba(128,128,128,0.3); }
  button { margin-bottom: 0.4rem; padding: 4px 10px; cursor: pointer; }
  #groups-stats { font-size: 0.8rem; margin-bottom: 0.4rem; }
  .group-header { font-weight: bold; font-size: 0.85rem; }
  .group-word { padding-left: 12px; }
  ```

- [ ] Start dev server, open browser, confirm the 6×5 grid renders. Type a few letters, press Enter, click tiles to cycle colors. Stop server.

- [ ] Commit: `git add web/src/grid.ts web/style.css web/index.html && git commit -m "feat(web): add tile grid component"`

---

## Task 8 — Panels (Best Guesses + Groups + Remaining Words)

**Files:**
- Create: `web/src/panels.ts`

- [ ] Create `web/src/panels.ts`:
  ```ts
  import type { AnswerPossibility } from "./types";

  type SelectCallback = (possibility: AnswerPossibility) => void;
  type UseWordCallback = (word: string) => void;

  export class BestGuessList {
    private el: HTMLUListElement;
    private possibilities: AnswerPossibility[] = [];
    private onSelect: SelectCallback;
    private onUseWord: UseWordCallback;

    constructor(el: HTMLUListElement, onSelect: SelectCallback, onUseWord: UseWordCallback) {
      this.el = el;
      this.onSelect = onSelect;
      this.onUseWord = onUseWord;
    }

    /** Populate the list. Highlighted items show groups on click; double-click fills the grid. */
    populate(possibilities: AnswerPossibility[], pinnedWord?: string): void {
      this.possibilities = possibilities;
      this.el.innerHTML = "";

      const addItem = (word: string, poss?: AnswerPossibility): void => {
        const li = document.createElement("li");
        li.textContent = word;
        li.addEventListener("click", () => {
          this.el.querySelectorAll("li").forEach((el) => el.classList.remove("selected"));
          li.classList.add("selected");
          if (poss) this.onSelect(poss);
        });
        li.addEventListener("dblclick", () => this.onUseWord(word));
        this.el.appendChild(li);
      };

      if (pinnedWord) addItem(pinnedWord);
      for (const poss of possibilities) {
        if (poss.word !== pinnedWord) addItem(poss.word, poss);
      }
    }

    clear(): void {
      this.el.innerHTML = "";
      this.possibilities = [];
    }
  }

  export class GroupsPanel {
    private listEl: HTMLUListElement;
    private statsEl: HTMLElement;

    constructor(listEl: HTMLUListElement, statsEl: HTMLElement) {
      this.listEl = listEl;
      this.statsEl = statsEl;
    }

    show(possibility: AnswerPossibility): void {
      this.listEl.innerHTML = "";
      const totalGroups = possibility.groups.length;
      const largest = possibility.maxGroupSize;
      const avg = (possibility.groups.reduce((s, g) => s + g.words.length, 0) / totalGroups).toFixed(1);
      this.statsEl.textContent = `Groups: ${totalGroups} | Largest: ${largest} | Avg: ${avg}`;

      for (const group of possibility.groups) {
        const header = document.createElement("li");
        header.className = "group-header";
        header.textContent = group.possibility; // e.g. "YNNMN"
        this.listEl.appendChild(header);
        for (const word of group.words) {
          const item = document.createElement("li");
          item.className = "group-word";
          item.textContent = word;
          this.listEl.appendChild(item);
        }
      }
    }

    clear(): void {
      this.listEl.innerHTML = "";
      this.statsEl.textContent = "";
    }
  }

  export class RemainingWordsPanel {
    private listEl: HTMLUListElement;
    private countEl: HTMLElement;
    private words: string[] = [];

    constructor(listEl: HTMLUListElement, countEl: HTMLElement) {
      this.listEl = listEl;
      this.countEl = countEl;
    }

    update(words: string[]): void {
      this.words = words;
      this.listEl.innerHTML = "";
      this.countEl.textContent = String(words.length);
      for (const word of words) {
        const li = document.createElement("li");
        li.textContent = word;
        this.listEl.appendChild(li);
      }
    }

    copyToClipboard(): void {
      navigator.clipboard.writeText(this.words.join("\n")).catch(() => {
        // Fallback for browsers without clipboard API permission
        const ta = document.createElement("textarea");
        ta.value = this.words.join("\n");
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      });
    }
  }
  ```

- [ ] Commit: `git add web/src/panels.ts && git commit -m "feat(web): add best-guesses, groups, remaining-words panels"`

---

## Task 9 — App Wiring

**Files:**
- Create: `web/src/app.ts`

This is the top-level controller. It owns puzzle state (remaining words, guesses), and coordinates the grid, panels, and worker.

**State the App tracks:**
- `remainingWords: string[]` — starts as all valid answers
- `validGuesses: string[]`
- `bestSecondGuesses: Record<string, string>`
- `guesses: Guess[]` — each committed + colored guess

**Flow for "Get best guesses":**
1. Read `grid.currentWord` and `grid.currentResult`.
2. Filter `remainingWords` using `filterWords()`.
3. Post `{ remainingWords, validGuesses }` to the worker.
4. Disable the button and show "Calculating…".
5. On worker response: re-enable button, populate `BestGuessList` with the pinned second-guess if applicable.

**Second-guess cache lookup:**
Apply when `guesses.length === 1` and `guesses[0].word === "SLATE"`.
Key = result string with `Y→0, M→1, N→2` substituted: e.g. `"YNNNN"` → `"02222"`.

- [ ] Create `web/src/app.ts`:
  ```ts
  import { loadData } from "./data";
  import { filterWords } from "./solver";
  import { Grid } from "./grid";
  import { BestGuessList, GroupsPanel, RemainingWordsPanel } from "./panels";
  import type { AppData, Guess, WorkerRequest, WorkerResponse, AnswerPossibility } from "./types";

  const STARTING_GUESS = "SLATE";

  function resultToSecondGuessKey(result: string): string {
    return result.replace(/Y/g, "0").replace(/M/g, "1").replace(/N/g, "2");
  }

  class App {
    private data!: AppData;
    private remainingWords: string[] = [];
    private guesses: Guess[] = [];
    private worker!: Worker;
    private grid!: Grid;
    private bestGuessList!: BestGuessList;
    private groupsPanel!: GroupsPanel;
    private remainingPanel!: RemainingWordsPanel;
    private getGuessesBtn!: HTMLButtonElement;

    async init(): Promise<void> {
      this.data = await loadData(import.meta.env.BASE_URL);
      this.remainingWords = [...this.data.validAnswers];

      this.worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
      this.worker.onmessage = (e: MessageEvent<WorkerResponse>) => this.onWorkerResult(e.data);

      const gridEl = document.getElementById("grid") as HTMLElement;
      this.grid = new Grid(gridEl);

      this.getGuessesBtn = document.getElementById("get-guesses-btn") as HTMLButtonElement;
      this.getGuessesBtn.addEventListener("click", () => this.onGetGuesses());

      this.bestGuessList = new BestGuessList(
        document.getElementById("best-guesses-list") as HTMLUListElement,
        (poss: AnswerPossibility) => this.groupsPanel.show(poss),
        (word: string) => { this.grid.setWord(word); },
      );
      this.bestGuessList.populate([], STARTING_GUESS);

      this.groupsPanel = new GroupsPanel(
        document.getElementById("groups-list") as HTMLUListElement,
        document.getElementById("groups-stats") as HTMLElement,
      );

      this.remainingPanel = new RemainingWordsPanel(
        document.getElementById("remaining-list") as HTMLUListElement,
        document.getElementById("remaining-count") as HTMLElement,
      );
      this.remainingPanel.update(this.remainingWords);

      document.addEventListener("keydown", (e) => {
        // Don't hijack input when focus is in a button/input
        if (document.activeElement !== document.body && document.activeElement !== gridEl) return;
        this.grid.handleKey(e.key);
      });

      document.getElementById("copy-remaining-btn")!.addEventListener("click", () =>
        this.remainingPanel.copyToClipboard(),
      );

      document.getElementById("dark-mode-toggle")!.addEventListener("click", () =>
        this.toggleDarkMode(),
      );

      document.getElementById("reset-btn")?.addEventListener("click", () => this.reset());

      // Apply system dark-mode preference on load
      if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
        document.documentElement.dataset["theme"] = "dark";
      }
    }

    private onGetGuesses(): void {
      if (this.grid.committedRows === 0) return;

      const word = this.grid.currentWord;
      const result = this.grid.currentResult;

      this.remainingWords = filterWords(this.remainingWords, word, result);
      this.guesses.push({ word, result });

      this.bestGuessList.clear();
      this.groupsPanel.clear();

      // Show cached second guess immediately if applicable
      let pinnedSecondGuess: string | undefined;
      if (this.guesses.length === 1 && word === STARTING_GUESS) {
        const key = resultToSecondGuessKey(result);
        pinnedSecondGuess = this.data.bestSecondGuesses[key];
      }

      this.getGuessesBtn.textContent = "Calculating…";
      this.getGuessesBtn.disabled = true;

      const request: WorkerRequest = {
        remainingWords: this.remainingWords,
        validGuesses: this.data.validGuesses,
      };
      // Stash pinnedSecondGuess for when the worker responds
      this._pendingPinnedGuess = pinnedSecondGuess;
      this.worker.postMessage(request);

      this.remainingPanel.update(this.remainingWords);
    }

    private _pendingPinnedGuess: string | undefined;

    private onWorkerResult(response: WorkerResponse): void {
      this.getGuessesBtn.textContent = "Get best guesses";
      this.getGuessesBtn.disabled = false;
      this.bestGuessList.populate(response.possibilities, this._pendingPinnedGuess);
      this._pendingPinnedGuess = undefined;
    }

    private reset(): void {
      this.remainingWords = [...this.data.validAnswers];
      this.guesses = [];
      this._pendingPinnedGuess = undefined;
      this.grid.reset();
      this.bestGuessList.clear();
      this.bestGuessList.populate([], STARTING_GUESS);
      this.groupsPanel.clear();
      this.remainingPanel.update(this.remainingWords);
      this.getGuessesBtn.textContent = "Get best guesses";
      this.getGuessesBtn.disabled = false;
    }

    private toggleDarkMode(): void {
      const html = document.documentElement;
      html.dataset["theme"] = html.dataset["theme"] === "dark" ? "light" : "dark";
    }
  }

  const app = new App();
  app.init().catch(console.error);
  ```

- [ ] Add a reset button to `index.html` inside `#best-guesses-section` (before the list):
  ```html
  <button id="reset-btn">Reset</button>
  ```

- [ ] Run `npm run dev`. Do a full smoke test:
  1. Page loads; grid shows; remaining words shows 3361.
  2. Type `SLATE`, press Enter, tiles go gray.
  3. Click tiles to set colors. Click "Get best guesses".
  4. Button shows "Calculating…" then re-enables; best guesses list populates.
  5. Click a guess in the list — groups panel populates.
  6. Double-click a guess — grid fills with that word.
  7. Click "Copy" — clipboard contains remaining words.
  8. Click dark-mode toggle — colors flip.
  9. Click "Reset" — everything clears.

- [ ] Commit: `git add web/src/app.ts web/index.html && git commit -m "feat(web): wire up app controller"`

---

## Task 10 — Final Styling Pass

**Files:**
- Modify: `web/style.css`

- [ ] Ensure the layout is usable on a narrow viewport (mobile). Add:
  ```css
  @media (max-width: 600px) {
    .tile { width: 44px; height: 44px; font-size: 1.2rem; }
    main { flex-direction: column; }
    #sidebar { flex-direction: column; }
    section { max-width: 100%; }
  }
  ```

- [ ] Run `npm run dev`, resize the browser window to ~375px width, confirm it's still usable.

- [ ] Commit: `git add web/style.css && git commit -m "feat(web): responsive mobile layout"`

---

## Task 11 — Build and Deploy to GitHub Pages

**Files:**
- Modify: `web/vite.config.ts` (set correct repo name)

- [ ] Edit `web/vite.config.ts` — replace `"octordle_solver"` in `base` with your actual GitHub repo name (check with `git remote -v`).

- [ ] From `web/`: run `npm run build`. Confirm `docs/` is created at the repo root and contains `index.html` + `assets/`.

- [ ] Commit the build output:
  ```powershell
  cd ..  # back to repo root
  git add docs/
  git commit -m "build: initial web UI release"
  git push
  ```

- [ ] On GitHub: Settings → Pages → Source = "Deploy from branch", Branch = `main`, Folder = `/docs`. Save.

- [ ] Visit `https://<username>.github.io/<repo>/` — confirm the page loads and the solver works.

- [ ] Add a note to the top-level `README.md` linking to the live page.

---

## Testing Checklist (manual smoke tests after each significant change)

| Scenario | Expected |
|---|---|
| Type 5 letters + Enter | Row committed, tiles go gray |
| Click tile → cycles colors | GRAY → YELLOW → GREEN → GRAY |
| Backspace before Enter | Removes last typed letter |
| Get best guesses with 0 committed rows | Nothing happens |
| First guess = SLATE | Cached second guess pinned at top of list |
| First guess ≠ SLATE | No pinned second guess |
| Click item in best guesses list | Groups panel updates |
| Double-click item in best guesses list | Grid fills with that word |
| 1 remaining word | List shows 1 entry |
| Copy remaining words | Clipboard contents match list |
| Dark mode toggle | Background/tile colors invert |
| Reset | All state cleared, remaining = 3361 |
| Mobile 375px width | Layout stacks vertically, tiles readable |
