"""잔여 경기 몬테카를로 시뮬레이션."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .data import League
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
