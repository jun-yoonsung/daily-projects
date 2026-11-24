# 스도쿠 솔버 (Sudoku Solver)

- **상태: 진행 중**
- 시작일: 2026-11-24
- 마지막 업데이트: 2026-11-24

## 프로젝트 설명
비트마스크와 MRV(Minimum Remaining Values, 후보가 가장 적은 칸부터 채우기) 휴리스틱을 사용한 백트래킹 스도쿠 솔버입니다.
외부 라이브러리 없이 Python 표준 라이브러리만으로 동작하며, 명령줄(CLI)에서 퍼즐 풀이 · 유일해 검사 · 칸별 후보 숫자 힌트를 제공합니다.

- 행/열/박스별 사용 숫자를 9비트 정수로 관리해 후보 계산이 빠릅니다.
- "세계에서 가장 어려운 스도쿠"(Arto Inkala, 2012)도 약 40ms 안에 풉니다.
- 해를 최대 N개까지 세어 유일해 여부를 검사할 수 있습니다(퍼즐 생성기의 기반).

## 실행 방법
Python 3.10 이상 필요 (외부 의존성 없음).

```bash
cd 2026-11-24_sudoku-solver

# 퍼즐 하나 풀기 (빈칸은 . 또는 0)
python3 -m sudoku solve "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"

# 파일에 있는 여러 퍼즐 풀기 (# 으로 시작하는 줄은 주석)
python3 -m sudoku solve -f puzzles/samples.txt

# 결과를 81자리 한 줄로 출력
python3 -m sudoku solve --oneline "<81자리>"

# 유일해 여부 검사
python3 -m sudoku check "<81자리>"

# (행, 열) 칸의 후보 숫자 보기 (0부터 시작)
python3 -m sudoku hint "<81자리>" 0 2

# 테스트
python3 -m unittest discover -s tests -v
```

## 사용 기술
- Python 3 (표준 라이브러리: argparse, dataclasses, unittest)
- 알고리즘: 백트래킹, 비트마스크 제약 전파, MRV 휴리스틱

## 구조
```
sudoku/board.py   # 파싱, 출력, 규칙 검증
sudoku/solver.py  # 비트마스크 + MRV 백트래킹 솔버, 해 개수 세기
sudoku/cli.py     # 명령줄 인터페이스 (solve / check / hint)
puzzles/          # 예제 퍼즐
tests/            # unittest 테스트 (16개)
```

## TODO
- [x] 보드 파싱/출력/검증
- [x] 비트마스크 + MRV 백트래킹 솔버
- [x] 유일해 검사, 후보 힌트 CLI
- [x] 단위 테스트
- [ ] 유일해를 보장하는 퍼즐 생성기 (`generate` 명령, 시드 지원)
- [ ] 사람이 쓰는 기법(Naked Single, Hidden Single 등) 기반 난이도 평가
- [ ] 단계별 풀이 설명 출력 (`explain` 명령)
- [ ] 브라우저에서 플레이할 수 있는 간단한 HTML 페이지

## 알려진 문제
- 현재 없음

## 작업 기록
- 2026-11-24: 프로젝트 시작 — 솔버, CLI(solve/check/hint), 예제 퍼즐, 테스트 16개 작성
