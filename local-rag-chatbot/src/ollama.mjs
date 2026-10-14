// Ollama 연결 확인과 스트리밍 답변 (CLAUDE.md 생성 계약)
export const OLLAMA_URL = "http://localhost:11434";
export const LLM_MODEL = "qwen3.5:2b";

export async function pingOllama() {
  try {
    const res = await fetch(`${OLLAMA_URL}/api/tags`);
    return res.ok;
  } catch {
    return false;
  }
}

// 조각이 올 때마다 onToken(text)을 부르고, 끝나면 전체 답변을 돌려준다.
export async function chatStream(messages, onToken) {
  const res = await fetch(`${OLLAMA_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: LLM_MODEL, messages, stream: true, think: false, options: { temperature: 0 } }),
  });
  if (!res.ok) throw new Error(`Ollama 오류 ${res.status}: ${await res.text()}`);

  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let answer = "";
  const handle = (line) => {
    if (!line.trim()) return;
    const msg = JSON.parse(line);
    if (msg.error) throw new Error(`Ollama 오류: ${msg.error}`);
    const piece = msg.message?.content ?? "";
    if (piece) {
      answer += piece;
      onToken(piece);
    }
  };
  for await (const chunk of res.body) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop(); // 덜 받은 줄은 다음 조각과 합친다
    lines.forEach(handle);
  }
  buffer += decoder.decode();
  handle(buffer);
  return answer;
}
