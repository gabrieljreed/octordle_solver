import type { AnswerPossibility, Group } from "./types";

/**
 * Simulate Wordle feedback for a guess vs. the real answer.
 * Returns a 5-char string: Y=correct, M=misplaced, N=absent.
 * Mirrors Python's score_guess() in solver.py.
 */
export function scoreGuess(guess: string, answer: string): string {
  const feedback: string[] = ["N", "N", "N", "N", "N"];
  const remainingCounts: Record<string, number> = {};

  // First pass: mark correct letters, count unmatched answer letters
  for (let i = 0; i < 5; i++) {
    if (guess[i] === answer[i]) {
      feedback[i] = "Y";
    } else {
      remainingCounts[answer[i]] = (remainingCounts[answer[i]] ?? 0) + 1;
    }
  }

  // Second pass: mark misplaced letters (consume from remaining counts)
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

/** Group remainingWords by how they score against word. */
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

/**
 * Compare two AnswerPossibility objects.
 * More groups wins; tie → smaller maxGroupSize wins.
 * Mirrors Python's AnswerPossibility.__gt__().
 */
function isFirstBetter(a: AnswerPossibility, b: AnswerPossibility): boolean {
  if (a.groups.length === b.groups.length) {
    if (a.groups.length === 0) return true;
    return a.maxGroupSize < b.maxGroupSize;
  }
  return a.groups.length > b.groups.length;
}

/**
 * Get all answer possibilities sorted best-first.
 * Mirrors Python's get_all_answers().
 */
export function getAllAnswers(remainingWords: string[], validGuesses: string[]): AnswerPossibility[] {
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
