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

## 결정 필요
- LLM에게 어떤 규칙(시스템 메시지)을 줄까?
