"""명령줄 인터페이스: table / strength / simulate / predict / backtest."""

from __future__ import annotations

import argparse
import sys
import time
import unicodedata
from pathlib import Path

from .data import DataError, load_league
from .model import estimate_strength
from .report import render_html
from .predict import backtest, predict_match
from .sim import apply_fixes, simulate
from .table import compute_table

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data"


def _width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _ljust(s: str, w: int) -> str:
    return s + " " * max(0, w - _width(s))


def _rjust(s: str, w: int) -> str:
    return " " * max(0, w - _width(s)) + s


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
    strength = estimate_strength(league)  # 전력은 실제로 치른 경기만으로 추정
    if args.fix:
        league, fixed = apply_fixes(league, args.fix)
        desc = ", ".join(
            f"{league.name_of(m.home)} {m.home_goals}-{m.away_goals} {league.name_of(m.away)}" for m in fixed
        )
        print(f"고정한 경기 {len(fixed)}개: {desc}")
    t0 = time.perf_counter()
    res = simulate(league, n=args.n, seed=args.seed, strength=strength)
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


def _team_id(league, raw: str) -> str:
    ids = {t.upper(): t for t in league.team_ids}
    if raw.upper() in ids:
        return ids[raw.upper()]
    for t in league.teams:
        if t.name == raw:
            return t.id
    raise DataError(f"알 수 없는 팀 '{raw}' (사용 가능한 ID: {', '.join(league.team_ids)})")


def cmd_predict(league, args) -> int:
    home, away = _team_id(league, args.home), _team_id(league, args.away)
    pred = predict_match(estimate_strength(league), home, away, top=5)
    print(f"{league.name_of(home)} (홈) vs {league.name_of(away)} (원정)")
    print(f"기대 득점      : {pred.lam:.2f} - {pred.mu:.2f}")
    print(f"홈 승 / 무 / 원정 승 : {pred.p_home * 100:.1f}% / {pred.p_draw * 100:.1f}% / {pred.p_away * 100:.1f}%")
    print("가장 가능성 높은 스코어")
    for hg, ag, p in pred.top_scores:
        print(f"  {hg}-{ag}  {p * 100:>5.1f}%")
    return 0


def cmd_backtest(league, args) -> int:
    r = backtest(league, args.train_rounds)
    print(f"1~{r.train_rounds}라운드 경기 {r.n_train}개로 학습, 이후 치른 경기 {r.n_test}개 평가")
    rows = [("포아송 모델", r.model), ("학습 구간 빈도", r.freq), ("균등 1/3", r.uniform)]
    nw = max(_width(n) for n, _ in rows) + 2
    print(f"{_ljust('모델', nw)}{_rjust('로그손실', 10)}{_rjust('Brier', 8)}{_rjust('적중률', 9)}")
    for name, sc in rows:
        acc = "-" if sc is r.uniform else f"{sc.accuracy * 100:.1f}%"
        print(f"{_ljust(name, nw)}{sc.log_loss:>10.3f}{sc.brier:>8.3f}{acc:>9}")
    print("(로그손실·Brier 는 낮을수록 좋음, 적중률은 가장 확률 높은 결과가 맞은 비율, 균등 모델은 적중률 없음)")
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
    s.add_argument("--fix", action="append", default=[], metavar='"H-A=2-1"',
                   help="잔여 경기 결과 고정 (여러 번 지정 가능)")
    pr = sub.add_parser("predict", help="단일 경기 승/무/패 확률과 스코어 예측")
    pr.add_argument("home", help="홈팀 ID 또는 이름")
    pr.add_argument("away", help="원정팀 ID 또는 이름")
    b = sub.add_parser("backtest", help="앞 N라운드로 학습해 이후 경기 예측 정확도 확인")
    b.add_argument("--train-rounds", type=int, default=10, help="학습에 쓸 라운드 수 (기본 10)")
    # --data 를 서브커맨드 뒤에 써도 되도록
    for sp in sub.choices.values():
        sp.add_argument("--data", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        league = load_league(args.data)
        handler = {"table": cmd_table, "strength": cmd_strength, "simulate": cmd_simulate,
                   "predict": cmd_predict, "backtest": cmd_backtest}[args.cmd]
        return handler(league, args)
    except DataError as e:
        print(f"데이터 오류: {e}", file=sys.stderr)
        return 1
