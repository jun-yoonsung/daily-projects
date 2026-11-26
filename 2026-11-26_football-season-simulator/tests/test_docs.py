import unittest

from helpers import ROOT
from html_check import check_html


class TestDocs(unittest.TestCase):
    def test_storyboard(self):
        html = (ROOT / "storyboard.html").read_text(encoding="utf-8")
        self.assertTrue(html.lstrip().lower().startswith("<!doctype html>"))
        self.assertEqual(check_html(html), [])
        for bad in ("<script src", "<link", "http"):
            self.assertNotIn(bad, html)
        for n in range(6):
            self.assertIn(f"장면 {n}", html)

    def test_required_docs_exist(self):
        for name in ("PRD.md", "ACCEPTANCE.md", "storyboard.html", "README.md"):
            self.assertTrue((ROOT / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
