"""팀 전력(공격력·수비력)과 홈 어드밴티지 추정.

기대 득점 모델
    홈 λ   = base × home_adv × attack[홈] × defense[원정]
    원정 μ = base × attack[원정] × defense[홈]

- base      : 치른 경기의 원정팀 평균 득점
- home_adv  : 홈팀 평균 득점 / 원정팀 평균 득점
- attack    : (팀 경기당 득점 / 리그 경기당 팀 평균 득점), 1.0 쪽으로 축소 보정 후 평균 1 로 정규화
- defense   : (팀 경기당 실점 / 리그 경기당 팀 평균 득점), 같은 방식 (작을수록 수비가 강함)
"""

from __future__ import annotations

from dataclasses import dataclass

from .data import League

DEFAULT_BASE = 1.3
PRIOR_GAMES = 5.0  # 경기 수가 이만큼일 때 관측값과 사전값(1.0)을 반반 섞음


@dataclass
class Strength:
    attack: dict[str, float]
    defense: dict[str, float]
    home_adv: float
    base: float

    def expected_goals(self, home: str, away: str) -> tuple[float, float]:
        lam = self.base * self.home_adv * self.attack[home] * self.defense[away]
        mu = self.base * self.attack[away] * self.defense[home]
        return lam, mu


def _normalize(values: dict[str, float]) -> dict[str, float]:
    mean = sum(values.values()) / len(values)
    if mean <= 0:
        return {k: 1.0 for k in values}
    return {k: v / mean for k, v in values.items()}


def estimate_strength(league: League, prior_games: float = PRIOR_GAMES) -> Strength:
    played = league.played
    ids = league.team_ids
    if not played:
        ones = {t: 1.0 for t in ids}
        return Strength(dict(ones), dict(ones), 1.0, DEFAULT_BASE)

    n = len(played)
    home_total = sum(m.home_goals for m in played)
    away_total = sum(m.away_goals for m in played)
    base = away_total / n if away_total > 0 else DEFAULT_BASE
    home_adv = (home_total / away_total) if away_total > 0 and home_total > 0 else 1.0
    per_team_avg = (home_total + away_total) / (2 * n)

    gf = {t: 0 for t in ids}
    ga = {t: 0 for t in ids}
    games = {t: 0 for t in ids}
    for m in played:
        gf[m.home] += m.home_goals
        ga[m.home] += m.away_goals
        gf[m.away] += m.away_goals
        ga[m.away] += m.home_goals
        games[m.home] += 1
        games[m.away] += 1

    attack: dict[str, float] = {}
    defense: dict[str, float] = {}
    for t in ids:
        g = games[t]
        if g == 0 or per_team_avg == 0:
            attack[t] = defense[t] = 1.0
            continue
        w = g / (g + prior_games)
        raw_att = gf[t] / (g * per_team_avg)
        raw_def = ga[t] / (g * per_team_avg)
        # 0 득점/실점 팀도 확률이 0이 되지 않도록 축소 보정이 하한 역할을 한다.
        attack[t] = w * raw_att + (1 - w) * 1.0
        defense[t] = w * raw_def + (1 - w) * 1.0

    return Strength(_normalize(attack), _normalize(defense), home_adv, base)
