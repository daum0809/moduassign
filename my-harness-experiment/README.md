# my-harness-experiment: notes/ 경험 기록은 같은 작업의 두 번째 시도를 빠르게 하는가

「도구의 불편을 개선 가설로 바꿔 실험하기」 과제. 도구는 Claude Code(2.1.299, headless), 모델은 `claude-sonnet-5-5`.
전체 보고서는 [experiment-01.md](experiment-01.md)에 있다. 판정식은 실행 전에 [PREREGISTRATION.md](PREREGISTRATION.md)로 커밋했다.

## 불편

LLM과 사업 구상을 이야기하면 새 대화에서는 앞서 정리한 구상을 전부 잊고, 한 창에서 길게 이야기하면 앞에서 정한 것을 헷갈린다.
매번 다시 설명하고 바로잡느라 시간이 아까웠다.
이 실험은 그중 "세션이 바뀌면 지난 경험이 사라진다"를, 성공을 테스트로 판정할 수 있는 코딩 작업으로 옮겨 측정했다.

## 가설

같은 작업을 다시 풀 때 첫 시도의 접근법·오류·해결을 `notes/`에 남기고 두 번째 시도에서 먼저 읽게 하면,
기록 없이 시작할 때보다 소요 시간이 10% 이상 짧고 시도 수는 같거나 적다.
그리고 그 효과는 "먼저 읽으라는 지시"가 아니라 기록의 **내용**에서 온다.

## 실험 설계

| 구분 | 내용 |
|---|---|
| 고정 | Claude Code 2.1.299 headless, `claude-sonnet-5-5`, 작업 3개(parse-log, refactor-util, fix-failing)와 [fixture/](fixture/), 같은 요청 문장, 권한 `acceptEdits`+`Bash(python:*)`, MCP 없음, auto memory 끔, 시도마다 새 세션, 최대 3회 요청 |
| 조작 (하나) | notes/의 내용: **A** 1차 시도 뒤 Claude가 쓴 3줄 노트 / **B** 없음 / **C** 위약(같은 형식의 일반론, 요청 문장은 A와 같음) |
| 측정 | 해결률, 시간, 시도 수 + 입력·출력 토큰, 편집 횟수, 도구 호출, 권한 거부(승인 필요 횟수) |
| 반론과 통제 | "지시 문장 효과일 뿐" → 위약 C / "우연" → 조건마다 3회 반복, 중앙값·범위 / "B도 auto memory로 학습" → auto memory 끔 |
| 사전 판정식 | 작업별 중앙값으로 비교한다. A가 X보다 낫다 = 해결률 ≥, 시간 10% 이상 짧음, 시도 수 ≤. A>B가 2/3 이상이고 A>C도 2/3 이상이면 지지. A>B만 2/3 이상이면 부분 지지(원인 설명 기각). 그 외는 기각 |

## 결과와 판정

| 작업 | A 경험 기록 | B 대조 | C 위약 | A vs B | A vs C |
|---|---|---|---|---|---|
| parse-log | 54.3s | 65.6s | 55.7s | A 나음 (−17%) | 차이 없음 |
| refactor-util | 53.8s | 50.0s | 51.9s | 아님 | 아님 |
| fix-failing | 53.1s | 74.4s | 54.2s | A 나음 (−29%) | 차이 없음 |

시간은 2차 시도 3회의 중앙값이다. 해결률은 모든 칸 100%, 시도 수는 모든 칸 1이었다.

**판정: 부분 지지, 원인 설명 기각.** notes가 있으면 빨라지는 현상은 재현됐다. 하지만 작업과 무관한 위약 노트로도 똑같이 빨라졌다.
trace를 보면, B는 파일을 bash heredoc으로 쓰려다 권한에 거부되고 Write로 다시 쓰느라 늦었다(parse-log 3/3회, fix-failing 1/3회).
A와 C는 "notes를 먼저 읽어라"는 문장 때문에 Read부터 시작했고, 처음부터 Write를 써서 거부가 없었다.
불편의 원인은 메모리 기능이 아니라 **요청 문장과 권한 정책이 만든 행동 경로**에 가까웠다.

## 후속 실험 02: 권한 모드만 바꾸기

전체 보고서는 [experiment-02.md](experiment-02.md)에 있다. 사전 등록은 [PREREGISTRATION-02.md](PREREGISTRATION-02.md).

실험 01의 해석("B가 느린 건 권한 거부 때문")을 검증했다.
notes 없이 권한 모드만 `acceptEdits`(P0)에서 `auto`(P1)로 바꿨고, 조건마다 5회씩 30세션을 돌렸다.

| 작업 | P0 acceptEdits | P1 auto | 권한 거부 | 사전 판정 |
|---|---|---|---|---|
| parse-log | 68.1s | 56.9s (−16%) | 6 → 0 | 충족 |
| fix-failing | 77.4s | 72.5s (−6%) | 2 → 0 | 불충족 |
| refactor-util | 52.1s | 53.2s (+2%) | 2 → 0 | 예측대로 차이 없음 |

**판정: 부분 지지.** auto 모드는 거부를 확실히 없앴지만, 빨라진 것은 거부가 많던 parse-log뿐이었다.

사후 분석(사전 등록 외, 57회)도 했다. 이 Windows 환경에서는 **셸 호출 1회에 약 7초**가 들고, Read·Write 도구는 거의 0초였다.
실험 01의 A·C가 빨랐던 진짜 이유는 "notes를 먼저 읽어라"는 문장 때문에 셸 대신 Read·Write로 일했기 때문으로 보인다.
이 해석은 다음 실험(요청 문장만 조작)에서 사전 등록 가설로 검증할 대상이다.

## 다시 검토할 조건

- 모델이 1차 시도에서 실제로 실패하는 어려운 작업에서 A가 C보다 빠르면, 원인 설명 기각을 철회한다.
- 권한 규칙을 바꿔 heredoc 거부를 없앴는데도 B가 느리면, 권한 거부 해석을 버린다.
- 다음 실험: 권한 정책만 조작, 요청 문장만 조작, 실패가 생기는 작업으로 경험 기록 재시험.

## 폴더

```
my-harness-experiment/
├── README.md            # 이 요약
├── experiment-01.md     # 실험 보고서 (불편·가설, 근거, 설계, 실행 기록, 결과, 돌아보기, 다음 계획)
├── experiment-02.md     # 후속 실험 보고서 (권한 모드 조작, 사후 분석)
├── PREREGISTRATION.md   # 실험 01: 실행 전에 커밋한 가설과 판정식
├── PREREGISTRATION-02.md # 실험 02: 실행 전에 커밋한 가설과 판정식
├── results.jsonl        # 실험 01 시도별 지표 33행 (notes 작성 3회는 지표에서 제외)
├── results-02.jsonl     # 실험 02 시도별 지표 30행
├── traces/              # 시도별 stream-json 기록, A가 쓴 notes, 집계표 summary.md (실험 02는 traces/exp02/)
├── fixture/             # 고정한 작업 입력 원본 (시도마다 복사해서 사용)
└── scripts/             # run_all.sh, run_trial.py, analyze.py, placebo_notes/
```

다시 실행하기 (Git Bash, Claude Code 로그인 필요):

```bash
CLAUDE_BIN=claude bash scripts/run_all.sh && python scripts/analyze.py
```
