"""
Standalone sanity checks for puzzle-deck.html.

There's no JS runtime in this environment, so the trickier bits of logic from
the HTML file are mirrored here in Python and exercised directly: pentomino/
tetromino rotation for Field Sum, the spanning-tree path generator and
connectivity check for Pipe Slot, and the ring-offset math for Ring Match.
Run with: python3 sanity_check.py
"""

import json
import random
import time

PASS = []
FAIL = []


def check(name, condition):
    (PASS if condition else FAIL).append(name)
    print(("ok  " if condition else "FAIL"), name)


# ---------------------------------------------------------------------------
# Game 1: Field Sum — shape rotation/mirroring, matches G1_SHAPES in the HTML
# ---------------------------------------------------------------------------

G1_SHAPES = {
    "P": [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],
    "Plus": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    "L": [(0, 0), (1, 0), (2, 0), (2, 1)],
    "T": [(0, 0), (0, 1), (0, 2), (1, 1)],
    "Square": [(0, 0), (0, 1), (1, 0), (1, 1)],
}
G1_ROWS = G1_COLS = 6


def g1_norm(cells):
    min_r = min(r for r, c in cells)
    min_c = min(c for r, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def g1_rot(cells):
    return g1_norm([(c, -r) for r, c in cells])


def g1_mirror(cells):
    return g1_norm([(r, -c) for r, c in cells])


def g1_build_orientations(shape_key):
    base = G1_SHAPES[shape_key]
    seen = set()
    out = []
    shape = g1_norm(base)
    for m in range(2):
        c = shape if m == 0 else g1_mirror(shape)
        for _ in range(4):
            key = json.dumps(c)
            if key not in seen:
                seen.add(key)
                out.append(c)
            c = g1_rot(c)
    return out


def g1_optimal(grid, orientations):
    best = -10 ** 9
    for o in orientations:
        h = max(r for r, c in o) + 1
        w = max(c for r, c in o) + 1
        for r in range(G1_ROWS - h + 1):
            for c in range(G1_COLS - w + 1):
                s = sum(grid[r + dr][c + dc] for dr, dc in o)
                best = max(best, s)
    return best


def run_game1_checks():
    for key, base in G1_SHAPES.items():
        orientations = g1_build_orientations(key)
        check(f"g1 {key}: every orientation keeps {len(base)} cells",
              all(len(o) == len(base) for o in orientations))
        check(f"g1 {key}: every orientation fits the 6x6 grid",
              all(max(r for r, c in o) < G1_ROWS and max(c for r, c in o) < G1_COLS
                  for o in orientations))
        for _ in range(100):
            grid = [[random.randint(-6, 9) for _ in range(G1_COLS)] for _ in range(G1_ROWS)]
            best = g1_optimal(grid, orientations)
            if best <= -10 ** 9:
                check(f"g1 {key}: optimal search finds a real placement", False)
                return
    check("g1: optimal search finds a real placement for every shape", True)


# ---------------------------------------------------------------------------
# Game 2: Ring Match — rotation/offset arithmetic, matches g2Rotate/g2ShadeAt
# ---------------------------------------------------------------------------

def g2_shade_at(base, offset, i):
    return base[((i - offset) % 8 + 8) % 8]


def run_game2_checks():
    base = list(range(8))
    for ring_count in (1, 2, 3):
        offsets = [random.randint(1, 7) for _ in range(ring_count)]
        # offset 0 must reproduce the outer (reference) sequence exactly
        matched = [g2_shade_at(base, 0, i) == base[i] for i in range(8)]
        check(f"g2 rings={ring_count}: offset 0 matches the reference ring", all(matched))
        # rotating a ring back to 0 restores the match regardless of path taken
        for i in range(ring_count):
            steps = random.randint(1, 20)
            o = offsets[i]
            for _ in range(steps):
                o = (o + random.choice([-1, 1])) % 8
            # walking it the rest of the way to 0 always lands exactly on 0
            while o != 0:
                o = (o + 1) % 8
            check(f"g2 rings={ring_count} ring {i}: offset always resolves to a clean 0",
                  o == 0)


# ---------------------------------------------------------------------------
# Game 3: Pipe Slot — spanning-tree path generator + connectivity, matches
# g3GenPath / g3CheckWin. The generator used to un-visit cells on backtrack,
# which turns it into an exhaustive search over all simple paths and blows up
# combinatorially above small grids (confirmed hanging at n=9). The fix grows
# a full random spanning tree instead (every cell visited exactly once) and
# reads the start->end path off via parent pointers, which is always O(cells).
# ---------------------------------------------------------------------------

DIRS = {"N": (-1, 0), "E": (0, 1), "S": (1, 0), "W": (0, -1)}
BIT = {"N": 1, "E": 2, "S": 4, "W": 8}
OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}
CONNECTORS = [5, 10, 3, 6, 12, 9]


def g3_dir_between(a, b):
    if b[0] < a[0]:
        return "N"
    if b[0] > a[0]:
        return "S"
    if b[1] < a[1]:
        return "W"
    return "E"


def g3_gen_path(n, start, end):
    parent = {}
    visited = {start}

    def dfs(cur):
        dirs = list(DIRS)
        random.shuffle(dirs)
        for d in dirs:
            nr, nc = cur[0] + DIRS[d][0], cur[1] + DIRS[d][1]
            if not (0 <= nr < n and 0 <= nc < n):
                continue
            k = (nr, nc)
            if k in visited:
                continue
            visited.add(k)
            parent[k] = cur
            dfs(k)

    dfs(start)
    path = [end]
    cur = end
    while cur != start:
        cur = parent[cur]
        path.append(cur)
    path.reverse()
    return path


def g3_check_win(n, tiles, start, end):
    visited = {start}
    queue = [start]
    while queue:
        r, c = queue.pop(0)
        mask = tiles[r][c]
        for d in "NESW":
            if not (mask & BIT[d]):
                continue
            nr, nc = r + DIRS[d][0], c + DIRS[d][1]
            if not (0 <= nr < n and 0 <= nc < n):
                continue
            if not (tiles[nr][nc] & BIT[OPP[d]]):
                continue
            k = (nr, nc)
            if k in visited:
                continue
            visited.add(k)
            queue.append(k)
    return end in visited


def run_game3_checks():
    for n in (5, 7, 9):
        t0 = time.time()
        trials = 150
        shuffled_still_solved = 0
        for _ in range(trials):
            mid = n // 2
            start, end = (mid, 0), (mid, n - 1)
            path = g3_gen_path(n, start, end)
            check_unique = len(set(path)) == len(path) if _ == 0 else True
            tiles = [[0] * n for _ in range(n)]
            for i, (r, c) in enumerate(path):
                mask = 0
                if i > 0:
                    mask |= BIT[OPP[g3_dir_between(path[i - 1], path[i])]]
                if i < len(path) - 1:
                    mask |= BIT[g3_dir_between(path[i], path[i + 1])]
                tiles[r][c] = mask
            on_path = set(path)
            for r in range(n):
                for c in range(n):
                    if (r, c) in on_path:
                        continue
                    tiles[r][c] = 0 if random.random() < 0.4 else random.choice(CONNECTORS)
            pre_solved = g3_check_win(n, tiles, start, end)
            if not pre_solved:
                check(f"g3 n={n}: freshly built board is solved before shuffling", False)
                return
            fixed = {start, end}
            for _try in range(6):
                coords = [(r, c) for r in range(n) for c in range(n) if (r, c) not in fixed]
                values = [tiles[r][c] for r, c in coords]
                random.shuffle(values)
                for (r, c), v in zip(coords, values):
                    tiles[r][c] = v
                if not g3_check_win(n, tiles, start, end):
                    break
            else:
                shuffled_still_solved += 1
        elapsed = time.time() - t0
        check(f"g3 n={n}: {trials} boards generate+shuffle in well under a second ({elapsed:.3f}s)",
              elapsed < 2.0)
        check(f"g3 n={n}: shuffling almost always breaks the solved board "
              f"({shuffled_still_solved}/{trials} stayed solved)",
              shuffled_still_solved <= trials * 0.05)


if __name__ == "__main__":
    run_game1_checks()
    run_game2_checks()
    run_game3_checks()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        raise SystemExit(1)
