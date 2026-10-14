// [2단계] 검색 + 프롬프트 + LLM 답변 + 근거 목록
// 실행: node src/ask.mjs "질문" [--k 3] [--show-prompt] [--no-rag]
import { search, WEAK_THRESHOLD } from "./search.mjs";
import { SYSTEM_MESSAGE, buildPrompt } from "./prompt.mjs";
import { pingOllama, chatStream } from "./ollama.mjs";

const argv = process.argv.slice(2);
let k = 3;
let showPrompt = false;
let noRag = false;
const words = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === "--k") k = Number(argv[++i]);
  else if (argv[i] === "--show-prompt") showPrompt = true;
  else if (argv[i] === "--no-rag") noRag = true;
  else words.push(argv[i]);
}
const question = words.join(" ").trim();
if (!question) {
  console.log('사용법: node src/ask.mjs "질문" [--k 3] [--show-prompt] [--no-rag]');
  process.exit(1);
}

async function ensureOllama() {
  if (!(await pingOllama())) {
    console.error("Ollama가 실행 중인지 확인하세요 (확인: curl.exe http://localhost:11434/api/tags)");
    process.exit(1);
  }
}

const write = (t) => process.stdout.write(t);

if (noRag) {
  // 비교 실험용: 검색·시스템 메시지 없이 질문만 보낸다
  await ensureOllama();
  console.log("💬 답변 (RAG 없이)");
  const t0 = performance.now();
  await chatStream([{ role: "user", content: question }], write);
  console.log(`\n⏱ 답변 ${((performance.now() - t0) / 1000).toFixed(1)}초`);
  process.exit(0);
}

const t0 = performance.now();
const hits = await search(question, k);
const searchSec = (performance.now() - t0) / 1000;
const weak = hits[0].score < WEAK_THRESHOLD;
const messages = [
  { role: "system", content: SYSTEM_MESSAGE },
  { role: "user", content: buildPrompt(question, hits) },
];

if (showPrompt) {
  console.log("===== [system] =====\n" + messages[0].content);
  console.log("\n===== [user] =====\n" + messages[1].content);
  process.exit(0);
}

console.log("🔎 검색 결과");
for (const h of hits) console.log(`  ${h.id}  ${h.score.toFixed(3)}  ${h.section}`);
if (weak) console.log(`  ⚠ 관련 자료가 약함(<${WEAK_THRESHOLD})`);

await ensureOllama();
console.log("💬 답변");
const t1 = performance.now();
const answer = await chatStream(messages, write);
const answerSec = (performance.now() - t1) / 1000;

console.log("\n📚 근거 (LLM에게 넘긴 자료 · ✓ = 답변에 ID가 표시된 자료)");
let marked = 0;
for (const h of hits) {
  const used = answer.includes(h.id);
  if (used) marked++;
  console.log(`  ${used ? "✓" : " "} ${h.id}  ${h.section}  ${h.url}`);
}
if (weak) console.log("  ⚠ 관련 자료가 약해 이 자료들을 답변의 근거로 보기 어렵습니다");
else if (!marked) console.log("  (답변에 ID 표시가 없습니다. 위 자료와 답변을 비교해 확인하세요)");
console.log(`⏱ 검색 ${searchSec.toFixed(1)}초 · 답변 ${answerSec.toFixed(1)}초`);
