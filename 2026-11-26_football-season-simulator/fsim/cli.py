"""명령줄 인터페이스: table / strength / simulate."""

from __future__ import annotations

import argparse
import sys
import time
import unicodedata
from pathlib import Path

from .data import DataError, load_league
from .model import estimate_strength
from .report import render_html
from .sim import simulate
from .table import compute_table

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data"


def _width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _ljust(s: str, w: int) -> str:
    return s + " " * max(0, w - _width(s))


def cmd_table(league, args) -> int:
    rows = compute_table(league)
    nw = max(_width(r.name) for r in rows) + 2
    print(f"{'#':>2}  {_ljust('팀', nw)}{'경기':>4}{'승':>4}{'무':>4}{'패':>4}{'득':>4}{'실':>4}{'득실':>6}{'승점':>6}")
    for i, r in enumerate(rows, start=1):
        print(f"{i:>2}  {_ljust(r.name, nw)}{r.played:>6}{r.win:>5}{r.draw:>5}{r.loss:>5}"
              f"{r.gf:>5}{r.ga:>5}{r.gd:>+7}{r.points:>7}")
    return 0


def cmd_strength(league, args) -> int:
    st = estimate_strength(league)
    print(f"리그 평균 득점(원정 기준) : {st.base:.2f}   홈 어드밴티지 : x{st.home_adv:.2f}")
    ids = sorted(league.team_ids, key=lambda t: -(st.attack[t] / st.defense[t]))
    nw = max(_width(league.name_of(t)) for t in ids) + 2
    print(f" {_ljust('팀', nw)}{'공격력':>6}{'수비력':>8}   (공격 >1 강함, 수비 <1 강함)")
    for t in ids:
        print(f" {_ljust(league.name_of(t), nw)}{st.attack[t]:>9.2f}{st.defense[t]:>11.2f}")
    return 0


def cmd_simulate(league, args) -> int:
    if args.n <= 0:
        raise DataError("--n 은 1 이상이어야 합니다")
    t0 = time.perf_counter()
    res = simulate(league, n=args.n, seed=args.seed)
    elapsed = time.perf_counter() - t0
    print(f"남은 경기 {len(league.remaining)}개를 {res.n}회 시뮬레이션 (seed={args.seed}, {elapsed:.1f}초)")
    ids = res.ranked_ids()
    nw = max(_width(league.name_of(t)) for t in ids) + 2
    print(f"{'#':>2}  {_ljust('팀', nw)}{'현재승점':>8}{'예상승점':>8}{'우승':>8}{'상위' + str(res.top_n):>8}{'강등':>8}")
    for i, t in enumerate(ids, start=1):
        print(f"{i:>2}  {_ljust(league.name_of(t), nw)}{res.current_points[t]:>12}{res.mean_points[t]:>12.1f}"
              f"{res.title_prob[t] * 100:>9.1f}%{res.top4_prob[t] * 100:>8.1f}%{res.releg_prob[t] * 100:>8.1f}%")
    if args.html:
        out = Path(args.html)
        out.write_text(render_html(league, res), encoding="utf-8")
        print(f"HTML 리포트 저장: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fsim", description="축구 리그 시즌 시뮬레이터 (가상 데이터)")
    p.add_argument("--data", default=str(DEFAULT_DATA), help="teams.csv / matches.csv 가 있는 폴더")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("table", help="현재 순위표")
    sub.add_parser("strength", help="팀 전력(공격력·수비력) 추정")
    s = sub.add_parser("simulate", help="잔여 경기 몬테카를로 시뮬레이션")
    s.add_argument("--n", type=int, default=10000, help="반복 횟수 (기본 10000)")
    s.add_argument("--seed", type=int, default=None, help="난수 시드 (같으면 같은 결과)")
    s.add_argument("--html", default=None, help="HTML 리포트 저장 경로")
    # --data 를 서브커맨드 뒤에 써도 되도록
    for sp in sub.choices.values():
        sp.add_argument("--data", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        league = load_league(args.data)
        handler = {"table": cmd_table, "strength": cmd_strength, "simulate": cmd_simulate}[args.cmd]
        return handler(league, args)
    except DataError as e:
        print(f"데이터 오류: {e}", file=sys.stderr)
        return 1
