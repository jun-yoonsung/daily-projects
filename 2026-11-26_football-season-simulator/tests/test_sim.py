import random
import unittest

from helpers import DATA, HEADER, TEAMS3, write_league

from fsim import compute_table, load_league, poisson, simulate


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


if __name__ == "__main__":
    unittest.main()
