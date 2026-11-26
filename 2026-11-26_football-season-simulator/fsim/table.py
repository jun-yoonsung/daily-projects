"""치른 경기로 순위표 계산."""

from __future__ import annotations

from dataclasses import dataclass

from .data import League

WIN, DRAW = 3, 1


@dataclass
class Standing:
    team: str
    name: str
    played: int = 0
    win: int = 0
    draw: int = 0
    loss: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def gd(self) -> int:
        return self.gf - self.ga

    @property
    def points(self) -> int:
        return self.win * WIN + self.draw * DRAW


def sort_key(s: Standing):
    """승점 → 득실차 → 다득점 (내림차순) → 팀 이름 (오름차순)."""
    return (-s.points, -s.gd, -s.gf, s.name)


def compute_table(league: League) -> list[Standing]:
    rows = {t.id: Standing(t.id, t.name) for t in league.teams}
    for m in league.played:
        h, a = rows[m.home], rows[m.away]
        h.played += 1
        a.played += 1
        h.gf += m.home_goals
        h.ga += m.away_goals
        a.gf += m.away_goals
        a.ga += m.home_goals
        if m.home_goals > m.away_goals:
            h.win += 1
            a.loss += 1
        elif m.home_goals < m.away_goals:
            a.win += 1
            h.loss += 1
        else:
            h.draw += 1
            a.draw += 1
    return sorted(rows.values(), key=sort_key)
