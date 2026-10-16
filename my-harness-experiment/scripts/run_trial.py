"""한 번의 시도(trial)를 headless Claude Code로 실행하고 지표를 기록한다.

사용: python run_trial.py <task> <cond> <round> <rep> <workroot> <tracedir>
  task  : parse-log | refactor-util | fix-failing
  cond  : A(경험 기록) | B(대조) | C(위약 기록)
  round : 1 | 2
시도마다 fixture/를 새 폴더에 복사해 쓰고, 새 세션으로 시작한다.
테스트가 실패하면 같은 세션을 이어(--resume) 최대 MAX_ATTEMPTS번까지 다시 요청한다.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
FIXTURE = EXP / "fixture"
CLAUDE = os.environ.get("CLAUDE_BIN", "claude")
MODEL = "claude-sonnet-5-5"
MAX_ATTEMPTS = 3
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
# 셸로 파일을 쓰는 명령도 편집으로 센다 (리다이렉트, sed -i, tee, PowerShell 쓰기 cmdlet)
SHELL_WRITE = re.compile(r"(?<![0-9&])>>?\s*(?!&|/dev/null|\$null)[\w./'\"-]|\bsed\s+-i|\btee\b|Set-Content|Out-File|Add-Content")

TASKS = {
    "parse-log": {
        "test": "test_parse.py",
        "prompt": "sample.log에서 오류(ERROR 레벨) 줄만 골라 표로 출력하는 parse.py를 작성해 줘. "
                  "확인: python test_parse.py 가 통과해야 해. 테스트 파일은 수정하지 마.",
    },
    "refactor-util": {
        "test": "test_util.py",
        "prompt": "util.py의 함수 3개에 타입 힌트와 독스트링을 추가해 줘. "
                  "확인: python test_util.py 가 통과해야 해. 테스트 파일은 수정하지 마.",
    },
    "fix-failing": {
        "test": "test_me.py",
        "prompt": "python test_me.py 에서 실패하는 2건을 통과하도록 고쳐 줘. 테스트 파일은 수정하지 마.",
    },
}
NOTES_SUFFIX = "\n\n시작하기 전에 notes/ 폴더의 기록을 먼저 읽고 참고해."
RETRY_PROMPT = "테스트가 아직 실패해. python {test} 결과를 확인하고 고쳐 줘. 테스트 파일은 수정하지 마."
NOTES_PROMPT = ("이번 작업에서 다음에 같은 작업을 할 때 쓸 수 있는 것만 notes/{task}.md에 세 줄 이내로 적어 줘. "
                "1) 접근법 2) 만난 오류와 그 근거(어떤 테스트 결과에서 확인했는지) 3) 해결 방법. "
                "다른 파일은 건드리지 마.")

BASE_ARGS = [
    "--output-format", "stream-json", "--verbose",
    "--model", MODEL,
    "--permission-mode", "acceptEdits",
    "--allowedTools", "Bash(python:*)", "Bash(python3:*)", "Bash(py:*)",
    "--strict-mcp-config",
]


def claude(prompt, cwd, trace_path, resume=None):
    args = [CLAUDE, "-p", prompt, *BASE_ARGS]
    if resume:
        args += ["--resume", resume]
    env = dict(os.environ, CLAUDE_CODE_DISABLE_AUTO_MEMORY="1")
    t0 = time.time()
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, timeout=900)
    wall = time.time() - t0
    with open(trace_path, "a", encoding="utf-8") as f:
        f.write(proc.stdout)
        if proc.stderr.strip():
            f.write(json.dumps({"type": "stderr", "text": proc.stderr}, ensure_ascii=False) + "\n")
    edits, tool_calls, result = 0, 0, None
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls += 1
                    name = block.get("name")
                    cmd = str(block.get("input", {}).get("command", ""))
                    if name in EDIT_TOOLS or (name in ("Bash", "PowerShell") and SHELL_WRITE.search(cmd)):
                        edits += 1
        elif ev.get("type") == "result":
            result = ev
    if result is None:
        raise RuntimeError(f"result 이벤트 없음: {proc.stderr[:500]}")
    u = result.get("usage", {})
    return {
        "session_id": result.get("session_id"),
        "wall_s": round(wall, 1),
        "duration_ms": result.get("duration_ms"),
        "num_turns": result.get("num_turns"),
        "input_tokens": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                        + u.get("cache_read_input_tokens", 0),
        "output_tokens": u.get("output_tokens", 0),
        "cost_usd": result.get("total_cost_usd"),
        "edits": edits,
        "tool_calls": tool_calls,
        "permission_denials": len(result.get("permission_denials", [])),
        "is_error": result.get("is_error"),
    }


def test_passes(cwd, test):
    r = subprocess.run([sys.executable, test], cwd=cwd, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr)[-1500:]


def main():
    task, cond, rnd, rep, workroot, tracedir = sys.argv[1:7]
    spec = TASKS[task]
    work = Path(workroot) / f"r{rnd}" / cond / f"{task}-{rep}"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(FIXTURE, work)
    if rnd == "2" and cond in ("A", "C"):
        src = Path(workroot) / ("notesA" if cond == "A" else "notesC")
        shutil.copytree(src, work / "notes")
    tracedir = Path(tracedir)
    tracedir.mkdir(parents=True, exist_ok=True)
    trace = tracedir / f"r{rnd}_{cond}_{task}_{rep}.jsonl"
    trace.unlink(missing_ok=True)

    prompt = spec["prompt"] + (NOTES_SUFFIX if rnd == "2" and cond in ("A", "C") else "")
    attempts, totals, session, passed, tail = 0, None, None, False, ""
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        m = claude(prompt if attempts == 1 else RETRY_PROMPT.format(test=spec["test"]),
                   work, trace, resume=session)
        session = m["session_id"]
        if totals is None:
            totals = m
        else:
            for k in ("wall_s", "duration_ms", "num_turns", "input_tokens", "output_tokens",
                      "cost_usd", "edits", "tool_calls", "permission_denials"):
                totals[k] = (totals[k] or 0) + (m[k] or 0)
        passed, tail = test_passes(work, spec["test"])
        if passed:
            break

    # 테스트 파일을 몰래 고쳤는지 확인 (고쳤으면 통과로 치지 않는다)
    tampered = (work / spec["test"]).read_bytes() != (FIXTURE / spec["test"]).read_bytes()
    row = {"task": task, "cond": cond, "round": int(rnd), "rep": int(rep),
           "passed": passed and not tampered, "tampered_test": tampered,
           "attempts": attempts, **totals}

    # 1차 시도의 A 조건만 notes/를 남긴다 (같은 세션을 이어서 기록하게 함, 지표에는 넣지 않는다)
    if rnd == "1" and cond == "A":
        claude(NOTES_PROMPT.format(task=task), work, tracedir / f"r1_A_{task}_notes.jsonl", resume=session)
        dst = Path(workroot) / "notesA"
        dst.mkdir(exist_ok=True)
        note = work / "notes" / f"{task}.md"
        if note.exists():
            shutil.copy(note, dst / note.name)

    with open(tracedir.parent / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))
    if not row["passed"]:
        print(tail, file=sys.stderr)


if __name__ == "__main__":
    main()
