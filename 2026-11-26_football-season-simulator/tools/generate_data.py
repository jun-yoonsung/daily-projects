"""가상 리그 데이터(data/teams.csv, data/matches.csv)를 생성한다.

사용법: python tools/generate_data.py [--seed 2026] [--rounds 15] [--out data]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fsim.generator import write  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="가상 축구 리그 데이터 생성기")
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--rounds", type=int, default=15, help="결과를 채울 라운드 수 (기본 15)")
    p.add_argument("--out", default=str(ROOT / "data"))
    args = p.parse_args(argv)
    teams, total, played = write(args.out, args.seed, args.rounds)
    print(f"teams.csv   : {teams} teams")
    print(f"matches.csv : {total} matches (played {played}, remaining {total - played})")
    print(f"저장 위치    : {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
