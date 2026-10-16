"""results-02.jsonl을 집계하고 PREREGISTRATION-02.md의 판정식을 그대로 적용한다."""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_trial import EDIT_TOOLS, SHELL_WRITE  # noqa: E402

EXP = Path(__file__).resolve().parent.parent
TRACES = EXP / "traces" / "exp02"
TASKS = ["parse-log", "refactor-util", "fix-failing"]
MODE = {"P0": "acceptEdits", "P1": "auto"}

rows = [json.loads(l) for l in open(EXP / "results-02.jsonl", encoding="utf-8") if l.strip()]


def first_write(row):
    """시도의 첫 파일 쓰기가 셸(heredoc 등)인지 Write/Edit 도구인지."""
    f = TRACES / f"r2_{row['cond']}_{row['task']}_{row['rep']}.jsonl"
    for line in open(f, encoding="utf-8"):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        for b in ev["message"]["content"]:
            if b.get("type") != "tool_use":
                continue
            if b["name"] in EDIT_TOOLS:
                return "도구"
            if b["name"] in ("Bash", "PowerShell") and SHELL_WRITE.search(str(b["input"].get("command", ""))):
                return "셸"
    return "없음"


def summary(rs):
    times = [r["wall_s"] for r in rs]
    fw = [first_write(r) for r in rs]
    return {
        "n": len(rs),
        "pass_rate": sum(r["passed"] for r in rs) / len(rs),
        "time": statistics.median(times), "tmin": min(times), "tmax": max(times),
        "attempts": statistics.median(r["attempts"] for r in rs),
        "denials": sum(r["permission_denials"] for r in rs),
        "denied_runs": sum(r["permission_denials"] > 0 for r in rs),
        "shell_first": fw.count("셸"),
        "in_tok": statistics.median(r["input_tokens"] for r in rs),
        "out_tok": statistics.median(r["output_tokens"] for r in rs),
        "tools": statistics.median(r["tool_calls"] for r in rs),
    }


out = []
p = out.append
p("## 실험 02 결과 (조건마다 5회, 중앙값)\n")
p("| 작업 | 조건 | n | 해결률 | 시간 중앙값(s) [최소~최대] | 권한 거부 합계 (거부 있던 시도) | 첫 쓰기가 셸 | 시도 수 | 도구 호출 | 입력 토큰 | 출력 토큰 |")
p("|---|---|---|---|---|---|---|---|---|---|---|")
S = {}
for t in TASKS:
    for c in ("P0", "P1"):
        rs = [r for r in rows if r["task"] == t and r["cond"] == c]
        if not rs:
            p(f"| {t} | {c} {MODE[c]} | 0 | 미확인 | | | | | | | |")
            continue
        s = S[(t, c)] = summary(rs)
        p(f"| {t} | {c} {MODE[c]} | {s['n']} | {s['pass_rate']:.0%} | {s['time']:.1f} [{s['tmin']:.0f}~{s['tmax']:.0f}] | "
          f"{s['denials']} ({s['denied_runs']}/{s['n']}) | {s['shell_first']}/{s['n']} | {s['attempts']:g} | {s['tools']:g} | "
          f"{s['in_tok']:,.0f} | {s['out_tok']:,.0f} |")

p("\n## 사전 판정식 적용\n")
ok = {}
for t in ("parse-log", "fix-failing"):
    a, b = S.get((t, "P1")), S.get((t, "P0"))
    if not a or not b:
        ok[t] = None
        continue
    ok[t] = (a["pass_rate"] >= b["pass_rate"] and a["denials"] < b["denials"] and a["time"] <= 0.9 * b["time"])
    p(f"- {t}: P1 해결률 {a['pass_rate']:.0%} vs {b['pass_rate']:.0%}, 거부 {a['denials']} vs {b['denials']}, "
      f"시간 {a['time']:.1f}s vs {b['time']:.1f}s ({(a['time'] / b['time'] - 1):+.0%}) → {'조건 충족' if ok[t] else '조건 불충족'}")
a, b = S.get(("refactor-util", "P1")), S.get(("refactor-util", "P0"))
flat = a is not None and b is not None and abs(a["time"] / b["time"] - 1) < 0.10
if a and b:
    p(f"- refactor-util: 시간 {a['time']:.1f}s vs {b['time']:.1f}s ({(a['time'] / b['time'] - 1):+.0%}) → "
      f"{'10% 미만 (예측대로)' if flat else '10% 이상 (예측과 다름)'}")

p0_denials = sum(S[(t, "P0")]["denials"] for t in TASKS if (t, "P0") in S)
n_ok = sum(1 for v in ok.values() if v)
if p0_denials == 0:
    verdict = "판정 불가 (P0에서 거부가 재현되지 않음)"
elif n_ok == 2 and flat:
    verdict = "지지"
elif n_ok == 2:
    verdict = "사전 판정식이 정하지 않은 경우 (두 작업은 충족, refactor-util 예측은 불일치)"
elif n_ok == 1:
    verdict = "부분 지지"
else:
    verdict = "기각"
p(f"\n**P0 거부 합계 {p0_denials}, 조건 충족 작업 {n_ok}/2, refactor-util 평탄 {'예' if flat else '아니오'} → 판정: {verdict}**")

text = "\n".join(out)
(TRACES / "summary.md").write_text(text + "\n", encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print(text)
