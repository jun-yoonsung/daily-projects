"""사람이 쓰는 기법으로 푸는 논리 풀이기 — 난이도 평가와 단계별 설명에 사용한다.

기법 (쉬운 순서):
  1. Naked Single  : 어떤 칸의 후보가 하나뿐이면 그 값을 넣는다.
  2. Hidden Single : 한 행/열/박스에서 어떤 숫자가 들어갈 수 있는 칸이 하나뿐이면 그 칸에 넣는다.
  3. Naked Pair    : 한 단위 안 두 칸의 후보가 같은 두 숫자뿐이면, 같은 단위의 다른 칸에서 그 두 숫자를 지운다.
매 단계마다 가장 쉬운 기법부터 다시 시도한다. 셋 다 막히면 "백트래킹 필요"로 멈춘다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .board import BOX, SIZE, Grid, is_valid

NAKED_SINGLE = "Naked Single"
HIDDEN_SINGLE = "Hidden Single"
NAKED_PAIR = "Naked Pair"
TECHNIQUES = [NAKED_SINGLE, HIDDEN_SINGLE, NAKED_PAIR]

LEVELS = {  # 필요했던 가장 어려운 기법 → 등급
    None: "쉬움",
    NAKED_SINGLE: "쉬움",
    HIDDEN_SINGLE: "보통",
    NAKED_PAIR: "어려움",
}
EXPERT = "전문가"

Cell = tuple[int, int]


def _units() -> list[tuple[str, list[Cell]]]:
    units: list[tuple[str, list[Cell]]] = []
    for r in range(SIZE):
        units.append((f"{r + 1}행", [(r, c) for c in range(SIZE)]))
    for c in range(SIZE):
        units.append((f"{c + 1}열", [(r, c) for r in range(SIZE)]))
    for b in range(SIZE):
        br, bc = (b // BOX) * BOX, (b % BOX) * BOX
        units.append((f"{b + 1}번 박스", [(br + i, bc + j) for i in range(BOX) for j in range(BOX)]))
    return units


UNITS = _units()
PEERS: dict[Cell, set[Cell]] = {
    (r, c): {cell for _, cells in UNITS if (r, c) in cells for cell in cells} - {(r, c)}
    for r in range(SIZE) for c in range(SIZE)
}


def cell_name(r: int, c: int) -> str:
    return f"R{r + 1}C{c + 1}"


@dataclass
class Step:
    technique: str
    cells: list[Cell]
    value: int | None                 # 칸을 채운 단계면 값, 후보 제거 단계면 None
    eliminated: list[tuple[int, int, int]] = field(default_factory=list)
    reason: str = ""

    def describe(self) -> str:
        if self.value is not None:
            r, c = self.cells[0]
            return f"{cell_name(r, c)} = {self.value}  [{self.technique}]  {self.reason}"
        elim = ", ".join(f"{cell_name(r, c)}에서 {v}" for r, c, v in self.eliminated)
        return f"후보 제거  [{self.technique}]  {self.reason} → {elim}"


@dataclass
class LogicResult:
    grid: Grid
    steps: list[Step]
    solved: bool
    stuck: bool          # 기본 기법으로 막혔는지
    contradiction: bool  # 후보 0개인 칸 발생(해 없음)

    @property
    def empty_cells(self) -> int:
        return sum(1 for row in self.grid for v in row if not v)

    def technique_counts(self) -> dict[str, int]:
        counts = {t: 0 for t in TECHNIQUES}
        for s in self.steps:
            counts[s.technique] += 1
        return counts

    def hardest(self) -> str | None:
        used = [t for t, n in self.technique_counts().items() if n]
        return used[-1] if used else None

    def level(self) -> str:
        if not self.solved:
            return EXPERT
        return LEVELS[self.hardest()]


class _Board:
    def __init__(self, grid: Grid):
        self.grid = [row[:] for row in grid]
        self.cands: dict[Cell, set[int]] = {}
        for r in range(SIZE):
            for c in range(SIZE):
                if not self.grid[r][c]:
                    used = {self.grid[pr][pc] for pr, pc in PEERS[(r, c)]}
                    self.cands[(r, c)] = set(range(1, 10)) - used

    def place(self, r: int, c: int, v: int) -> None:
        self.grid[r][c] = v
        del self.cands[(r, c)]
        for p in PEERS[(r, c)]:
            if p in self.cands:
                self.cands[p].discard(v)


def _naked_single(b: _Board) -> Step | None:
    for (r, c), cs in sorted(b.cands.items()):
        if len(cs) == 1:
            v = next(iter(cs))
            b.place(r, c, v)
            return Step(NAKED_SINGLE, [(r, c)], v, reason=f"이 칸에 남은 후보가 {v} 하나뿐")
    return None


def _hidden_single(b: _Board) -> Step | None:
    for name, cells in UNITS:
        for v in range(1, 10):
            spots = [cell for cell in cells if cell in b.cands and v in b.cands[cell]]
            if len(spots) == 1:
                r, c = spots[0]
                b.place(r, c, v)
                return Step(HIDDEN_SINGLE, [(r, c)], v,
                            reason=f"{name}에서 {v}가 들어갈 수 있는 칸은 여기뿐")
    return None


def _naked_pair(b: _Board) -> Step | None:
    for name, cells in UNITS:
        open_cells = [cell for cell in cells if cell in b.cands]
        pairs = [cell for cell in open_cells if len(b.cands[cell]) == 2]
        for i, a in enumerate(pairs):
            for bb in pairs[i + 1:]:
                if b.cands[a] != b.cands[bb]:
                    continue
                pair = b.cands[a]
                elim = [(r, c, v) for (r, c) in open_cells if (r, c) not in (a, bb)
                        for v in sorted(pair & b.cands[(r, c)])]
                if not elim:
                    continue
                for r, c, v in elim:
                    b.cands[(r, c)].discard(v)
                x, y = sorted(pair)
                return Step(NAKED_PAIR, [a, bb], None, elim,
                            reason=f"{name}의 {cell_name(*a)}, {cell_name(*bb)} 후보가 {{{x},{y}}} 뿐")
    return None


STRATEGIES = [_naked_single, _hidden_single, _naked_pair]


def logic_solve(grid: Grid, max_steps: int = 10_000) -> LogicResult:
    """기본 기법만으로 최대한 풀고, 단계 기록과 함께 결과를 반환한다."""
    if not is_valid(grid):
        return LogicResult([row[:] for row in grid], [], False, False, True)
    b = _Board(grid)
    steps: list[Step] = []
    while b.cands and len(steps) < max_steps:
        if any(not cs for cs in b.cands.values()):
            return LogicResult(b.grid, steps, False, False, True)
        for strat in STRATEGIES:
            step = strat(b)
            if step:
                steps.append(step)
                break
        else:
            return LogicResult(b.grid, steps, False, True, False)
    solved = not b.cands and is_valid(b.grid)
    return LogicResult(b.grid, steps, solved, not solved, False)


def rate(grid: Grid) -> LogicResult:
    """난이도 평가용 별칭. result.level() 로 등급을 얻는다."""
    return logic_solve(grid)
