# 스도쿠 솔버 (Sudoku Solver)

- **상태: 완료**
- 분류: 일반
- 시작일: 2026-11-24
- 마지막 업데이트: 2026-11-25
- 문서: [PRD.md](PRD.md) · [ACCEPTANCE.md](ACCEPTANCE.md) (필수 21/21 충족) · [storyboard.html](storyboard.html)

## 프로젝트 설명
비트마스크와 MRV(Minimum Remaining Values, 후보가 가장 적은 칸부터 채우기) 휴리스틱을 사용한 백트래킹 스도쿠 솔버입니다.
외부 라이브러리 없이 Python 표준 라이브러리만으로 동작하며, 명령줄(CLI)에서 퍼즐 풀이 · 유일해 검사 · 칸별 후보 숫자 힌트 · 퍼즐 생성 · 난이도 평가 · 단계별 풀이 설명을 제공합니다.

- 행/열/박스별 사용 숫자를 9비트 정수로 관리해 후보 계산이 빠릅니다.
- "세계에서 가장 어려운 스도쿠"(Arto Inkala, 2012)도 약 40ms 안에 풉니다.
- 해를 최대 N개까지 세어 유일해 여부를 검사할 수 있습니다.
- 시드 기반 생성기가 유일해가 보장된 퍼즐을 만듭니다(같은 시드 → 같은 퍼즐).
- Naked Single / Hidden Single / Naked Pair 를 쓰는 논리 풀이기로 난이도(쉬움·보통·어려움·전문가)를 매기고, 풀이 과정을 한 단계씩 설명합니다.

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

# 유일해 퍼즐 생성 (같은 시드면 같은 퍼즐, --clues 는 남길 단서 수 목표 17~81)
python3 -m sudoku generate --seed 42 --clues 30
python3 -m sudoku generate --seed 42 --oneline

# 기법 기반 난이도 평가
python3 -m sudoku rate "<81자리>"

# 단계별 풀이 설명 (R행C열, 1부터)
python3 -m sudoku explain "<81자리>" --limit 10

# 테스트 (storyboard.html 검사 포함)
python3 -m unittest discover -s tests -v
```

## 사용 기술
- Python 3 (표준 라이브러리: argparse, dataclasses, random, unittest, html.parser)
- 알고리즘: 백트래킹, 비트마스크 제약 전파, MRV 휴리스틱, 사람 기법 기반 논리 풀이

## 구조
```
sudoku/board.py   # 파싱, 출력, 규칙 검증
sudoku/solver.py  # 비트마스크 + MRV 백트래킹 솔버, 해 개수 세기
sudoku/generator.py # 유일해 보장 퍼즐 생성기 (시드 지원)
sudoku/logic.py   # Naked/Hidden Single, Naked Pair 논리 풀이 → 난이도·단계 설명
sudoku/cli.py     # 명령줄 인터페이스 (solve / check / hint / generate / rate / explain)
puzzles/          # 예제 퍼즐
tests/            # unittest 테스트 (33개)
```

## TODO
- [x] 보드 파싱/출력/검증
- [x] 비트마스크 + MRV 백트래킹 솔버
- [x] 유일해 검사, 후보 힌트 CLI
- [x] 단위 테스트
- [x] PRD / 인수 기준 / 스토리보드 문서
- [x] 유일해를 보장하는 퍼즐 생성기 (`generate` 명령, 시드 지원)
- [x] 사람이 쓰는 기법(Naked Single, Hidden Single, Naked Pair) 기반 난이도 평가 (`rate`)
- [x] 단계별 풀이 설명 출력 (`explain` 명령)
- [ ] (선택, 범위 밖) 브라우저에서 플레이할 수 있는 간단한 HTML 페이지 — 나중에 별도 프로젝트로 다룰 후보
- [ ] (선택, 범위 밖) X-Wing 등 고급 기법 추가로 "전문가" 등급 세분화

## 알려진 문제
- 기본 기법 3가지만 구현해서, 사람 기준으로 "어려움" 정도인 퍼즐도 상당수가 "전문가"로 분류됩니다(시드 0~149, 단서 24개 기준 약 53%).
- `generate --clues` 를 22 이하로 주면 유일해를 유지하느라 목표보다 단서가 많이 남을 수 있습니다(출력에 안내 표시).

## 작업 기록
- 2026-11-24: 프로젝트 시작 — 솔버, CLI(solve/check/hint), 예제 퍼즐, 테스트 16개 작성
- 2026-11-25: PRD/인수기준/스토리보드 작성, 퍼즐 생성기(`generate`)·난이도 평가(`rate`)·단계별 설명(`explain`) 구현, 테스트 33개 → 필수 기준 21/21 충족, 상태 "완료"
