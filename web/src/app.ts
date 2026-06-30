import { loadData } from "./data";
import { filterWords } from "./solver";
import { Grid } from "./grid";
import { BestGuessList, GroupsPanel, RemainingWordsPanel } from "./panels";
import { OnScreenKeyboard } from "./keyboard";
import type { AppData, Guess, WorkerRequest, WorkerResponse, AnswerPossibility } from "./types";

const STARTING_GUESS = "SLATE";

/**
 * Convert a Y/M/N result string to the key format used in best_second_guesses.json.
 * Y→0, M→1, N→2  (matches Python's PossibilityState int values)
 */
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
  private loadingEl!: HTMLElement;
  private pendingPinnedGuess: string | undefined;

  async init(): Promise<void> {
    // Show a loading state while data files download
    document.getElementById("app")!.innerHTML = `<p style="padding:2rem">Loading word lists…</p>`;

    this.data = await loadData(import.meta.env.BASE_URL);
    this.remainingWords = [...this.data.validAnswers];

    // Restore full app HTML now that data is loaded
    document.getElementById("app")!.innerHTML = `
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
            <button id="reset-btn">Reset</button>
            <div id="loading">Calculating…</div>
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
      <div id="keyboard"></div>
    `;

    this.worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
    this.worker.onmessage = (e: MessageEvent<WorkerResponse>) => this.onWorkerResult(e.data);

    const gridEl = document.getElementById("grid") as HTMLElement;
    this.grid = new Grid(gridEl);

    this.getGuessesBtn = document.getElementById("get-guesses-btn") as HTMLButtonElement;
    this.loadingEl = document.getElementById("loading") as HTMLElement;

    this.bestGuessList = new BestGuessList(
      document.getElementById("best-guesses-list") as HTMLUListElement,
      (poss: AnswerPossibility) => this.groupsPanel.show(poss),
      (word: string) => this.grid.setWord(word),
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

    this.getGuessesBtn.addEventListener("click", () => this.onGetGuesses());
    document.getElementById("reset-btn")!.addEventListener("click", () => this.reset());
    document.getElementById("copy-remaining-btn")!.addEventListener("click", () =>
      this.remainingPanel.copyToClipboard(),
    );
    document.getElementById("dark-mode-toggle")!.addEventListener("click", () =>
      this.toggleDarkMode(),
    );

    new OnScreenKeyboard(
      document.getElementById("keyboard") as HTMLElement,
      (key) => this.grid.handleKey(key),
    );

    document.addEventListener("keydown", (e) => {
      // Ignore key events when the user is interacting with a button
      const tag = (document.activeElement as HTMLElement)?.tagName;
      if (tag === "BUTTON" || tag === "INPUT" || tag === "TEXTAREA") return;
      this.grid.handleKey(e.key);
    });

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

    // Show cached second guess immediately if this was the opening SLATE guess
    let pinnedSecondGuess: string | undefined;
    if (this.guesses.length === 1 && word === STARTING_GUESS) {
      const key = resultToSecondGuessKey(result);
      pinnedSecondGuess = this.data.bestSecondGuesses[key];
    }

    this.pendingPinnedGuess = pinnedSecondGuess;
    this.loadingEl.classList.add("visible");
    this.getGuessesBtn.disabled = true;

    const request: WorkerRequest = {
      remainingWords: this.remainingWords,
      validGuesses: this.data.validGuesses,
    };
    this.worker.postMessage(request);

    this.remainingPanel.update(this.remainingWords);
  }

  private onWorkerResult(response: WorkerResponse): void {
    this.loadingEl.classList.remove("visible");
    this.getGuessesBtn.disabled = false;
    this.bestGuessList.populate(response.possibilities, this.pendingPinnedGuess);
    this.pendingPinnedGuess = undefined;
  }

  private reset(): void {
    this.remainingWords = [...this.data.validAnswers];
    this.guesses = [];
    this.pendingPinnedGuess = undefined;
    this.grid.reset();
    this.bestGuessList.clear();
    this.bestGuessList.populate([], STARTING_GUESS);
    this.groupsPanel.clear();
    this.remainingPanel.update(this.remainingWords);
    this.loadingEl.classList.remove("visible");
    this.getGuessesBtn.disabled = false;
  }

  private toggleDarkMode(): void {
    const html = document.documentElement;
    html.dataset["theme"] = html.dataset["theme"] === "dark" ? "light" : "dark";
  }
}

const app = new App();
app.init().catch(console.error);
