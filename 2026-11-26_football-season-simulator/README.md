# 축구 리그 시즌 시뮬레이터 (Football Season Simulator)

- **상태: 진행 중**
- 분류: 스포츠
- 시작일: 2026-11-26
- 마지막 업데이트: 2026-11-26
- 문서: [PRD.md](PRD.md) · [ACCEPTANCE.md](ACCEPTANCE.md) (필수 25/25 충족) · [storyboard.html](storyboard.html)

> ⚠️ 이 프로젝트의 팀 이름과 경기 결과는 모두 **가상 데이터**입니다. 실제 리그·구단과 무관합니다.

## 프로젝트 설명
시즌 중반까지의 경기 결과로 팀별 공격력·수비력을 추정하고, 남은 경기를 포아송 득점 모델로 수천~수만 번 시뮬레이션해
팀별 **우승 / 상위 4위 / 강등(하위 2팀) 확률**, 예상 최종 승점, 최종 순위 분포를 계산하는 CLI 도구입니다.

- 기대 득점: 홈 λ = 기본 득점 × 홈 어드밴티지 × 공격력[홈] × 수비력[원정], 원정 μ = 기본 득점 × 공격력[원정] × 수비력[홈]
- 공격력·수비력은 리그 평균 대비 비율이며, 경기 수가 적은 영향을 줄이려고 1.0 쪽으로 축소 보정(사전 5경기)합니다.
- 순위 기준: 승점 → 득실차 → 다득점 → (현재 순위표) 팀 이름 / (시뮬레이션) 무작위
- 같은 `--seed` 면 같은 결과가 나옵니다. 10,000회 시뮬레이션은 약 0.2초.
- `--html` 로 외부 의존성 없는 단일 HTML 리포트(확률 막대 + 순위 분포 히트맵)를 저장합니다.

## 실행 방법
Python 3.10 이상 필요 (외부 의존성 없음, `requirements.txt` 는 비어 있음). 이 폴더에서 실행하세요.

```bash
python -m fsim table                                  # 현재 순위표
python -m fsim strength                               # 팀 전력 추정
python -m fsim simulate --n 10000 --seed 42           # 시즌 시뮬레이션
python -m fsim simulate --n 10000 --seed 42 --html report.html   # HTML 리포트 저장
python -m fsim table --data 다른/데이터/폴더            # 다른 데이터 사용
python tools/generate_data.py --seed 2026 --rounds 15 # 가상 데이터 다시 생성
python -m unittest discover -s tests -v               # 테스트
```

### 데이터 형식
- `data/teams.csv`: `id,name`
- `data/matches.csv`: `round,home,away,home_goals,away_goals` — 치르지 않은 경기는 점수를 비워 둡니다.

## 사용 기술
Python 표준 라이브러리(csv, random, math, argparse, html, unittest)

## 폴더 구조
```
fsim/            패키지 (data · table · model · sim · report · generator · cli)
tools/           가상 데이터 생성 스크립트
data/            가상 리그 데이터 (12팀, 22라운드 중 15라운드 진행)
tests/           unittest 테스트
```

## TODO
- [x] PRD / 인수 기준 / 스토리보드 작성
- [x] 데이터 로드·검증, 순위표, 전력 추정, 시뮬레이션, CLI, HTML 리포트, 데이터 생성기
- [ ] (선택) `predict 홈 원정` — 단일 경기 승/무/패 확률과 최빈 스코어
- [ ] (선택) `--fix "HAN-BUS=2-1"` — 특정 잔여 경기 결과 고정(What-if)
- [ ] 백테스트: 앞 10라운드로 추정한 모델이 11~15라운드를 얼마나 맞히는지(로그 손실) 확인
- [ ] 마무리 및 상태 "완료" 처리

## 알려진 문제
- 전력 추정은 홈/원정 일정 불균형을 보정하지 않는 단순 비율 방식입니다(더블 라운드로빈 중반이라 영향은 작음).

## 작업 기록
- 2026-11-26: PRD·인수 기준·스토리보드 작성, 핵심 기능(F1~F8) 구현 및 테스트 작성
