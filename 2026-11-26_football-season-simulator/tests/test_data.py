import filecmp
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from helpers import DATA, HEADER, ROOT, TEAMS3, write_league

from fsim import DataError, load_league
from fsim.generator import TEAMS, round_robin


class TestLoad(unittest.TestCase):
    def test_default_data_counts(self):
        lg = load_league(DATA)
        self.assertEqual(len(lg.teams), 12)
        self.assertEqual(len(lg.matches), 132)
        self.assertEqual(len(lg.played), 90)
        self.assertEqual(len(lg.remaining), 42)

    def test_unknown_team(self):
        d = write_league(TEAMS3, HEADER + "1,A,B,1,0\n1,A,XXX,2,2\n")
        with self.assertRaises(DataError) as cm:
            load_league(d)
        self.assertIn("3번째 줄", str(cm.exception))
        self.assertIn("XXX", str(cm.exception))

    def test_bad_score(self):
        for bad in ("1,A,B,-1,0\n", "1,A,B,x,0\n", "1,A,B,2,\n"):
            with self.subTest(row=bad):
                d = write_league(TEAMS3, HEADER + bad)
                with self.assertRaises(DataError):
                    load_league(d)

    def test_duplicate_match(self):
        d = write_league(TEAMS3, HEADER + "1,A,B,1,0\n2,A,B,,\n")
        with self.assertRaises(DataError) as cm:
            load_league(d)
        self.assertIn("중복", str(cm.exception))

    def test_reverse_fixture_is_not_duplicate(self):
        d = write_league(TEAMS3, HEADER + "1,A,B,1,0\n2,B,A,,\n")
        self.assertEqual(len(load_league(d).matches), 2)


class TestGenerator(unittest.TestCase):
    def test_schedule(self):
        ids = [t[0] for t in TEAMS]
        rounds = round_robin(ids)
        self.assertEqual(len(rounds), 22)
        pairs = Counter()
        for rnd in rounds:
            self.assertEqual(len(rnd), 6)
            in_round = [t for m in rnd for t in m]
            self.assertEqual(len(in_round), len(set(in_round)), "한 라운드에 두 경기 하는 팀이 있음")
            pairs.update(rnd)
        expected = {(a, b) for a in ids for b in ids if a != b}
        self.assertEqual(set(pairs), expected)
        self.assertTrue(all(c == 1 for c in pairs.values()))

    def test_deterministic(self):
        outs = []
        for _ in range(2):
            out = Path(tempfile.mkdtemp(prefix="fsim_gen_"))
            subprocess.run(
                [sys.executable, str(ROOT / "tools" / "generate_data.py"), "--out", str(out)],
                check=True, capture_output=True,
            )
            outs.append(out)
        for name in ("teams.csv", "matches.csv"):
            self.assertTrue(filecmp.cmp(outs[0] / name, outs[1] / name, shallow=False))
            # 저장소에 포함된 기본 데이터도 같은 시드로 생성된 것이어야 한다
            self.assertTrue(filecmp.cmp(outs[0] / name, DATA / name, shallow=False))


if __name__ == "__main__":
    unittest.main()
