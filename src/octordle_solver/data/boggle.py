"""Boggle solver."""

import time
from pathlib import Path

DICTIONARY_PATH = Path(__file__).parent / "Collins Scrabble Words (2019).txt"
words = DICTIONARY_PATH.read_text().split("\n")[1:]
words = [w for w in words if len(w) >= 3]


class TrieNode:
    """Node for a trie."""

    def __init__(self):
        """Initialize the node."""
        self.children: dict[str, TrieNode] = {}
        self.is_word = False


def build_trie(words: list[str]) -> TrieNode:
    """Build a trie from a list of words."""
    root = TrieNode()
    for word in words:
        node = root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_word = True
    return root


def find_words(board: list[list[str]], words: list[str]) -> set[str]:
    """Find words in a given boggle board."""
    rows, cols = len(board), len(board[0])
    found = set()
    trie = build_trie(words)

    def dfs(r: int, c: int, node: TrieNode, prefix: str, visited: set[tuple[int, int]]):
        if (r, c) in visited:
            return
        char = board[r][c]
        if char not in node.children:
            return
        visited.add((r, c))
        node = node.children[char]
        word = prefix + char

        if node.is_word:
            found.add(word)

        # Explore all 8 directions
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                dfs(nr, nc, node, word, visited)

        visited.remove((r, c))  # backtrack

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, trie, "", set())

    return found


board = [["T", "H", "I", "S"], ["W", "A", "T", "S"], ["O", "A", "H", "G"], ["F", "G", "D", "T"]]

start_time = time.time()
found_words = find_words(board, words)
end_time = time.time()
for word in found_words:
    print(word)
print(len(found_words))
print(f"Time: {end_time - start_time} seconds")
