// data/chunks.json → data/vectors.json  (실행: node src/build-index.mjs)
import { readFile, writeFile } from "node:fs/promises";
import { embedDocument, MODEL, DTYPE, DIM } from "./embedder.mjs";

const chunks = JSON.parse(await readFile("data/chunks.json", "utf8"));

// 먼저 검사: 필드 누락·중복 id는 중단, 120자 미만은 경고
const seen = new Set();
for (const c of chunks) {
  const missing = ["id", "text", "url", "section"].filter((k) => !c[k]);
  if (missing.length) throw new Error(`${c.id ?? "(id 없음)"}: 필드 누락 ${missing.join(", ")}`);
  if (seen.has(c.id)) throw new Error(`중복 id: ${c.id}`);
  seen.add(c.id);
  if (c.text.length < 120) console.warn(`⚠ ${c.id}: text가 ${c.text.length}자 (120자 미만)`);
}

const out = [];
for (const c of chunks) {
  const vector = await embedDocument(c);
  if (vector.length !== DIM) throw new Error(`${c.id}: 벡터가 ${vector.length}차원 (${DIM}이어야 함)`);
  out.push({ id: c.id, text: c.text, url: c.url, section: c.section, vector });
  console.log(`✓ ${c.id} (${c.section})`);
}

const first = out[0].vector;
const norm = Math.sqrt(first.reduce((s, x) => s + x * x, 0));
console.log(`첫 벡터 앞 5개: [${first.slice(0, 5).map((x) => x.toFixed(4)).join(", ")}]  노름: ${norm.toFixed(4)}`);

await writeFile("data/vectors.json",
  JSON.stringify({ model: MODEL, dtype: DTYPE, dim: DIM, createdAt: new Date().toISOString(), chunks: out }));
console.log(`저장: data/vectors.json — ${out.length}청크 × ${DIM}차원`);
