"""스도쿠 솔버 명령줄 인터페이스.

사용 예:
    python -m sudoku solve "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    python -m sudoku solve -f puzzles/easy.txt
    python -m sudoku check "<81자리>"        # 유일해 여부 검사
    python -m sudoku hint "<81자리>" 0 2    # (행, 열) 후보 숫자 보기 (0부터 시작)
"""

from __future__ import annotations

import argparse
import sys
import time

from .board import parse, pretty, to_string
from .solver import candidates, solve_all


def _read_puzzles(args: argparse.Namespace) -> list[str]:
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        # 한 줄에 81자리 형식이면 줄마다 퍼즐, 아니면 파일 전체를 하나의 퍼즐로 본다
        if all(len(ln) >= 81 for ln in lines):
            return lines
        return ["\n".join(lines)]
    if args.puzzle:
        return [args.puzzle]
    return [sys.stdin.read()]


def cmd_solve(args: argparse.Namespace) -> int:
    rc = 0
    for i, text in enumerate(_read_puzzles(args), 1):
        try:
            grid = parse(text)
        except ValueError as e:
            print(f"[{i}] 입력 오류: {e}", file=sys.stderr)
            rc = 2
            continue
        t0 = time.perf_counter()
        sols, stats = solve_all(grid, limit=1)
        ms = (time.perf_counter() - t0) * 1000
        if not sols:
            print(f"[{i}] 해가 없습니다.")
            rc = 1
            continue
        if args.oneline:
            print(to_string(sols[0]))
        else:
            print(f"[{i}] 풀이 완료 ({ms:.1f} ms, 노드 {stats.nodes}, 백트래킹 {stats.backtracks})")
            print(pretty(sols[0]))
            print()
    return rc


def cmd_check(args: argparse.Namespace) -> int:
    grid = parse(_read_puzzles(args)[0])
    sols, _ = solve_all(grid, limit=2)
    if not sols:
        print("해 없음")
        return 1
    if len(sols) == 1:
        print("유일해 있음 ✔")
        return 0
    print("해가 2개 이상입니다 (올바른 스도쿠 아님)")
    return 1


def cmd_hint(args: argparse.Namespace) -> int:
    grid = parse(args.puzzle)
    if not (0 <= args.row < 9 and 0 <= args.col < 9):
        print("행/열은 0~8 사이여야 합니다.", file=sys.stderr)
        return 2
    if grid[args.row][args.col]:
        print(f"({args.row}, {args.col}) 칸은 이미 {grid[args.row][args.col]} 입니다.")
        return 0
    cands = candidates(grid, args.row, args.col)
    print(f"({args.row}, {args.col}) 후보: {', '.join(map(str, cands)) or '없음'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sudoku", description="스도쿠 솔버 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("solve", help="퍼즐 풀기")
    s.add_argument("puzzle", nargs="?", help="81자리 퍼즐 문자열 (빈칸은 0 또는 .)")
    s.add_argument("-f", "--file", help="퍼즐 파일 (한 줄에 하나씩 또는 9x9 격자)")
    s.add_argument("--oneline", action="store_true", help="결과를 81자리 한 줄로 출력")
    s.set_defaults(func=cmd_solve)

    c = sub.add_parser("check", help="유일해 여부 검사")
    c.add_argument("puzzle", nargs="?")
    c.add_argument("-f", "--file")
    c.set_defaults(func=cmd_check)

    h = sub.add_parser("hint", help="특정 칸의 후보 숫자 보기")
    h.add_argument("puzzle")
    h.add_argument("row", type=int)
    h.add_argument("col", type=int)
    h.set_defaults(func=cmd_hint)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ValueError as e:
        print(f"입력 오류: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
