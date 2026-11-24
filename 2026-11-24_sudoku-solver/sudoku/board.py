"""스도쿠 보드 파싱/출력/검증 유틸리티."""

from __future__ import annotations

Grid = list[list[int]]

SIZE = 9
BOX = 3


def parse(text: str) -> Grid:
    """81자리 문자열(또는 여러 줄)을 9x9 격자로 변환한다.

    숫자 1-9는 값, '0' '.' '_' 는 빈칸으로 처리한다. 공백/줄바꿈/구분자(| - +)는 무시한다.
    """
    cells: list[int] = []
    for ch in text:
        if ch in "123456789":
            cells.append(int(ch))
        elif ch in "0._":
            cells.append(0)
        # 그 외 문자는 무시
    if len(cells) != SIZE * SIZE:
        raise ValueError(f"칸 수가 81개가 아닙니다: {len(cells)}개")
    return [cells[r * SIZE:(r + 1) * SIZE] for r in range(SIZE)]


def to_string(grid: Grid) -> str:
    """격자를 한 줄 81자리 문자열로 변환한다(빈칸은 '.')."""
    return "".join(str(v) if v else "." for row in grid for v in row)


def pretty(grid: Grid) -> str:
    """사람이 보기 좋은 형태로 격자를 출력용 문자열로 만든다."""
    lines = []
    for r, row in enumerate(grid):
        if r and r % BOX == 0:
            lines.append("------+-------+------")
        parts = []
        for c, v in enumerate(row):
            if c and c % BOX == 0:
                parts.append("|")
            parts.append(str(v) if v else ".")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def box_index(r: int, c: int) -> int:
    return (r // BOX) * BOX + c // BOX


def is_valid(grid: Grid) -> bool:
    """현재 채워진 숫자들이 규칙(행/열/박스 중복 없음)을 위반하지 않는지 확인한다."""
    rows = [set() for _ in range(SIZE)]
    cols = [set() for _ in range(SIZE)]
    boxes = [set() for _ in range(SIZE)]
    for r in range(SIZE):
        for c in range(SIZE):
            v = grid[r][c]
            if not v:
                continue
            if not 1 <= v <= 9:
                return False
            b = box_index(r, c)
            if v in rows[r] or v in cols[c] or v in boxes[b]:
                return False
            rows[r].add(v)
            cols[c].add(v)
            boxes[b].add(v)
    return True


def is_solved(grid: Grid) -> bool:
    return all(v for row in grid for v in row) and is_valid(grid)
