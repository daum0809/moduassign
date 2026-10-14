# 학원 학습코칭 안내 챗봇

## 제품
- 학원 학생이 공부 방법(시험 계획, 오답노트, 복습 주기, 집중법)과 학원 규칙(결석·보강)을 매번 선생님께 물어봐야 해서 불편하다.
  질문하면 학원 학습코칭 SOP와 공개 자료(위키백과)를 근거로 안내하는 챗봇을 만든다.
- 1단계: 질문과 비슷한 자료를 찾아 보여 준다. 2단계: 찾은 자료를 질문과 함께 LLM에 넣어 답을 받는다.

## 비목표
- 웹 화면, 서버, 배포, 로그인.
- 학생 개인의 성적·출결·숙제 현황 조회(학원 관리 시스템 연동). 개인 현황은 담당 선생님께 확인하도록 안내한다.

## 환경
- 내 PC에서만 실행한다. Node.js로 만들고 PowerShell에서 실행한다.
- LLM은 Ollama의 qwen3.5:2b를 쓴다.

## 작업 규칙
- 요청한 것만 만든다.
- 모르는 사실이나 URL은 지어내지 않는다.
- 만든 뒤 직접 실행해 보고, 결과를 같이 보여 준다.

## 데이터 계약
- 청크 원본은 `data/chunks.json`, 배열이고 각 항목은 `{ id, text, url, section }`.
- `id`는 `AC-001`부터 연속(AC = ACademy), 한 번 붙인 id의 뜻은 바꾸지 않는다.
- `text`는 최소 120자, 사실 하나. 원문에 없는 말을 보태지 않는다.
- `url`은 확인 가능한 출처. 웹은 퍼센트 인코딩된 주소, 내 SOP는 `docs/sop.md#제목`(공백은 하이픈).

## 임베딩 계약
- 모델 `onnx-community/embeddinggemma-300m-ONNX`, transformers.js `pipeline("feature-extraction", MODEL, { dtype: "q8" })`,
  호출 옵션 `{ pooling: "mean", normalize: true }`, 768차원.
- 입력 형식: 문서는 `"title: " + section + " | text: " + text`, 질문은 `"task: search result | query: " + question`.
- `src/embedder.mjs` 한 곳에서만 정의하고 파이프라인은 한 번만 만들어 재사용.
  export: `embedDocument(chunk)`, `embedQuery(question)`, `MODEL`, `DTYPE`, `DIM`.
- 벡터 저장소 `data/vectors.json`은 `{ model, dtype, dim, createdAt, chunks: [{ id, text, url, section, vector }] }`.
  저장소의 model·dtype이 현재 embedder와 다르면 검색을 거부하고 "build-index를 다시 실행하라"고 안내.

## 검색 계약
- 벡터는 정규화되어 있으므로 코사인 유사도 = 내적. 점수 내림차순 top-k(기본 3, `--k`로 변경).
- 약한 근거 기준 `WEAK_THRESHOLD = 0.55`는 `src/search.mjs`에서만 정의·export하고 다른 파일은 import.
  1위 점수가 이보다 낮으면 "관련 자료가 약함" 표시. 결과는 버리지 않는다.
- `search.mjs`는 다른 파일이 `search()`를 import해도 CLI가 실행되지 않게, 직접 실행됐을 때만 CLI를 돈다
  (`import.meta.url === pathToFileURL(process.argv[1]).href` 확인).

## 생성 계약
- 시스템 메시지 (2026-10-14 결정: 학습코치·존댓말·친근하되 규칙과 공부를 피하려는 질문에는 단호·초등중등 대상.
  STEP 8에서 2B 모델이 숫자와 선생님 안내를 빠뜨려, 할 말을 따옴표로 직접 적음):
  "당신은 우리 학원 초등·중등 학생을 돕는 학습코치입니다. 존댓말로 쉽고 친근하게 답하지만, 학원 규칙을 묻거나
  공부를 피하려는 질문(예: 공부 왜 해요, 숙제 안 해도 돼요)에는 단호하게 답합니다. 주어진 자료에 있는 내용만 답하고,
  자료에 시간·날짜·횟수가 있으면 빠짐없이 그대로 알려 줍니다. 자료에 없는 내용은 "그건 제 자료에 없어요. 담당 선생님께
  여쭤보세요"라고 답합니다. 숙제 점수·성적·출결처럼 학생 개인 기록을 물으면 "담당 선생님이나 학원 카카오톡으로 확인해
  주세요"라고 답합니다. 근거로 쓴 자료의 ID를 [AC-012]처럼 대괄호로 감싸 문장 끝에 붙입니다."
  - 이전 초안(STEP 8 1차 실험에 사용)은 git 기록 `2dfe39c`에 있다.
- 사용자 메시지(프롬프트) 순서: ① 자료 소개 ② 근거 원칙 ③ 출처 규칙 ④ KST 현재 시각
  ⑤ `[자료]` + `[AC-xxx] (section) text` 줄들(대괄호 안에는 ID만) ⑥ `[질문]` + 질문 ⑦ 출처 규칙 한 번 더.
- ③ 출처 규칙: "근거가 된 조각의 ID만 [AC-012]처럼 대괄호로 감싸 해당 문장 끝에 표시합니다."
- ⑦ 출처 규칙 한 번 더: "(답할 때 근거로 쓴 자료의 ID를 [AC-012]처럼 문장 끝에 붙입니다.)"
- ② 근거 원칙은 1위 점수에 따라 둘 중 하나. `WEAK_THRESHOLD`는 `src/search.mjs`에서 import.
  - 이상: "자료에 근거한 내용만 답하고, 자료에 없으면 없다고 말합니다."
  - 미만: "주의: 검색된 조각의 유사도가 낮습니다. 질문과 완전히 맞는 근거가 아닐 수 있으니,
    근거에 있는 내용만 짧게 답하고 자료에 없는 부분은 없다고 말합니다."
- LLM: Ollama `http://localhost:11434`, 모델 `qwen3.5:2b`, `POST /api/chat`,
  `{ model, messages, stream: true, think: false, options: { temperature: 0 } }`.
  응답은 NDJSON. `TextDecoder`는 `{ stream: true }`로 써서 한글이 조각 경계에서 깨지지 않게.
- 근거 표시는 LLM에 맡기지 않는다. 답변 뒤에 LLM에게 넘긴 자료를 모두 보여 주고, 답변에 ID가 적힌 자료에 ✓를 붙인다.
- Ollama 연결 확인은 실제로 LLM을 호출할 때만 한다(`--show-prompt`는 Ollama 없이도 동작).
  연결이 안 되면 "Ollama가 실행 중인지 확인하세요"와 확인 명령을 안내하고 종료.

## 결정 필요
- (없음)
