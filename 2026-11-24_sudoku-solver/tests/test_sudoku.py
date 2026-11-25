import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sudoku import (  # noqa: E402
    candidates, count_solutions, has_unique_solution, is_solved, is_valid,
    parse, pretty, solve, to_string,
)
from sudoku.cli import main  # noqa: E402
from sudoku.generator import generate  # noqa: E402
from sudoku.logic import HIDDEN_SINGLE, NAKED_PAIR, logic_solve  # noqa: E402

EASY = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
EASY_SOL = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"
HARD = "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
HARD_SOL = "812753649943682175675491283154237896369845721287169534521974368438526917796318452"
MEDIUM = "..9748...7.........2.1.9.....7...24..64.1.59..98...3.....8.3.2.........6...2759.."
# generate(seed=13, clues=24) 로 얻은 퍼즐: Naked Pair 가 있어야 풀린다
PAIR = ".6...9.5.85.7...9.....3.46......2.7..3...4...9..87.....4.........8..7...7...91..3"


def run_cli(argv):
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(argv)
    return rc, buf.getvalue()


class TestBoard(unittest.TestCase):
    def test_parse_roundtrip(self):
        self.assertEqual(to_string(parse(EASY)), EASY)

    def test_parse_grid_format(self):
        text = pretty(parse(EASY))  # | - + 구분자가 섞인 형식도 파싱 가능해야 함
        self.assertEqual(to_string(parse(text)), EASY)

    def test_parse_zero_as_blank(self):
        self.assertEqual(to_string(parse(EASY.replace(".", "0"))), EASY)

    def test_parse_wrong_length(self):
        with self.assertRaises(ValueError):
            parse("123")

    def test_validity(self):
        self.assertTrue(is_valid(parse(EASY)))
        bad = "55" + EASY[2:]
        self.assertFalse(is_valid(parse(bad)))


class TestSolver(unittest.TestCase):
    def test_solve_easy(self):
        sol = solve(parse(EASY))
        self.assertIsNotNone(sol)
        self.assertTrue(is_solved(sol))
        self.assertEqual(to_string(sol), EASY_SOL)

    def test_solve_hard(self):
        sol = solve(parse(HARD))
        self.assertEqual(to_string(sol), HARD_SOL)

    def test_solution_keeps_givens(self):
        grid = parse(HARD)
        sol = solve(grid)
        for r in range(9):
            for c in range(9):
                if grid[r][c]:
                    self.assertEqual(grid[r][c], sol[r][c])

    def test_does_not_mutate_input(self):
        grid = parse(EASY)
        solve(grid)
        self.assertEqual(to_string(grid), EASY)

    def test_unique(self):
        self.assertTrue(has_unique_solution(parse(EASY)))

    def test_multiple_solutions(self):
        empty = parse("." * 81)
        self.assertEqual(count_solutions(empty, limit=2), 2)
        self.assertFalse(has_unique_solution(empty))

    def test_invalid_input_no_solution(self):
        self.assertIsNone(solve(parse("55" + EASY[2:])))

    def test_unsolvable_but_valid(self):
        # 첫 행 0번 칸에 들어갈 숫자가 없도록 구성: 행에 1~8, 열에 9
        text = "." + "12345678" + "9" + "." * 71
        self.assertIsNone(solve(parse(text)))

    def test_candidates(self):
        grid = parse(EASY)
        self.assertEqual(candidates(grid, 0, 2), [1, 2, 4])
        self.assertEqual(candidates(grid, 0, 0), [])


class TestCli(unittest.TestCase):
    def test_cli_solve_oneline(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["solve", EASY, "--oneline"])
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip(), EASY_SOL)

    def test_cli_check(self):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["check", EASY]), 0)
            self.assertEqual(main(["check", "." * 81]), 1)

    def test_cli_bad_input(self):
        import io
        from contextlib import redirect_stderr
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(["check", "123"]), 2)

    def test_cli_generate(self):
        rc, out = run_cli(["generate", "--seed", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("단서", out)
        self.assertIn("난이도:", out)
        self.assertIn("------+-------+------", out)

    def test_cli_explain(self):
        rc, out = run_cli(["explain", EASY])
        self.assertEqual(rc, 0)
        first = out.splitlines()[0]
        self.assertRegex(first, r"^\s*1\. R[1-9]C[1-9] = [1-9]  \[Naked Single\]  .+")
        self.assertIn("완료: 51단계", out)

    def test_cli_explain_limit(self):
        rc, out = run_cli(["explain", EASY, "--limit", "5"])
        self.assertEqual(rc, 0)
        step_lines = [ln for ln in out.splitlines() if ln.lstrip()[:1].isdigit()]
        self.assertEqual(len(step_lines), 5)
        self.assertIn("총 51단계 중 5단계", out)

    def test_cli_explain_stuck(self):
        rc, out = run_cli(["explain", HARD])
        self.assertEqual(rc, 0)
        self.assertIn("기본 기법으로 더 진행할 수 없음", out)
        self.assertIn("남은 빈칸 60개", out)

    def test_cli_rate(self):
        rc, out = run_cli(["rate", EASY])
        self.assertEqual(rc, 0)
        self.assertIn("난이도: 쉬움", out)


class TestGenerator(unittest.TestCase):
    def test_generate_reproducible(self):
        a = generate(seed=7)
        b = generate(seed=7)
        self.assertEqual(to_string(a.puzzle), to_string(b.puzzle))
        self.assertNotEqual(to_string(a.puzzle), to_string(generate(seed=8).puzzle))

    def test_generate_unique_solution(self):
        for seed in range(10):
            g = generate(seed=seed, clues=26)
            self.assertTrue(is_valid(g.puzzle))
            self.assertTrue(has_unique_solution(g.puzzle), f"seed={seed}")
            self.assertEqual(to_string(solve(g.puzzle)), to_string(g.solution))

    def test_generate_clue_target(self):
        for seed in range(5):
            g = generate(seed=seed, clues=30)
            self.assertGreaterEqual(g.clues, 30)
            self.assertLessEqual(g.clues, 33)

    def test_generate_rejects_bad_clues(self):
        with self.assertRaises(ValueError):
            generate(seed=1, clues=10)


class TestLogic(unittest.TestCase):
    def test_rate_easy(self):
        self.assertEqual(logic_solve(parse(EASY)).level(), "쉬움")

    def test_rate_expert(self):
        res = logic_solve(parse(HARD))
        self.assertEqual(res.level(), "전문가")
        self.assertTrue(res.stuck)

    def test_rate_needs_hidden_single(self):
        res = logic_solve(parse(MEDIUM))
        self.assertIn(res.level(), ("보통", "어려움", "전문가"))
        self.assertGreaterEqual(res.technique_counts()[HIDDEN_SINGLE], 1)

    def test_rate_naked_pair(self):
        res = logic_solve(parse(PAIR))
        self.assertTrue(res.solved)
        self.assertEqual(res.level(), "어려움")
        self.assertGreaterEqual(res.technique_counts()[NAKED_PAIR], 1)

    def test_logic_matches_solver(self):
        # 논리 풀이로 끝까지 풀린 퍼즐은 솔버 정답과 같아야 한다 (기법 구현 정확성)
        checked = 0
        for text in [EASY, PAIR] + [to_string(generate(seed=s, clues=26).puzzle) for s in range(15)]:
            grid = parse(text)
            res = logic_solve(grid)
            if res.solved:
                self.assertEqual(to_string(res.grid), to_string(solve(grid)))
                checked += 1
            else:
                # 막힌 경우에도 채운 칸은 모두 정답과 일치해야 한다
                sol = solve(grid)
                for r in range(9):
                    for c in range(9):
                        if res.grid[r][c]:
                            self.assertEqual(res.grid[r][c], sol[r][c])
        self.assertGreaterEqual(checked, 3)

    def test_logic_invalid(self):
        self.assertTrue(logic_solve(parse("55" + EASY[2:])).contradiction)


class TestDocs(unittest.TestCase):
    def test_storyboard_html(self):
        from html.parser import HTMLParser
        void = {"meta", "br", "img", "input", "link", "hr"}

        class Checker(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack, self.errors, self.external = [], [], []

            def handle_starttag(self, tag, attrs):
                for k, v in attrs:
                    if k in ("src", "href") and v and not v.startswith("#"):
                        self.external.append(v)
                if tag not in void:
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if self.stack and self.stack[-1] == tag:
                    self.stack.pop()
                else:
                    self.errors.append(tag)

        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storyboard.html")
        ch = Checker()
        with open(path, encoding="utf-8") as f:
            ch.feed(f.read())
        self.assertEqual(ch.stack, [])
        self.assertEqual(ch.errors, [])
        self.assertEqual(ch.external, [])


if __name__ == "__main__":
    unittest.main()
