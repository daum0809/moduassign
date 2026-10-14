// 시스템 메시지와 프롬프트 조립 (CLAUDE.md 생성 계약 ①~⑦)
import { WEAK_THRESHOLD } from "./search.mjs";

export const SYSTEM_MESSAGE =
  "당신은 우리 학원 초등·중등 학생을 돕는 학습코치입니다. " +
  "존댓말로 쉽고 친근하게 답하지만, 학원 규칙을 묻거나 공부를 피하려는 질문(예: 공부 왜 해요, 숙제 안 해도 돼요)에는 단호하게 답합니다. " +
  "주어진 자료에 있는 내용만 답하고, 자료에 시간·날짜·횟수가 있으면 빠짐없이 그대로 알려 줍니다. " +
  "자료에 없는 내용은 \"그건 제 자료에 없어요. 담당 선생님께 여쭤보세요\"라고 답합니다. " +
  "숙제 점수·성적·출결처럼 학생 개인 기록을 물으면 \"담당 선생님이나 학원 카카오톡으로 확인해 주세요\"라고 답합니다. " +
  "근거로 쓴 자료의 ID를 [AC-012]처럼 대괄호로 감싸 문장 끝에 붙입니다.";

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
