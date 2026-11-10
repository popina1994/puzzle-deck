# Puzzle Deck

Four small browser puzzles in a single, dependency-free HTML file.

**Play it online:** https://claude.ai/code/artifact/192291c1-e8c6-4a9e-8d7f-39b1d2dd475a

## Running it

Open [puzzle-deck.html](puzzle-deck.html) directly in a browser. No build step,
no server, no external libraries — everything (layout, styling, and game
logic) lives in that one file.

## The games

- **Field Sum** — drop a shape onto a 6×6 grid of positive and negative
  numbers to cover the highest sum you can find, then lock in and see how
  close you got to the true optimum. Pick from five shapes (P, Plus, L, T,
  Square) in the shape picker; each has a different number of cells and
  rotation symmetry.
- **Ring Match** — rotate concentric rings of grey wedges until every ring
  lines up with the fixed outer reference ring. Choose 1, 2, or 3 rotatable
  rings to control difficulty.
- **Pipe Slot** — swap tiles (never rotate them) to connect two fixed points
  with a pipe run. Choose a 5×5, 7×7, or 9×9 board.
- **Word Pairs** — a timed verbal-reasoning quiz: for each word pair, decide
  whether the words mean the same thing, mean the opposite, or have no
  relation.

## Sanity checks

[sanity_check.py](sanity_check.py) mirrors the trickier bits of the game
logic in Python and exercises them directly, since there's no JS runtime
available in this environment to run the HTML file's own script. Run it with:

```bash
python3 sanity_check.py
```

It checks:

- **Field Sum** — every shape's rotations/mirrors stay the right size and fit
  the grid, and the brute-force "optimal sum" search always finds a real
  placement.
- **Ring Match** — the rotation-offset arithmetic always resolves cleanly to
  a matched state (offset 0), for 1–3 rings.
- **Pipe Slot** — the board generator produces a solved layout before
  shuffling, shuffling reliably breaks that solved state, and generation
  stays fast at every board size.

That last point mattered in practice: the first version of the Pipe Slot
generator built a path by walking the grid and backtracking on dead ends,
un-visiting cells as it went. That's an exhaustive search over *all* simple
paths between two points, and it blows up combinatorially once the board
gets much bigger than 5×5 — it visibly hung at 9×9. The fix grows a random
spanning tree over the whole board instead (every cell visited exactly once,
never un-visited) and reads the path off with parent pointers, which stays
fast — microseconds — regardless of board size.
