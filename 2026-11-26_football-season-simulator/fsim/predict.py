"""단일 경기 예측(포아송 스코어 행렬)과 백테스트."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .data import DataError, League
from .model import Strength, estimate_strength

MAX_GOALS = 10
LN3 = math.log(3)
EPS = 1e-12


def _pmf(lam: float, max_goals: int = MAX_GOALS) -> list[float]:
    out = [math.exp(-lam)]
    for k in range(1, max_goals + 1):
        out.append(out[-1] * lam / k)
    return out


@dataclass
class MatchPrediction:
    home: str
    away: str
    lam: float
    mu: float
    p_home: float
    p_draw: float
    p_away: float
    top_scores: list[tuple[int, int, float]]  # (홈 득점, 원정 득점, 확률), 확률 내림차순
    matrix: list[list[float]]  # matrix[홈 득점][원정 득점]

    @property
    def probs(self) -> tuple[float, float, float]:
        return self.p_home, self.p_draw, self.p_away


def predict_from_rates(home: str, away: str, lam: float, mu: float, top: int = 5) -> MatchPrediction:
    ph, pa = _pmf(lam), _pmf(mu)
    matrix = [[x * y for y in pa] for x in ph]
    total = sum(sum(r) for r in matrix)
    matrix = [[v / total for v in r] for r in matrix]  # 10골 초과 꼬리를 잘라낸 만큼 정규화
    p_home = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if i > j)
    p_draw = sum(matrix[i][i] for i in range(len(matrix)))
    p_away = 1.0 - p_home - p_draw
    cells = [(i, j, matrix[i][j]) for i in range(len(matrix)) for j in range(len(matrix))]
    cells.sort(key=lambda c: (-c[2], c[0], c[1]))
    return MatchPrediction(home, away, lam, mu, p_home, p_draw, p_away, cells[:top], matrix)


def predict_match(strength: Strength, home: str, away: str, top: int = 5) -> MatchPrediction:
    if home == away:
        raise DataError("홈팀과 원정팀이 같습니다")
    for t in (home, away):
        if t not in strength.attack:
            raise DataError(f"알 수 없는 팀 ID '{t}'")
    lam, mu = strength.expected_goals(home, away)
    return predict_from_rates(home, away, lam, mu, top)


# ---------------------------------------------------------------- 백테스트

@dataclass
class Score:
    log_loss: float
    brier: float
    accuracy: float


@dataclass
class BacktestResult:
    train_rounds: int
    n_train: int
    n_test: int
    model: Score
    freq: Score
    uniform: Score


def _outcome(hg: int, ag: int) -> int:
    return 0 if hg > ag else (1 if hg == ag else 2)


def _score(preds: list[tuple[float, float, float]], outcomes: list[int]) -> Score:
    ll = br = hit = 0.0
    for p, o in zip(preds, outcomes):
        ll -= math.log(max(p[o], EPS))
        br += sum((p[k] - (1.0 if k == o else 0.0)) ** 2 for k in range(3))
        # 동률이면 앞(홈 승 → 무 → 원정 승)을 고른다
        hit += 1.0 if max(range(3), key=lambda k: (p[k], -k)) == o else 0.0
    n = len(outcomes)
    return Score(ll / n, br / n, hit / n)


def backtest(league: League, train_rounds: int) -> BacktestResult:
    if train_rounds < 1:
        raise DataError("--train-rounds 는 1 이상이어야 합니다")
    train = [m for m in league.played if m.round <= train_rounds]
    test = [m for m in league.played if m.round > train_rounds]
    if not train:
        raise DataError(f"1~{train_rounds}라운드에 치른 경기가 없습니다")
    if not test:
        raise DataError(f"{train_rounds}라운드 이후에 치른 경기가 없어 평가할 수 없습니다")

    st = estimate_strength(League(league.teams, train))
    outcomes = [_outcome(m.home_goals, m.away_goals) for m in test]
    model_preds = [predict_match(st, m.home, m.away).probs for m in test]

    counts = [1.0, 1.0, 1.0]  # 라플라스 보정
    for m in train:
        counts[_outcome(m.home_goals, m.away_goals)] += 1
    tot = sum(counts)
    freq = tuple(c / tot for c in counts)

    return BacktestResult(
        train_rounds=train_rounds,
        n_train=len(train),
        n_test=len(test),
        model=_score(model_preds, outcomes),
        freq=_score([freq] * len(test), outcomes),
        uniform=_score([(1 / 3, 1 / 3, 1 / 3)] * len(test), outcomes),
    )
