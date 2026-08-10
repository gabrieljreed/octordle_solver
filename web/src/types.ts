/** Feedback state for a single tile. */
export enum TileState {
  Empty = "empty",
  Pending = "pending",
  Absent = "absent",      // gray  (N)
  Misplaced = "misplaced", // yellow (M)
  Correct = "correct",    // green  (Y)
}

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
  result: string; // 5-char score string (Y/M/N)
}

// Messages to/from the Web Worker
export interface WorkerRequest {
  remainingWords: string[];
  validGuesses: string[];
}

export interface WorkerResponse {
  possibilities: AnswerPossibility[];
}

export interface AppData {
  validAnswers: string[];
  validGuesses: string[];
  bestSecondGuesses: Record<string, string>;
}
