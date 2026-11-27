import random
import unittest

from helpers import DATA, HEADER, TEAMS3, write_league

from fsim import DataError, apply_fixes, compute_table, estimate_strength, load_league, parse_fix, poisson, simulate


class TestSim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.league = load_league(DATA)
        cls.res = simulate(cls.league, n=3000, seed=7)

    def test_reproducible(self):
        a = simulate(self.league, n=500, seed=123)
        b = simulate(self.league, n=500, seed=123)
        c = simulate(self.league, n=500, seed=124)
        self.assertEqual(a.pos_dist, b.pos_dist)
        self.assertEqual(a.mean_points, b.mean_points)
        self.assertNotEqual(a.mean_points, c.mean_points)

    def test_poisson_mean(self):
        rng = random.Random(0)
        xs = [poisson(rng, 1.5) for _ in range(20000)]
        self.assertAlmostEqual(sum(xs) / len(xs), 1.5, delta=0.05)
        self.assertEqual(poisson(rng, 0.0), 0)

    def test_no_remaining(self):
        m = HEADER + "1,A,B,3,0\n2,B,C,2,1\n3,C,A,0,1\n"
        lg = load_league(write_league(TEAMS3, m))
        res = simulate(lg, n=200, seed=1)
        order = [r.team for r in compute_table(lg)]
        for pos, t in enumerate(order):
            self.assertEqual(res.pos_dist[t][pos], 1.0)
            self.assertEqual(res.mean_points[t], res.current_points[t])

    def test_probability_sums(self):
        r = self.res
        self.assertAlmostEqual(sum(r.title_prob.values()), 1.0, places=9)
        self.assertAlmostEqual(sum(r.top4_prob.values()), 4.0, places=9)
        self.assertAlmostEqual(sum(r.releg_prob.values()), 2.0, places=9)
        for t, dist in r.pos_dist.items():
            self.assertAlmostEqual(sum(dist), 1.0, places=9, msg=t)
        # 각 순위도 정확히 한 팀이 차지
        for pos in range(12):
            self.assertAlmostEqual(sum(d[pos] for d in r.pos_dist.values()), 1.0, places=9)

    def test_points_bounds(self):
        r = self.res
        for t in r.team_ids:
            self.assertGreaterEqual(r.mean_points[t], r.current_points[t])
            self.assertLessEqual(r.mean_points[t], r.current_points[t] + 3 * r.remaining_games[t])
            self.assertEqual(r.remaining_games[t], 7)

    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            simulate(self.league, n=0)


class TestFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.league = load_league(DATA)

    def test_parse(self):
        self.assertEqual(parse_fix(" JEJ-HAN = 0-2 "), ("JEJ", "HAN", 0, 2))

    def test_fix_one(self):
        before = len(self.league.remaining)
        fixed_league, fixed = apply_fixes(self.league, ["JEJ-HAN=0-2"])
        self.assertEqual(len(fixed_league.remaining), before - 1)
        self.assertEqual(len(self.league.remaining), before)  # 원본은 그대로
        self.assertEqual([(m.home, m.away, m.home_goals, m.away_goals) for m in fixed], [("JEJ", "HAN", 0, 2)])
        t0 = {s.team: s for s in compute_table(self.league)}
        t1 = {s.team: s for s in compute_table(fixed_league)}
        self.assertEqual(t1["HAN"].points, t0["HAN"].points + 3)
        self.assertEqual(t1["JEJ"].points, t0["JEJ"].points)
        # CLI 와 같은 방식: 전력은 원본(실제 치른 경기)으로 추정해 넘긴다
        st = estimate_strength(self.league)
        res = simulate(fixed_league, n=300, seed=1, strength=st)
        self.assertEqual(res.remaining_games["HAN"] + 1, sum(
            1 for m in self.league.remaining if "HAN" in (m.home, m.away)))
        self.assertGreaterEqual(res.mean_points["HAN"], t1["HAN"].points)

    def test_fix_all_deterministic(self):
        specs = [f"{m.home}-{m.away}=1-0" for m in self.league.remaining]
        fixed_league, fixed = apply_fixes(self.league, specs)
        self.assertEqual(len(fixed), len(self.league.remaining))
        self.assertEqual(fixed_league.remaining, [])
        res = simulate(fixed_league, n=200, seed=5, strength=estimate_strength(self.league))
        table = compute_table(fixed_league)
        keys = [(s.points, s.gd, s.gf) for s in table]
        for pos, s in enumerate(table):
            self.assertEqual(res.mean_points[s.team], s.points)
            self.assertTrue(all(v in (0.0, 1.0) or keys.count((s.points, s.gd, s.gf)) > 1
                                for v in res.pos_dist[s.team]))
            if keys.count((s.points, s.gd, s.gf)) == 1:
                self.assertEqual(res.pos_dist[s.team][pos], 1.0)

    def test_fix_errors(self):
        played = self.league.played[0]
        bad = [
            f"{played.home}-{played.away}=1-0",  # 이미 치른 경기
            "HAN-HAN=1-0",                         # 일정에 없음
            "XXX-HAN=1-0",                         # 없는 팀
            "JEJ-HAN=0:2", "JEJ-HAN", "JEJ=0-2", "JEJ-HAN=a-1", "JEJ-HAN=-1-0",
            "JEJ-HAN=1-0;JEJ-HAN=2-0",
        ]
        for spec in bad:
            with self.subTest(spec=spec), self.assertRaises(DataError):
                apply_fixes(self.league, [spec])
        with self.assertRaises(DataError):
            apply_fixes(self.league, ["JEJ-HAN=1-0", "JEJ-HAN=2-0"])  # 중복 고정


if __name__ == "__main__":
    unittest.main()
