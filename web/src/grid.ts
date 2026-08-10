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

  /** Word from the last committed row (uppercase). */
  get currentWord(): string {
    const row = this.currentRow - 1;
    if (row < 0) return "";
    return this.tiles[row].map((t) => t.letter).join("");
  }

  /** Score string (Y/M/N) from the last committed row. */
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

  /** Number of rows that have been committed (Enter pressed). */
  get committedRows(): number {
    return this.currentRow;
  }

  reset(): void {
    this.currentRow = 0;
    this.currentCol = 0;
    this.build();
  }

  /** Fill the current (uncommitted) row with the given word. */
  setWord(word: string): void {
    if (this.currentRow >= 6) return;
    // Clear any partially typed letters first
    for (let c = 0; c < 5; c++) {
      this.setTileState(this.currentRow, c, TileState.Empty, "");
    }
    for (let c = 0; c < 5; c++) {
      this.setTileState(this.currentRow, c, TileState.Pending, word[c]);
    }
    this.currentCol = 5;
  }
}
