"""축구 리그 시즌 시뮬레이터 (가상 데이터 기반)."""

from .data import DataError, League, Match, Team, load_league
from .table import Standing, compute_table
from .model import Strength, estimate_strength
from .sim import SimResult, apply_fixes, parse_fix, poisson, simulate
from .predict import BacktestResult, MatchPrediction, backtest, predict_from_rates, predict_match

__all__ = [
    "DataError", "League", "Match", "Team", "load_league",
    "Standing", "compute_table",
    "Strength", "estimate_strength",
    "SimResult", "apply_fixes", "parse_fix", "poisson", "simulate",
    "BacktestResult", "MatchPrediction", "backtest", "predict_from_rates", "predict_match",
]
