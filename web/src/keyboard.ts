type KeyHandler = (key: string) => void;

const ROWS = [
  ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
  ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
  ["Enter", "Z", "X", "C", "V", "B", "N", "M", "Backspace"],
];

export class OnScreenKeyboard {
  private container: HTMLElement;
  private onKey: KeyHandler;

  constructor(container: HTMLElement, onKey: KeyHandler) {
    this.container = container;
    this.onKey = onKey;
    this.build();
  }

  private build(): void {
    this.container.innerHTML = "";
    for (const row of ROWS) {
      const rowEl = document.createElement("div");
      rowEl.className = "kb-row";
      for (const key of row) {
        const btn = document.createElement("button");
        btn.className = "kb-key";
        btn.textContent = key === "Backspace" ? "⌫" : key;
        btn.dataset["key"] = key;
        if (key === "Enter" || key === "Backspace") {
          btn.classList.add("kb-key--wide");
        }
        btn.addEventListener("click", () => {
          this.onKey(key);
          btn.blur(); // return focus to body so physical keyboard still works
        });
        rowEl.appendChild(btn);
      }
      this.container.appendChild(rowEl);
    }
  }
}
