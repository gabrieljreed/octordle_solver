import type { AppData } from "./types";

function parseWordList(text: string): string[] {
  return text
    .split("\n")
    .map((w) => w.trim().toUpperCase())
    .filter((w) => w.length === 5);
}

/**
 * Fetch word lists and precomputed data. Call once at app startup.
 * base should be import.meta.env.BASE_URL (set by Vite config).
 */
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
