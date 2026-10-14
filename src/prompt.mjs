// 시스템 메시지와 프롬프트 조립 (CLAUDE.md 생성 계약 ①~⑦)
import { WEAK_THRESHOLD } from "./search.mjs";

// [초안] 사용자가 직접 고쳐 쓸 문장
export const SYSTEM_MESSAGE =
  "당신은 학원 학습코칭 안내 도우미입니다. 주어진 자료에 근거한 내용만 답하고, 자료에 없는 정보는 " +
  "'제가 가진 자료에는 없습니다'라고 답합니다. 학생 개인의 성적·출결·숙제 현황을 묻는 질문에는 " +
  "자료에 없다고 말하고 담당 선생님께 확인하라고 안내합니다. 근거 조각의 ID만 [AC-012]처럼 대괄호로 감싸 " +
  "해당 문장 끝에 표시합니다.";

function nowKST() {
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul", year: "numeric", month: "long", day: "numeric",
    weekday: "long", hour: "numeric", minute: "2-digit",
  }).format(new Date());
}

export function buildPrompt(question, hits) {
  const weak = hits.length === 0 || hits[0].score < WEAK_THRESHOLD;
  return [
    "다음 자료는 학원 학습코칭에 관한 공개 문서와 학원 SOP에서 뽑은 조각입니다.",
    weak
      ? "주의: 검색된 조각의 유사도가 낮습니다. 질문과 완전히 맞는 근거가 아닐 수 있으니, " +
        "근거에 있는 내용만 짧게 답하고 자료에 없는 부분은 없다고 말합니다."
      : "자료에 근거한 내용만 답하고, 자료에 없으면 없다고 말합니다.",
    "근거가 된 조각의 ID만 [AC-012]처럼 대괄호로 감싸 해당 문장 끝에 표시합니다.",
    `현재 시각은 ${nowKST()}(KST)입니다. '지금', '올해', '다음 주' 같은 상대 표현은 이 시각을 기준으로 해석합니다.`,
    "",
    "[자료]",
    hits.map((h) => `[${h.id}] (${h.section}) ${h.text}`).join("\n\n"),
    "",
    "[질문]",
    question,
    "",
    "(답할 때 근거로 쓴 자료의 ID를 [AC-012]처럼 문장 끝에 붙입니다.)",
  ].join("\n");
}
