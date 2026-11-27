import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import DATA, ROOT

from fsim import load_league
from html_check import check_html


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "fsim", *args],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )


class TestCli(unittest.TestCase):
    def test_table(self):
        p = run("table")
        self.assertEqual(p.returncode, 0, p.stderr)
        lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
        self.assertIn("승점", lines[0])
        self.assertEqual(len(lines), 13)

    def test_strength(self):
        p = run("strength")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("홈 어드밴티지", p.stdout)
        self.assertIn("공격력", p.stdout)
        self.assertIn("수비력", p.stdout)
        for t in load_league(DATA).teams:
            self.assertIn(t.name, p.stdout)

    def test_simulate(self):
        p = run("simulate", "--n", "2000", "--seed", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        header = [ln for ln in p.stdout.splitlines() if "우승" in ln][0]
        for col in ("예상승점", "우승", "상위4", "강등"):
            self.assertIn(col, header)
        self.assertEqual(p.stdout.count("%"), 36)  # 12팀 × 3개 확률

    def test_html_report(self):
        out = Path(tempfile.mkdtemp(prefix="fsim_cli_")) / "out.html"
        p = run("simulate", "--n", "500", "--seed", "3", "--html", str(out))
        self.assertEqual(p.returncode, 0, p.stderr)
        html = out.read_text(encoding="utf-8")
        for t in load_league(DATA).teams:
            self.assertIn(t.name, html)
        self.assertIn("순위 분포", html)
        for bad in ("<script src", "<link", "http"):
            self.assertNotIn(bad, html)
        self.assertEqual(check_html(html), [])

    def test_error_exit_code(self):
        p = run("--data", str(ROOT / "no_such_dir"), "table")
        self.assertEqual(p.returncode, 1)
        self.assertIn("데이터 오류", p.stderr)
        d = Path(tempfile.mkdtemp(prefix="fsim_bad_"))
        (d / "teams.csv").write_text("id,name\nA,알파\nB,베타\n", encoding="utf-8")
        (d / "matches.csv").write_text("round,home,away,home_goals,away_goals\n1,A,XXX,1,0\n", encoding="utf-8")
        p = run("table", "--data", str(d))
        self.assertEqual(p.returncode, 1)
        self.assertIn("2번째 줄", p.stderr)

    def test_predict(self):
        p = run("predict", "HAN", "BUS")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("기대 득점", p.stdout)
        self.assertIn("홈 승 / 무 / 원정 승", p.stdout)
        score_lines = [ln for ln in p.stdout.splitlines() if ln.startswith("  ") and "-" in ln]
        self.assertEqual(len(score_lines), 5)
        self.assertEqual(run("predict", "han", "부산 갈매기").returncode, 0)
        for args in (("HAN", "HAN"), ("HAN", "XXX")):
            q = run("predict", *args)
            self.assertEqual(q.returncode, 1)
            self.assertIn("데이터 오류", q.stderr)

    def test_fix_cli(self):
        p = run("simulate", "--n", "300", "--seed", "1", "--fix", "JEJ-HAN=0-2", "--fix", "SUW-POH=1-1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("고정한 경기 2개", p.stdout)
        self.assertIn("남은 경기 40개", p.stdout)
        for spec in ("HAN-JEJ=1-0", "JEJ-HAN=0:2"):
            q = run("simulate", "--n", "10", "--fix", spec)
            self.assertEqual(q.returncode, 1)
            self.assertIn("--fix", q.stderr)

    def test_backtest(self):
        p = run("backtest", "--train-rounds", "10")
        self.assertEqual(p.returncode, 0, p.stderr)
        for word in ("포아송 모델", "학습 구간 빈도", "균등 1/3", "로그손실", "Brier", "30개 평가"):
            self.assertIn(word, p.stdout)
        self.assertEqual(run("backtest", "--train-rounds", "15").returncode, 1)


if __name__ == "__main__":
    unittest.main()
