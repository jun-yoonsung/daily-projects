import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA = ROOT / "data"


def write_league(teams_csv: str, matches_csv: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="fsim_"))
    (d / "teams.csv").write_text(teams_csv, encoding="utf-8")
    (d / "matches.csv").write_text(matches_csv, encoding="utf-8")
    return d


TEAMS3 = "id,name\nA,알파\nB,베타\nC,감마\n"
HEADER = "round,home,away,home_goals,away_goals\n"
