// [1단계] 질문과 비슷한 청크 찾기  (실행: node src/search.mjs "질문1" ["질문2" …] [--k 3])
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { embedQuery, MODEL, DTYPE } from "./embedder.mjs";

export const WEAK_THRESHOLD = 0.55;

let store = null;

async function loadStore() {
  if (!store) {
    const s = JSON.parse(await readFile("data/vectors.json", "utf8"));
    if (s.model !== MODEL || s.dtype !== DTYPE) {
      throw new Error(`벡터 저장소(${s.model}, ${s.dtype})가 현재 임베딩 설정(${MODEL}, ${DTYPE})과 다릅니다. ` +
        "node src/build-index.mjs 를 다시 실행하세요.");
    }
    store = s;
  }
  return store;
}

export async function search(question, k = 3) {
  const { chunks } = await loadStore();
  const q = await embedQuery(question);
  return chunks
    .map(({ vector, ...c }) => ({ ...c, score: vector.reduce((s, x, i) => s + x * q[i], 0) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
}

function bar(score) {
  const n = Math.max(0, Math.min(20, Math.round(score * 20)));
  return "█".repeat(n) + "░".repeat(20 - n);
}

async function main(argv) {
  let k = 3;
  const questions = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--k") k = Number(argv[++i]);
    else questions.push(argv[i]);
  }
  if (!questions.length) {
    console.log('사용법: node src/search.mjs "질문1" ["질문2" …] [--k 3]');
    process.exit(1);
  }
  for (const question of questions) {
    const hits = await search(question, k);
    const weak = hits[0].score < WEAK_THRESHOLD ? `  ⚠ 관련 자료가 약함(<${WEAK_THRESHOLD})` : "";
    console.log(`\nQ: ${question}${weak}`);
    hits.forEach((h, i) => {
      console.log(`  ${i + 1}. ${h.id}  ${h.score.toFixed(3)}  ${bar(h.score)}  [${h.section}]`);
      console.log(`     ${h.text.slice(0, 60)}…`);
      console.log(`     출처: ${h.url}`);
    });
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv.slice(2)).catch((e) => {
    console.error(e.message);
    process.exit(1);
  });
}
