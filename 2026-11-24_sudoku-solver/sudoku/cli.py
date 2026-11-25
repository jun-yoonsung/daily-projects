"""스도쿠 솔버 명령줄 인터페이스.

사용 예:
    python -m sudoku solve "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    python -m sudoku solve -f puzzles/easy.txt
    python -m sudoku check "<81자리>"        # 유일해 여부 검사
    python -m sudoku hint "<81자리>" 0 2    # (행, 열) 후보 숫자 보기 (0부터 시작)
    python -m sudoku generate --seed 42 --clues 30   # 유일해 퍼즐 생성
    python -m sudoku rate "<81자리>"        # 기법 기반 난이도 평가
    python -m sudoku explain "<81자리>"     # 단계별 풀이 설명
"""

from __future__ import annotations

import argparse
import sys
import time

from .board import parse, pretty, to_string
from .generator import generate
from .logic import logic_solve
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


def cmd_generate(args: argparse.Namespace) -> int:
    g = generate(seed=args.seed, clues=args.clues)
    level = logic_solve(g.puzzle).level()
    if args.oneline:
        print(to_string(g.puzzle))
        return 0
    seed = "무작위" if args.seed is None else str(args.seed)
    print(f"생성 완료 (시드 {seed}, 단서 {g.clues}개, 난이도: {level})")
    if g.clues > args.clues:
        print(f"  ※ 유일해를 유지하려고 목표({args.clues}개)보다 {g.clues - args.clues}개 더 남겼습니다.")
    print(pretty(g.puzzle))
    print(to_string(g.puzzle))
    return 0


def cmd_rate(args: argparse.Namespace) -> int:
    grid = parse(_read_puzzles(args)[0])
    res = logic_solve(grid)
    if res.contradiction:
        print("해가 없는 퍼즐입니다(규칙 위반 또는 후보가 없는 칸).")
        return 1
    print(f"난이도: {res.level()}")
    print("사용 기법:")
    used = {t: n for t, n in res.technique_counts().items() if n}
    for tech, n in used.items():
        print(f"  {tech:<14} {n}회")
    if not used:
        print("  (없음 — 첫 단계부터 기본 기법이 통하지 않음)")
    if res.stuck:
        print(f"  (기본 기법으로 막힘 — 남은 빈칸 {res.empty_cells}개, 백트래킹 필요)")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    grid = parse(_read_puzzles(args)[0])
    res = logic_solve(grid)
    if res.contradiction and not res.steps:
        print("해가 없는 퍼즐입니다(규칙 위반 또는 후보가 없는 칸).")
        return 1
    shown = res.steps if args.limit is None else res.steps[:args.limit]
    width = len(str(len(res.steps))) or 1
    for i, step in enumerate(shown, 1):
        print(f"{i:>{width}}. {step.describe()}")
    if len(shown) < len(res.steps):
        print(f"… (총 {len(res.steps)}단계 중 {len(shown)}단계 표시)")
    if res.solved:
        print(f"완료: {len(res.steps)}단계로 풀었습니다 (난이도: {res.level()}).")
        return 0
    if res.contradiction:
        print("모순 발생: 후보가 없는 칸이 생겼습니다. 퍼즐에 해가 없습니다.")
        return 1
    print(f"기본 기법으로 더 진행할 수 없음 — 남은 빈칸 {res.empty_cells}개. `solve` 로 정답을 확인하세요.")
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

    g = sub.add_parser("generate", help="유일해 퍼즐 생성")
    g.add_argument("--seed", type=int, default=None, help="난수 시드 (같으면 같은 퍼즐)")
    g.add_argument("--clues", type=int, default=30, help="남길 단서 수 목표 (17~81, 기본 30)")
    g.add_argument("--oneline", action="store_true", help="퍼즐을 81자리 한 줄로만 출력")
    g.set_defaults(func=cmd_generate)

    rt = sub.add_parser("rate", help="기법 기반 난이도 평가")
    rt.add_argument("puzzle", nargs="?")
    rt.add_argument("-f", "--file")
    rt.set_defaults(func=cmd_rate)

    e = sub.add_parser("explain", help="단계별 풀이 설명")
    e.add_argument("puzzle", nargs="?")
    e.add_argument("-f", "--file")
    e.add_argument("--limit", type=int, default=None, help="처음 N단계만 출력")
    e.set_defaults(func=cmd_explain)
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
