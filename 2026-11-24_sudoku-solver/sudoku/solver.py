"""비트마스크 + MRV(최소 남은 값) 휴리스틱 백트래킹 스도쿠 솔버."""

from __future__ import annotations

from dataclasses import dataclass, field

from .board import BOX, SIZE, Grid, box_index, is_valid

ALL = 0x3FE  # 비트 1..9 세트


@dataclass
class SolveStats:
    nodes: int = 0          # 탐색한 노드(값 시도) 수
    backtracks: int = 0     # 되돌아간 횟수
    solutions: int = 0      # 찾은 해의 수


@dataclass
class _State:
    grid: Grid
    rows: list[int] = field(default_factory=lambda: [0] * SIZE)
    cols: list[int] = field(default_factory=lambda: [0] * SIZE)
    boxes: list[int] = field(default_factory=lambda: [0] * SIZE)


def _init_state(grid: Grid) -> _State:
    st = _State([row[:] for row in grid])
    for r in range(SIZE):
        for c in range(SIZE):
            v = st.grid[r][c]
            if v:
                bit = 1 << v
                st.rows[r] |= bit
                st.cols[c] |= bit
                st.boxes[box_index(r, c)] |= bit
    return st


def _candidates(st: _State, r: int, c: int) -> int:
    return ALL & ~(st.rows[r] | st.cols[c] | st.boxes[box_index(r, c)])


def candidates(grid: Grid, r: int, c: int) -> list[int]:
    """(r, c) 칸에 들어갈 수 있는 숫자 목록. 이미 채워진 칸이면 빈 리스트."""
    if grid[r][c]:
        return []
    st = _init_state(grid)
    mask = _candidates(st, r, c)
    return [v for v in range(1, 10) if mask >> v & 1]


def _pick_cell(st: _State) -> tuple[int, int, int] | None:
    """후보 수가 가장 적은 빈칸을 고른다. 빈칸이 없으면 None."""
    best = None
    best_count = 10
    for r in range(SIZE):
        row = st.grid[r]
        for c in range(SIZE):
            if row[c]:
                continue
            mask = _candidates(st, r, c)
            cnt = mask.bit_count()
            if cnt < best_count:
                best, best_count = (r, c, mask), cnt
                if cnt <= 1:
                    return best
    return best


def _search(st: _State, stats: SolveStats, limit: int, out: list[Grid]) -> bool:
    """해를 찾아 out 에 추가한다. limit 개를 찾으면 True 를 반환해 탐색을 중단한다."""
    pick = _pick_cell(st)
    if pick is None:
        stats.solutions += 1
        out.append([row[:] for row in st.grid])
        return len(out) >= limit
    r, c, mask = pick
    b = box_index(r, c)
    while mask:
        low = mask & -mask
        mask ^= low
        v = low.bit_length() - 1
        stats.nodes += 1
        st.grid[r][c] = v
        st.rows[r] |= low
        st.cols[c] |= low
        st.boxes[b] |= low
        if _search(st, stats, limit, out):
            return True
        st.grid[r][c] = 0
        st.rows[r] &= ~low
        st.cols[c] &= ~low
        st.boxes[b] &= ~low
        stats.backtracks += 1
    return False


def solve_all(grid: Grid, limit: int = 2) -> tuple[list[Grid], SolveStats]:
    """최대 limit 개의 해와 탐색 통계를 반환한다. 규칙 위반 입력이면 해 0개."""
    stats = SolveStats()
    if not is_valid(grid):
        return [], stats
    out: list[Grid] = []
    _search(_init_state(grid), stats, limit, out)
    return out, stats


def solve(grid: Grid) -> Grid | None:
    """해 하나를 반환한다. 해가 없으면 None."""
    sols, _ = solve_all(grid, limit=1)
    return sols[0] if sols else None


def count_solutions(grid: Grid, limit: int = 2) -> int:
    """해의 개수를 limit 까지 센다(유일해 검사용)."""
    sols, _ = solve_all(grid, limit=limit)
    return len(sols)


def has_unique_solution(grid: Grid) -> bool:
    return count_solutions(grid, limit=2) == 1


__all__ = [
    "SolveStats",
    "candidates",
    "solve",
    "solve_all",
    "count_solutions",
    "has_unique_solution",
    "BOX",
]
