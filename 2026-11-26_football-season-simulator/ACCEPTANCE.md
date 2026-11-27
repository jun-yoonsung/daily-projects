# 인수 기준 (Acceptance Criteria)

상태 표시: [ ] 미충족 / [x] 충족 — 2026-11-27 기준 필수 25/25 충족, 선택 8/8 충족 (전체 33/33)
테스트 실행: `cd 2026-11-26_football-season-simulator && python -m unittest discover -s tests -v`

## F1. 데이터 로드·검증
- [x] **AC1-1** Given 기본 `data/` 폴더 / When `load_league("data")` 호출 / Then 12개 팀과 132경기(치른 경기 90, 남은 경기 42)가 로드된다. — 확인: `test_data.TestLoad.test_default_data_counts`
- [x] **AC1-2** Given `teams.csv` 에 없는 팀 ID가 있는 경기 줄 / When 로드 / Then 줄 번호를 포함한 `DataError` 가 발생한다. — 확인: `test_data.TestLoad.test_unknown_team`
- [x] **AC1-3** Given 음수 또는 숫자가 아닌 점수, 또는 한쪽 점수만 있는 줄 / When 로드 / Then `DataError` 가 발생한다. — 확인: `test_data.TestLoad.test_bad_score`
- [x] **AC1-4** Given 같은 홈·원정 조합이 두 번 있는 경우 / When 로드 / Then 중복 경기 `DataError` 가 발생한다. — 확인: `test_data.TestLoad.test_duplicate_match`
- [x] **AC1-5** Given 잘못된 데이터 폴더 / When CLI 실행 / Then 오류 메시지를 출력하고 종료 코드 1로 끝난다. — 확인: `test_cli.TestCli.test_error_exit_code`

## F2. 현재 순위표
- [x] **AC2-1** Given 직접 만든 3팀 소규모 결과 / When `compute_table` / Then 승·무·패·득점·실점·득실차·승점이 손 계산과 일치한다. — 확인: `test_table.TestTable.test_small_league`
- [x] **AC2-2** Given 승점이 같은 팀들 / When 정렬 / Then 득실차 → 다득점 → 팀 이름 순으로 정렬된다. — 확인: `test_table.TestTable.test_tiebreak`
- [x] **AC2-3** Given 기본 데이터 / When 순위표 계산 / Then 모든 팀의 경기 수 합이 치른 경기×2(=180)이고 총 득점 = 총 실점이다. — 확인: `test_table.TestTable.test_default_consistency`

## F3. 팀 전력 추정
- [x] **AC3-1** Given 기본 데이터 / When `estimate_strength` / Then 공격력·수비력이 모두 양수이고 공격력의 팀 평균이 1.0 (±0.01)이다. — 확인: `test_model.TestStrength.test_normalized`
- [x] **AC3-2** Given 한 팀이 다른 팀보다 득점이 확실히 많은 데이터 / When 추정 / Then 그 팀의 공격력이 더 크다(수비력은 실점이 적을수록 작다). — 확인: `test_model.TestStrength.test_ordering`
- [x] **AC3-3** Given 홈팀 득점 합이 원정팀보다 많은 데이터 / When 추정 / Then 홈 어드밴티지가 1보다 크다. — 확인: `test_model.TestStrength.test_home_advantage`

## F4. 잔여 경기 시뮬레이션
- [x] **AC4-1** Given 같은 시드 / When 두 번 시뮬레이션 / Then 결과(확률·평균 승점)가 완전히 같다. 다른 시드면 달라진다. — 확인: `test_sim.TestSim.test_reproducible`
- [x] **AC4-2** Given 포아송 샘플러 λ=1.5 / When 20,000번 샘플 / Then 표본 평균이 1.5±0.05 이다. — 확인: `test_sim.TestSim.test_poisson_mean`
- [x] **AC4-3** Given 남은 경기가 없는 리그 / When 시뮬레이션 / Then 현재 순위가 확률 1.0으로 그대로 최종 순위가 된다. — 확인: `test_sim.TestSim.test_no_remaining`
- [x] **AC4-4** Given 기본 데이터, n=10,000 / When `simulate` CLI 실행 / Then 10초 이내에 끝난다. — 확인: `time python -m fsim simulate --n 10000 --seed 42`

## F5. 확률 집계
- [x] **AC5-1** Given 시뮬레이션 결과 / When 집계 / Then 우승 확률 합 = 1, 상위4 확률 합 = 4, 강등 확률 합 = 2 (±1e-9), 각 팀 순위 분포 합 = 1. — 확인: `test_sim.TestSim.test_probability_sums`
- [x] **AC5-2** Given 시뮬레이션 결과 / When 평균 최종 승점 확인 / Then 모든 팀이 현재 승점 이상, 현재 승점 + 3×남은 경기 수 이하이다. — 확인: `test_sim.TestSim.test_points_bounds`

## F6. CLI
- [x] **AC6-1** Given 기본 데이터 / When `python -m fsim table` / Then 12줄의 순위표가 헤더와 함께 출력되고 종료 코드 0. — 확인: `test_cli.TestCli.test_table`
- [x] **AC6-2** Given 기본 데이터 / When `python -m fsim strength` / Then 팀별 공격력·수비력과 홈 어드밴티지가 출력된다. — 확인: `test_cli.TestCli.test_strength`
- [x] **AC6-3** Given 기본 데이터 / When `python -m fsim simulate --n 2000 --seed 1` / Then 우승·상위4·강등 확률 열과 예상 승점 열이 있는 표가 출력된다. — 확인: `test_cli.TestCli.test_simulate`

## F7. HTML 리포트
- [x] **AC7-1** Given `simulate --html out.html` / When 실행 / Then 파일이 생성되고, 모든 팀 이름과 순위 분포 표가 포함되며, `<script src`·`<link`·`http` 외부 참조가 없다. — 확인: `test_cli.TestCli.test_html_report`
- [x] **AC7-2** Given 팀 이름에 `<`, `&` 같은 문자 / When 리포트 생성 / Then HTML 이스케이프된다. — 확인: `test_report.TestReport.test_escape`

## F8. 가상 데이터 생성기
- [x] **AC8-1** Given 12팀 / When 일정 생성 / Then 22라운드, 각 라운드 6경기, 모든 팀 쌍이 홈·원정 한 번씩, 한 라운드에 한 팀은 한 경기만 한다. — 확인: `test_data.TestGenerator.test_schedule`
- [x] **AC8-2** Given 같은 시드 / When `python tools/generate_data.py` 두 번 실행 / Then 같은 CSV가 생성된다. — 확인: `test_data.TestGenerator.test_deterministic`

## 선택 기능 (완료 판정에 포함하지 않음)
### F9. 단일 경기 예측
- [x] **AC9-1 (선택)** Given 기본 데이터 / When `predict_match(strength, "HAN", "BUS")` / Then 홈승+무+원정승 확률 합이 1 (±1e-9)이고, 상위 스코어는 확률 내림차순이며 첫 번째가 행렬의 최댓값이다. — 확인: `test_predict.TestPredict.test_probabilities`
- [x] **AC9-2 (선택)** Given λ=μ 인 두 팀(전력 동일, 홈 어드밴티지 1) / When 예측 / Then 홈승 확률 = 원정승 확률 (±1e-9). — 확인: `test_predict.TestPredict.test_symmetric`
- [x] **AC9-3 (선택)** Given 기본 데이터 / When `python -m fsim predict HAN BUS` / Then 기대 득점·승/무/패 확률·스코어 상위 5개가 출력되고 종료 코드 0, 없는 팀 ID나 같은 팀이면 종료 코드 1. — 확인: `test_cli.TestCli.test_predict`

### F10. What-if 결과 고정
- [x] **AC10-1 (선택)** Given 남은 경기 전부를 `--fix` 로 고정 / When 시뮬레이션 / Then 모든 팀의 최종 순위 확률이 0 또는 1이고 예상 승점이 고정 결과로 손 계산한 승점과 같다(모든 반복에서 고정 결과 사용). — 확인: `test_sim.TestFix.test_fix_all_deterministic`
- [x] **AC10-2 (선택)** Given 한 경기 고정 / When `apply_fixes` / Then 남은 경기 수가 1 줄고, 해당 경기는 지정 점수로 처리된다. 전력 추정은 실제 치른 경기만 사용한다. — 확인: `test_sim.TestFix.test_fix_one`
- [x] **AC10-3 (선택)** Given 이미 치른 경기, 일정에 없는 경기, 형식이 틀린 문자열(`HAN-BUS=2:1` 등) / When `--fix` / Then `DataError` 와 종료 코드 1. — 확인: `test_sim.TestFix.test_fix_errors`, `test_cli.TestCli.test_fix_cli`

### F11. 백테스트
- [x] **AC11-1 (선택)** Given 기본 데이터 / When `backtest(league, train_rounds=10)` / Then 11~15라운드의 30경기가 평가되고, 모델·균등·빈도 기준의 로그 손실이 유한한 양수, Brier 는 0~2, 적중률은 0~1 이며 균등 기준 로그 손실은 ln 3 이다. — 확인: `test_predict.TestBacktest.test_default`
- [x] **AC11-2 (선택)** Given 학습 구간 뒤에 치른 경기가 없거나 train_rounds < 1 / When 백테스트 / Then `DataError`. CLI `python -m fsim backtest --train-rounds 10` 은 표를 출력하고 종료 코드 0. — 확인: `test_predict.TestBacktest.test_errors`, `test_cli.TestCli.test_backtest`

## 기타
- [x] **AC-DOC** `storyboard.html` 이 닫힌 태그로 구성된 단일 HTML이며 외부 의존성(`<script src`, `<link`, `http`)이 없고, 장면 0~8이 모두 있다. — 확인: `test_docs.TestDocs.test_storyboard`
