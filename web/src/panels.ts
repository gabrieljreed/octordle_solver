import type { AnswerPossibility } from "./types";

type SelectCallback = (possibility: AnswerPossibility) => void;
type UseWordCallback = (word: string) => void;

export class BestGuessList {
  private el: HTMLUListElement;
  private possibilitiesMap = new Map<string, AnswerPossibility>();
  private onSelect: SelectCallback;
  private onUseWord: UseWordCallback;

  constructor(el: HTMLUListElement, onSelect: SelectCallback, onUseWord: UseWordCallback) {
    this.el = el;
    this.onSelect = onSelect;
    this.onUseWord = onUseWord;
  }

  /**
   * Populate the list. pinnedWord (if given) is shown at the top without group data.
   * Double-clicking any word fills the grid with it.
   */
  populate(possibilities: AnswerPossibility[], pinnedWord?: string): void {
    this.possibilitiesMap.clear();
    this.el.innerHTML = "";

    const addItem = (word: string, poss?: AnswerPossibility): void => {
      const li = document.createElement("li");
      li.textContent = word;
      if (poss) {
        li.addEventListener("click", () => {
          this.el.querySelectorAll("li").forEach((el) => el.classList.remove("selected"));
          li.classList.add("selected");
          this.onSelect(poss);
        });
      }
      li.addEventListener("dblclick", () => this.onUseWord(word));
      this.el.appendChild(li);
    };

    if (pinnedWord) addItem(pinnedWord);

    for (const poss of possibilities) {
      this.possibilitiesMap.set(poss.word, poss);
      if (poss.word !== pinnedWord) addItem(poss.word, poss);
    }
  }

  clear(): void {
    this.el.innerHTML = "";
    this.possibilitiesMap.clear();
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
    if (totalGroups === 0) return;

    const largest = possibility.maxGroupSize;
    const avg = (
      possibility.groups.reduce((s, g) => s + g.words.length, 0) / totalGroups
    ).toFixed(1);
    this.statsEl.textContent = `Groups: ${totalGroups} | Largest: ${largest} | Avg: ${avg}`;

    for (const group of possibility.groups) {
      const header = document.createElement("li");
      header.className = "group-header";
      header.textContent = group.possibility;
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
    const text = this.words.join("\n");
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => this.fallbackCopy(text));
    } else {
      this.fallbackCopy(text);
    }
  }

  private fallbackCopy(text: string): void {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }
}
