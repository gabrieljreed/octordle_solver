import { describe, it, expect } from "vitest";
import { scoreGuess, generateGroups, getAllAnswers, filterWords } from "../src/solver";

describe("scoreGuess", () => {
  it("all correct", () => {
    expect(scoreGuess("CRANE", "CRANE")).toBe("YYYYY");
  });
  it("all absent", () => {
    expect(scoreGuess("ZZZZZ", "CRANE")).toBe("NNNNN");
  });
  it("mixed correct/misplaced/absent — SLATE vs STALE", () => {
    // s=Y, l=M(in remaining [t,l]), a=Y, t=M(in remaining [t]), e=Y
    expect(scoreGuess("SLATE", "STALE")).toBe("YMYMY");
  });
  it("duplicate letters — only marks as many as exist in answer", () => {
    // EJECT vs CREAM: E at pos2 is exact match (Y); E at pos0 is N because that E was already consumed
    // E(0)≠C → N, J(1)≠R → N, E(2)==E → Y, C(3)≠A but C in remaining → M, T(4)≠M → N
    expect(scoreGuess("EJECT", "CREAM")).toBe("NNYMN");
  });
  it("misplaced duplicate does not double-count", () => {
    // LLAMA vs HOTEL: one L in hotel (pos4); guess[0]='L' → M (consumes it), guess[1]='L' → N (no L left)
    expect(scoreGuess("LLAMA", "HOTEL")).toBe("MNNNN");
  });
  it("correct takes priority over misplaced for same letter", () => {
    // guess ABBEY, answer KEBAB: A=N, B=M(b at pos3), B=Y(pos2==pos2? no)
    // ABBEY: A B B E Y  vs  KEBAB: K E B A B
    // A(0) vs K(0): N. B(1) vs E(1): N (no b at pos1, remaining=[K,E,A,B] minus corrects)
    // first pass: only B(2)==B(2) → Y. remaining=[K,E,A,B]
    // second pass: A(0)→not in [K,E,A,B]? A is in remaining → M. B(1)→B in remaining → M. E(3)→E in remaining → M. Y(4)→N
    expect(scoreGuess("ABBEY", "KEBAB")).toBe("MMYMN");
  });
});

describe("generateGroups", () => {
  it("single word — one group scored YYYYY", () => {
    const groups = generateGroups("CRANE", ["CRANE"]);
    expect(groups).toHaveLength(1);
    expect(groups[0].possibility).toBe("YYYYY");
    expect(groups[0].words).toEqual(["CRANE"]);
  });
  it("two words with different scores produce two groups", () => {
    const groups = generateGroups("CRANE", ["CRANE", "AUDIO"]);
    expect(groups).toHaveLength(2);
  });
  it("two words with the same score produce one group", () => {
    // ZZZZZ scores every word as NNNNN
    const groups = generateGroups("ZZZZZ", ["CRANE", "AUDIO"]);
    expect(groups).toHaveLength(1);
    expect(groups[0].words).toHaveLength(2);
  });
});

describe("getAllAnswers", () => {
  const words = ["CRANE", "AUDIO", "STALE", "SUITE"];

  it("returns one entry per unique candidate", () => {
    const results = getAllAnswers(words, []);
    expect(results).toHaveLength(4);
  });

  it("sorted: more groups first, then smaller maxGroupSize", () => {
    const results = getAllAnswers(words, []);
    for (let i = 1; i < results.length; i++) {
      const prev = results[i - 1];
      const curr = results[i];
      const prevBetter =
        prev.groups.length > curr.groups.length ||
        (prev.groups.length === curr.groups.length && prev.maxGroupSize <= curr.maxGroupSize);
      expect(prevBetter).toBe(true);
    }
  });

  it("single remaining word returns immediately without scanning guesses", () => {
    const results = getAllAnswers(["CRANE"], []);
    expect(results).toHaveLength(1);
    expect(results[0].word).toBe("CRANE");
  });

  it("deduplicates remaining words and valid guesses", () => {
    const results = getAllAnswers(["CRANE"], ["CRANE", "AUDIO"]);
    expect(results.map((r) => r.word)).toContain("CRANE");
  });
});

describe("filterWords", () => {
  it("keeps only words consistent with guess/result", () => {
    const filtered = filterWords(["CRANE", "STALE", "AUDIO"], "CRANE", "YYYYY");
    expect(filtered).toEqual(["CRANE"]);
  });
  it("returns empty array when no words match", () => {
    const filtered = filterWords(["AUDIO"], "CRANE", "YYYYY");
    expect(filtered).toEqual([]);
  });
  it("keeps multiple matching words", () => {
    // ZZZZZ scores everything NNNNN — all words match
    const words = ["CRANE", "AUDIO", "STALE"];
    const filtered = filterWords(words, "ZZZZZ", "NNNNN");
    expect(filtered).toEqual(words);
  });
});
