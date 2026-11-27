"""잔여 경기 몬테카를로 시뮬레이션."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace

from .data import DataError, League, Match
from .model import Strength, estimate_strength
from .table import DRAW, WIN, compute_table


def poisson(rng: random.Random, lam: float, exp_neg: float | None = None) -> int:
    """Knuth 방식 포아송 샘플러 (축구 득점처럼 λ 가 작을 때 충분히 빠름)."""
    limit = math.exp(-lam) if exp_neg is None else exp_neg
    k = 0
    p = rng.random()
    while p > limit:
        k += 1
        p *= rng.random()
    return k


@dataclass
class SimResult:
    n: int
    seed: int | None
    team_ids: list[str]
    current_points: dict[str, int]
    remaining_games: dict[str, int]
    title_prob: dict[str, float]
    top4_prob: dict[str, float]
    releg_prob: dict[str, float]
    mean_points: dict[str, float]
    pos_dist: dict[str, list[float]]  # pos_dist[team][순위-1]
    top_n: int
    releg_n: int

    def ranked_ids(self) -> list[str]:
        """예상 승점 → 우승 확률 순으로 정렬한 팀 ID."""
        return sorted(
            self.team_ids,
            key=lambda t: (-self.mean_points[t], -self.title_prob[t], t),
        )


def simulate(
    league: League,
    n: int = 10000,
    seed: int | None = None,
    strength: Strength | None = None,
    top_n: int = 4,
    releg_n: int = 2,
) -> SimResult:
    if n <= 0:
        raise ValueError("반복 횟수 n 은 1 이상이어야 합니다")
    rng = random.Random(seed)
    strength = strength or estimate_strength(league)
    ids = league.team_ids
    k = len(ids)
    top_n = min(top_n, k)
    releg_n = min(releg_n, max(k - 1, 0))
    idx = {t: i for i, t in enumerate(ids)}

    table = {s.team: s for s in compute_table(league)}
    base_pts = [table[t].points for t in ids]
    base_gd = [table[t].gd for t in ids]
    base_gf = [table[t].gf for t in ids]

    fixtures = []
    remaining_games = {t: 0 for t in ids}
    for m in league.remaining:
        lam, mu = strength.expected_goals(m.home, m.away)
        fixtures.append((idx[m.home], idx[m.away], math.exp(-lam), math.exp(-mu)))
        remaining_games[m.home] += 1
        remaining_games[m.away] += 1

    pos_counts = [[0] * k for _ in range(k)]
    pts_sum = [0] * k
    order = list(range(k))

    for _ in range(n):
        pts = base_pts[:]
        gd = base_gd[:]
        gf = base_gf[:]
        for h, a, eh, ea in fixtures:
            hg = poisson(rng, 0.0, eh)
            ag = poisson(rng, 0.0, ea)
            gf[h] += hg
            gf[a] += ag
            gd[h] += hg - ag
            gd[a] += ag - hg
            if hg > ag:
                pts[h] += WIN
            elif hg < ag:
                pts[a] += WIN
            else:
                pts[h] += DRAW
                pts[a] += DRAW
        # 승점·득실차·다득점까지 같으면 무작위로 순위를 정한다.
        tie = [rng.random() for _ in range(k)]
        order.sort(key=lambda i: (-pts[i], -gd[i], -gf[i], tie[i]))
        for pos, i in enumerate(order):
            pos_counts[i][pos] += 1
        for i in range(k):
            pts_sum[i] += pts[i]

    pos_dist = {t: [c / n for c in pos_counts[idx[t]]] for t in ids}
    return SimResult(
        n=n,
        seed=seed,
        team_ids=ids,
        current_points={t: table[t].points for t in ids},
        remaining_games=remaining_games,
        title_prob={t: pos_dist[t][0] for t in ids},
        top4_prob={t: sum(pos_dist[t][:top_n]) for t in ids},
        releg_prob={t: sum(pos_dist[t][k - releg_n:]) if releg_n else 0.0 for t in ids},
        mean_points={t: pts_sum[idx[t]] / n for t in ids},
        pos_dist=pos_dist,
        top_n=top_n,
        releg_n=releg_n,
    )


# ---------------------------------------------------------------- What-if

_FIX_HELP = '형식은 "홈ID-원정ID=홈득점-원정득점" 입니다 (예: "HAN-BUS=2-1")'


def parse_fix(spec: str) -> tuple[str, str, int, int]:
    """'HAN-BUS=2-1' → ('HAN', 'BUS', 2, 1)."""
    raw = spec.strip()
    if raw.count("=") != 1:
        raise DataError(f"--fix '{spec}': {_FIX_HELP}")
    left, right = raw.split("=")
    teams = left.strip().split("-")
    goals = right.strip().split("-")
    if len(teams) != 2 or len(goals) != 2 or not all(t.strip() for t in teams):
        raise DataError(f"--fix '{spec}': {_FIX_HELP}")
    if not all(g.strip().isdigit() for g in goals):
        raise DataError(f"--fix '{spec}': 점수는 0 이상의 정수여야 합니다. {_FIX_HELP}")
    return teams[0].strip(), teams[1].strip(), int(goals[0]), int(goals[1])


def apply_fixes(league: League, specs: list[str]) -> tuple[League, list[Match]]:
    """잔여 경기 중 지정한 경기의 결과를 채운 새 League 와 고정된 경기 목록을 돌려준다."""
    fixes: dict[tuple[str, str], tuple[int, int]] = {}
    for spec in specs:
        home, away, hg, ag = parse_fix(spec)
        key = (home, away)
        if key in fixes:
            raise DataError(f"--fix '{spec}': 같은 경기를 두 번 고정했습니다")
        match = next((m for m in league.matches if (m.home, m.away) == key), None)
        if match is None:
            raise DataError(f"--fix '{home}-{away}': 일정에 없는 경기입니다 (홈-원정 순서를 확인하세요)")
        if match.played:
            raise DataError(f"--fix '{home}-{away}': 이미 치른 경기입니다")
        fixes[key] = (hg, ag)

    fixed: list[Match] = []
    new_matches: list[Match] = []
    for m in league.matches:
        if (m.home, m.away) in fixes:
            hg, ag = fixes[(m.home, m.away)]
            m = replace(m, home_goals=hg, away_goals=ag)
            fixed.append(m)
        new_matches.append(m)
    return League(league.teams, new_matches), fixed
