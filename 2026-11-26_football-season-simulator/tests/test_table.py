import unittest

from helpers import DATA, HEADER, TEAMS3, write_league

from fsim import compute_table, load_league


class TestTable(unittest.TestCase):
    def test_small_league(self):
        # A 3-0 B, B 1-1 C, C 0-2 A, B vs A (미진행)
        d = write_league(TEAMS3, HEADER + "1,A,B,3,0\n2,B,C,1,1\n3,C,A,0,2\n4,B,A,,\n")
        rows = {r.team: r for r in compute_table(load_league(d))}
        a, b, c = rows["A"], rows["B"], rows["C"]
        self.assertEqual((a.played, a.win, a.draw, a.loss, a.gf, a.ga, a.gd, a.points), (2, 2, 0, 0, 5, 0, 5, 6))
        self.assertEqual((b.played, b.win, b.draw, b.loss, b.gf, b.ga, b.gd, b.points), (2, 0, 1, 1, 1, 4, -3, 1))
        self.assertEqual((c.played, c.win, c.draw, c.loss, c.gf, c.ga, c.gd, c.points), (2, 0, 1, 1, 1, 3, -2, 1))
        self.assertEqual([r.team for r in compute_table(load_league(d))], ["A", "C", "B"])

    def test_tiebreak(self):
        teams = "id,name\nA,다\nB,가\nC,나\nD,라\n"
        # B 2승 1패, A·C·D 는 1승 1패로 승점 3 동률 → 득실차로 갈린다.
        matches = HEADER + (
            "1,A,B,0,1\n"   # B 승
            "1,C,D,1,0\n"   # C 승
            "2,A,C,4,1\n"   # A 승
            "2,B,D,2,0\n"   # B 승
            "3,D,B,2,0\n"   # D 승
            "3,C,A,,\n"     # 미진행
        )
        rows = compute_table(load_league(write_league(teams, matches)))
        pts = {r.team: r.points for r in rows}
        # 승점: A 3, B 6, C 3, D 3
        self.assertEqual(pts, {"A": 3, "B": 6, "C": 3, "D": 3})
        # A: 득4 실2 (+2), C: 득2 실4 (-2), D: 득2 실3 (-1)
        self.assertEqual([r.team for r in rows], ["B", "A", "D", "C"])

    def test_tiebreak_goals_and_name(self):
        teams = "id,name\nA,다\nB,가\nC,나\n"
        # A 2-2 B, A 1-1 C, B 0-0 C → 모두 승점 2, 득실 0; 다득점 A3 B2 C1
        rows = compute_table(load_league(write_league(teams, HEADER + "1,A,B,2,2\n2,A,C,1,1\n3,B,C,0,0\n")))
        self.assertEqual([r.team for r in rows], ["A", "B", "C"])
        # 완전 동률이면 팀 이름(가나다) 순
        rows = compute_table(load_league(write_league(teams, HEADER + "1,A,B,1,1\n2,B,C,1,1\n3,C,A,1,1\n")))
        self.assertEqual([r.name for r in rows], ["가", "나", "다"])

    def test_default_consistency(self):
        lg = load_league(DATA)
        rows = compute_table(lg)
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(r.played for r in rows), 180)
        self.assertEqual(sum(r.gf for r in rows), sum(r.ga for r in rows))
        self.assertEqual(sum(r.win for r in rows), sum(r.loss for r in rows))


if __name__ == "__main__":
    unittest.main()
