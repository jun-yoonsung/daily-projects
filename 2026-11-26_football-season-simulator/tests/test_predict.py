import math
import unittest

from helpers import DATA, HEADER, TEAMS3, write_league

from fsim import DataError, Strength, backtest, estimate_strength, load_league, predict_from_rates, predict_match


class TestPredict(unittest.TestCase):
    def test_probabilities(self):
        st = estimate_strength(load_league(DATA))
        p = predict_match(st, "HAN", "BUS")
        self.assertAlmostEqual(p.p_home + p.p_draw + p.p_away, 1.0, delta=1e-9)
        self.assertTrue(all(0 < x < 1 for x in p.probs))
        probs = [c[2] for c in p.top_scores]
        self.assertEqual(len(probs), 5)
        self.assertEqual(probs, sorted(probs, reverse=True))
        self.assertAlmostEqual(probs[0], max(max(r) for r in p.matrix), delta=1e-15)
        self.assertAlmostEqual(sum(sum(r) for r in p.matrix), 1.0, delta=1e-9)
        lam, mu = st.expected_goals("HAN", "BUS")
        self.assertEqual((p.lam, p.mu), (lam, mu))

    def test_symmetric(self):
        ones = {t: 1.0 for t in ("A", "B")}
        st = Strength(dict(ones), dict(ones), 1.0, 1.4)
        p = predict_match(st, "A", "B")
        self.assertAlmostEqual(p.p_home, p.p_away, delta=1e-9)
        # 손 계산: λ=μ=1 이면 무승부 확률은 Σ e^-2 / (k!)^2 ≈ 0.3085
        q = predict_from_rates("A", "B", 1.0, 1.0)
        expected = sum(math.exp(-2) / math.factorial(k) ** 2 for k in range(11))
        self.assertAlmostEqual(q.p_draw, expected, delta=1e-6)

    def test_errors(self):
        st = estimate_strength(load_league(DATA))
        with self.assertRaises(DataError):
            predict_match(st, "HAN", "HAN")
        with self.assertRaises(DataError):
            predict_match(st, "HAN", "XXX")


class TestBacktest(unittest.TestCase):
    def test_default(self):
        r = backtest(load_league(DATA), train_rounds=10)
        self.assertEqual(r.n_train, 60)
        self.assertEqual(r.n_test, 30)
        for sc in (r.model, r.freq, r.uniform):
            self.assertTrue(math.isfinite(sc.log_loss) and sc.log_loss > 0)
            self.assertTrue(0 <= sc.brier <= 2)
            self.assertTrue(0 <= sc.accuracy <= 1)
        self.assertAlmostEqual(r.uniform.log_loss, math.log(3), delta=1e-12)
        self.assertAlmostEqual(r.uniform.brier, 2 / 3, delta=1e-12)

    def test_errors(self):
        league = load_league(DATA)
        with self.assertRaises(DataError):
            backtest(league, 0)
        with self.assertRaises(DataError):
            backtest(league, 15)  # 16라운드 이후 치른 경기 없음
        d = write_league(TEAMS3, HEADER + "2,A,B,1,0\n")
        with self.assertRaises(DataError):
            backtest(load_league(d), 1)  # 학습 구간에 경기 없음


if __name__ == "__main__":
    unittest.main()
