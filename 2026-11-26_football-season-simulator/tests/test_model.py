import unittest

from helpers import DATA, HEADER, TEAMS3, write_league

from fsim import estimate_strength, load_league


class TestStrength(unittest.TestCase):
    def test_normalized(self):
        st = estimate_strength(load_league(DATA))
        self.assertTrue(all(v > 0 for v in st.attack.values()))
        self.assertTrue(all(v > 0 for v in st.defense.values()))
        self.assertAlmostEqual(sum(st.attack.values()) / len(st.attack), 1.0, delta=0.01)
        self.assertAlmostEqual(sum(st.defense.values()) / len(st.defense), 1.0, delta=0.01)

    def test_ordering(self):
        # A 는 많이 넣고 적게 먹음, C 는 반대
        m = HEADER + "1,A,B,4,0\n2,A,C,5,1\n3,B,C,1,1\n4,B,A,0,3\n5,C,A,0,4\n6,C,B,1,2\n"
        st = estimate_strength(load_league(write_league(TEAMS3, m)))
        self.assertGreater(st.attack["A"], st.attack["B"])
        self.assertGreater(st.attack["A"], st.attack["C"])
        self.assertLess(st.defense["A"], st.defense["B"])
        self.assertLess(st.defense["A"], st.defense["C"])

    def test_home_advantage(self):
        m = HEADER + "1,A,B,3,1\n2,B,C,2,0\n3,C,A,2,1\n"
        st = estimate_strength(load_league(write_league(TEAMS3, m)))
        self.assertGreater(st.home_adv, 1.0)

    def test_no_played_matches(self):
        st = estimate_strength(load_league(write_league(TEAMS3, HEADER + "1,A,B,,\n")))
        self.assertEqual(set(st.attack.values()), {1.0})
        self.assertGreater(st.base, 0)


if __name__ == "__main__":
    unittest.main()
