import unittest

from helpers import HEADER, write_league

from fsim import load_league, simulate
from fsim.report import render_html


class TestReport(unittest.TestCase):
    def test_escape(self):
        teams = "id,name\nA,<b>악당</b> & Co\nB,베타\n"
        lg = load_league(write_league(teams, HEADER + "1,A,B,1,0\n2,B,A,,\n"))
        html = render_html(lg, simulate(lg, n=50, seed=1))
        self.assertIn("&lt;b&gt;악당&lt;/b&gt; &amp; Co", html)
        self.assertNotIn("<b>악당", html)


if __name__ == "__main__":
    unittest.main()
