import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sudoku import (  # noqa: E402
    candidates, count_solutions, has_unique_solution, is_solved, is_valid,
    parse, pretty, solve, to_string,
)
from sudoku.cli import main  # noqa: E402

EASY = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
EASY_SOL = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"
HARD = "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
HARD_SOL = "812753649943682175675491283154237896369845721287169534521974368438526917796318452"


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


if __name__ == "__main__":
    unittest.main()
