# 인수 기준 (Acceptance Criteria) — 스도쿠 솔버

상태 표시: [ ] 미충족 / [x] 충족 (실제로 실행·테스트로 확인한 항목만 [x])
테스트 실행: `python3 -m unittest discover -s tests -v`

## F1. 파싱 · 출력 · 검증
- [ ] **AC1-1** Given 81자리 문자열(빈칸 `.` 또는 `0`), When `parse` 후 `to_string`, Then 원래 문자열과 같다.
  - 확인: `test_parse_roundtrip`, `test_parse_zero_as_blank`
- [ ] **AC1-2** Given `pretty` 로 출력한 격자 텍스트, When 다시 `parse`, Then 같은 퍼즐이 된다.
  - 확인: `test_parse_grid_format`
- [ ] **AC1-3** Given 칸 수가 81이 아닌 입력, When `parse`, Then `ValueError` 가 발생하고 CLI는 종료 코드 2를 반환한다.
  - 확인: `test_parse_wrong_length`, `test_cli_bad_input`

## F2. 솔버
- [ ] **AC2-1** Given 위키백과 예제 퍼즐, When `solve`, Then 알려진 정답과 일치한다.
  - 확인: `test_solve_easy`
- [ ] **AC2-2** Given Arto Inkala "세계에서 가장 어려운 스도쿠", When `solve`, Then 정답과 일치하고 1초 이내에 끝난다.
  - 확인: `test_solve_hard`, `python3 -m sudoku solve -f puzzles/samples.txt`
- [ ] **AC2-3** Given 규칙을 위반한 퍼즐, When `solve`, Then 해 없음(None)을 반환한다.
  - 확인: `test_invalid_input_no_solution`, `test_unsolvable_but_valid`

## F3. 유일해 검사
- [ ] **AC3-1** Given 유일해 퍼즐, When `check`, Then "유일해 있음"과 종료 코드 0. Given 빈 격자, Then 해가 2개 이상으로 판정하고 종료 코드 1.
  - 확인: `test_unique`, `test_cli_check`

## F4. 후보 힌트
- [ ] **AC4-1** Given 예제 퍼즐의 (0, 2) 칸, When `hint`, Then 후보 `1, 2, 4` 를 출력한다.
  - 확인: `test_candidates`

## F5. 퍼즐 생성기
- [ ] **AC5-1** Given `--seed 7`, When `generate` 를 두 번 실행, Then 같은 퍼즐이 출력된다(재현성).
  - 확인: `test_generate_reproducible`
- [ ] **AC5-2** Given 임의 시드 여러 개, When `generate`, Then 생성된 퍼즐은 항상 유일해를 가지며 규칙을 위반하지 않는다.
  - 확인: `test_generate_unique_solution`
- [ ] **AC5-3** Given `--clues 30`, When `generate`, Then 단서 수가 30 이상이고, 가능한 경우 30에 가깝다(±0~3).
  - 확인: `test_generate_clue_target`
- [ ] **AC5-4** Given CLI `generate --seed 1`, When 실행, Then 퍼즐 격자, 단서 수, 난이도 등급을 출력하고 종료 코드 0.
  - 확인: `test_cli_generate`

## F6. 난이도 평가
- [ ] **AC6-1** Given Naked Single 만으로 풀리는 위키백과 예제, When `rate`, Then 등급 "쉬움".
  - 확인: `test_rate_easy`
- [ ] **AC6-2** Given Arto Inkala 퍼즐, When `rate`, Then 등급 "전문가"(기본 기법으로 막혀 백트래킹 필요).
  - 확인: `test_rate_expert`
- [ ] **AC6-3** Given Hidden Single 이 필요한 퍼즐, When `rate`, Then 등급 "보통" 이상이며 기법별 사용 횟수에 Hidden Single 이 1회 이상 포함된다.
  - 확인: `test_rate_needs_hidden_single`
- [ ] **AC6-4** Given 논리 풀이가 끝까지 진행된 결과, When 결과 격자를 확인, Then 솔버의 정답과 일치한다(기법 구현 정확성).
  - 확인: `test_logic_matches_solver`

## F7. 단계별 설명
- [ ] **AC7-1** Given 예제 퍼즐, When `explain`, Then 각 줄에 단계 번호, 칸 좌표(R행C열, 1부터), 값, 기법 이름, 이유가 출력된다.
  - 확인: `test_cli_explain`
- [ ] **AC7-2** Given `explain --limit 5`, When 실행, Then 처음 5단계만 출력한다.
  - 확인: `test_cli_explain_limit`
- [ ] **AC7-3** Given 기본 기법으로 막히는 퍼즐, When `explain`, Then 막힌 지점에서 "기본 기법으로 더 진행할 수 없음" 안내와 남은 빈칸 수를 출력한다.
  - 확인: `test_cli_explain_stuck`

## 문서
- [ ] **AC-D1** storyboard.html 이 외부 의존성 없이 열리고, 태그가 올바르게 닫혀 있다.
  - 확인: `python3 -c` HTML 파서 검사 스크립트 (README 참고)
