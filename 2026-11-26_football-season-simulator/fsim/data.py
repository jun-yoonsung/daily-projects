"""teams.csv / matches.csv 로드와 검증."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


class DataError(Exception):
    """입력 데이터가 잘못되었을 때 발생."""


@dataclass(frozen=True)
class Team:
    id: str
    name: str


@dataclass(frozen=True)
class Match:
    round: int
    home: str
    away: str
    home_goals: int | None = None
    away_goals: int | None = None

    @property
    def played(self) -> bool:
        return self.home_goals is not None


@dataclass
class League:
    teams: list[Team]
    matches: list[Match] = field(default_factory=list)

    @property
    def team_ids(self) -> list[str]:
        return [t.id for t in self.teams]

    def name_of(self, team_id: str) -> str:
        for t in self.teams:
            if t.id == team_id:
                return t.name
        raise KeyError(team_id)

    @property
    def played(self) -> list[Match]:
        return [m for m in self.matches if m.played]

    @property
    def remaining(self) -> list[Match]:
        return [m for m in self.matches if not m.played]


def _parse_goal(raw: str, where: str) -> int | None:
    raw = (raw or "").strip()
    if raw == "":
        return None
    if not raw.isdigit():
        raise DataError(f"{where}: 점수는 0 이상의 정수여야 합니다 ({raw!r})")
    return int(raw)


def load_teams(path: Path) -> list[Team]:
    if not path.exists():
        raise DataError(f"파일이 없습니다: {path}")
    teams: list[Team] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not {"id", "name"} <= set(reader.fieldnames):
            raise DataError(f"{path.name}: 헤더는 id,name 이어야 합니다")
        for lineno, row in enumerate(reader, start=2):
            tid = (row.get("id") or "").strip()
            name = (row.get("name") or "").strip()
            if not tid or not name:
                raise DataError(f"{path.name} {lineno}번째 줄: id 와 name 이 필요합니다")
            if tid in seen:
                raise DataError(f"{path.name} {lineno}번째 줄: 중복 팀 ID '{tid}'")
            seen.add(tid)
            teams.append(Team(tid, name))
    if len(teams) < 2:
        raise DataError(f"{path.name}: 팀이 2개 이상 필요합니다")
    return teams


def load_matches(path: Path, team_ids: set[str]) -> list[Match]:
    if not path.exists():
        raise DataError(f"파일이 없습니다: {path}")
    required = {"round", "home", "away", "home_goals", "away_goals"}
    matches: list[Match] = []
    pairs: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not required <= set(reader.fieldnames):
            raise DataError(f"{path.name}: 헤더는 round,home,away,home_goals,away_goals 이어야 합니다")
        for lineno, row in enumerate(reader, start=2):
            where = f"{path.name} {lineno}번째 줄"
            rnd_raw = (row.get("round") or "").strip()
            if not rnd_raw.isdigit():
                raise DataError(f"{where}: 라운드는 정수여야 합니다 ({rnd_raw!r})")
            home = (row.get("home") or "").strip()
            away = (row.get("away") or "").strip()
            for tid in (home, away):
                if tid not in team_ids:
                    raise DataError(f"{where}: 알 수 없는 팀 ID '{tid}'")
            if home == away:
                raise DataError(f"{where}: 홈팀과 원정팀이 같습니다 ('{home}')")
            hg = _parse_goal(row.get("home_goals", ""), where)
            ag = _parse_goal(row.get("away_goals", ""), where)
            if (hg is None) != (ag is None):
                raise DataError(f"{where}: 홈/원정 점수는 둘 다 입력하거나 둘 다 비워야 합니다")
            if (home, away) in pairs:
                raise DataError(f"{where}: 중복 경기 {home} vs {away}")
            pairs.add((home, away))
            matches.append(Match(int(rnd_raw), home, away, hg, ag))
    return matches


def load_league(data_dir: str | Path) -> League:
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise DataError(f"데이터 폴더가 없습니다: {data_dir}")
    teams = load_teams(data_dir / "teams.csv")
    matches = load_matches(data_dir / "matches.csv", {t.id for t in teams})
    return League(teams, matches)
