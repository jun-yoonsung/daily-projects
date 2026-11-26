"""가상 리그 데이터 생성기 (모든 팀·결과는 가상)."""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path

from .sim import poisson

# (id, 이름, 숨은 공격력, 숨은 수비력) — 실제 구단과 무관한 가상 팀
TEAMS = [
    ("HAN", "한강 FC", 1.40, 0.70),
    ("BUS", "부산 갈매기", 1.25, 0.80),
    ("DAE", "대전 사이언스", 1.10, 0.90),
    ("ULS", "울산 고래", 1.15, 0.95),
    ("GWJ", "광주 빛고을", 1.00, 0.95),
    ("ICN", "인천 등대", 1.00, 1.00),
    ("POH", "포항 제철", 0.95, 1.00),
    ("JEJ", "제주 감귤", 0.95, 1.05),
    ("SUW", "수원 성곽", 0.90, 1.10),
    ("JNJ", "전주 한옥", 0.90, 1.15),
    ("CHC", "춘천 호수", 0.80, 1.20),
    ("YSU", "여수 밤바다", 0.75, 1.30),
]
BASE = 1.15
HOME_ADV = 1.20


def round_robin(team_ids: list[str]) -> list[list[tuple[str, str]]]:
    """원형(circle) 방식 더블 라운드로빈. 반환: 라운드별 (홈, 원정) 목록."""
    ids = list(team_ids)
    if len(ids) % 2:
        ids.append(None)  # 부전승 자리
    n = len(ids)
    first_half: list[list[tuple[str, str]]] = []
    arr = ids[:]
    for r in range(n - 1):
        pairs = []
        for i in range(n // 2):
            a, b = arr[i], arr[n - 1 - i]
            if a is None or b is None:
                continue
            # 홈/원정이 한쪽으로 쏠리지 않도록 번갈아 배정
            pairs.append((a, b) if (r + i) % 2 == 0 else (b, a))
        first_half.append(pairs)
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    second_half = [[(b, a) for a, b in rnd] for rnd in first_half]
    return first_half + second_half


def generate(seed: int = 2026, played_rounds: int = 15):
    rng = random.Random(seed)
    ids = [t[0] for t in TEAMS]
    att = {t[0]: t[2] for t in TEAMS}
    dfn = {t[0]: t[3] for t in TEAMS}
    rows = []
    for r, pairs in enumerate(round_robin(ids), start=1):
        for h, a in pairs:
            if r <= played_rounds:
                lam = BASE * HOME_ADV * att[h] * dfn[a]
                mu = BASE * att[a] * dfn[h]
                hg = poisson(rng, lam, math.exp(-lam))
                ag = poisson(rng, mu, math.exp(-mu))
                rows.append((r, h, a, str(hg), str(ag)))
            else:
                rows.append((r, h, a, "", ""))
    return [(t[0], t[1]) for t in TEAMS], rows


def write(out_dir: str | Path, seed: int = 2026, played_rounds: int = 15) -> tuple[int, int, int]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    teams, rows = generate(seed, played_rounds)
    with (out / "teams.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "name"])
        w.writerows(teams)
    with (out / "matches.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["round", "home", "away", "home_goals", "away_goals"])
        w.writerows(rows)
    played = sum(1 for r in rows if r[3] != "")
    return len(teams), len(rows), played
