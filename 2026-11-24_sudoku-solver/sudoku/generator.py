"""유일해를 보장하는 스도쿠 퍼즐 생성기.

1) 무작위 순서로 후보를 시도하는 백트래킹으로 완성 격자를 만든다.
2) 칸을 무작위 순서로 하나씩 지우고, 지운 뒤 해가 2개 이상이 되면 되돌린다.
3) 목표 단서 수에 도달하거나 더 지울 칸이 없으면 멈춘다.
같은 seed 는 항상 같은 퍼즐을 만든다(random.Random 인스턴스를 따로 사용).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .board import SIZE, Grid, box_index
from .solver import count_solutions

MIN_CLUES = 17  # 유일해 스도쿠의 이론적 최소 단서 수


@dataclass
class Generated:
    puzzle: Grid
    solution: Grid
    seed: int | None

    @property
    def clues(self) -> int:
        return sum(1 for row in self.puzzle for v in row if v)


def _random_full_grid(rng: random.Random) -> Grid:
    grid = [[0] * SIZE for _ in range(SIZE)]
    rows = [0] * SIZE
    cols = [0] * SIZE
    boxes = [0] * SIZE

    def fill(pos: int) -> bool:
        if pos == SIZE * SIZE:
            return True
        r, c = divmod(pos, SIZE)
        b = box_index(r, c)
        digits = list(range(1, 10))
        rng.shuffle(digits)
        for v in digits:
            bit = 1 << v
            if (rows[r] | cols[c] | boxes[b]) & bit:
                continue
            grid[r][c] = v
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            if fill(pos + 1):
                return True
            grid[r][c] = 0
            rows[r] &= ~bit
            cols[c] &= ~bit
            boxes[b] &= ~bit
        return False

    fill(0)
    return grid


def generate(seed: int | None = None, clues: int = 30) -> Generated:
    """유일해 퍼즐을 생성한다. clues 는 남길 단서 수 목표(최소 17).

    목표까지 지우지 못하면(더 지우면 유일해가 깨짐) 가능한 만큼만 지운 퍼즐을 반환한다.
    """
    if not MIN_CLUES <= clues <= SIZE * SIZE:
        raise ValueError(f"단서 수는 {MIN_CLUES}~81 사이여야 합니다: {clues}")
    rng = random.Random(seed)
    solution = _random_full_grid(rng)
    puzzle = [row[:] for row in solution]
    cells = [(r, c) for r in range(SIZE) for c in range(SIZE)]
    rng.shuffle(cells)
    remaining = SIZE * SIZE
    for r, c in cells:
        if remaining <= clues:
            break
        v = puzzle[r][c]
        puzzle[r][c] = 0
        if count_solutions(puzzle, limit=2) != 1:
            puzzle[r][c] = v
        else:
            remaining -= 1
    return Generated(puzzle, solution, seed)
