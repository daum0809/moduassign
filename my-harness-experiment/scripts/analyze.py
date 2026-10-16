"""results.jsonl을 집계하고 PREREGISTRATION.md의 판정식을 그대로 적용한다."""
import json
import statistics
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
TASKS = ["parse-log", "refactor-util", "fix-failing"]
COND_NAME = {"A": "경험 기록", "B": "대조", "C": "위약 기록"}

rows = [json.loads(l) for l in open(EXP / "results.jsonl", encoding="utf-8") if l.strip()]


def med(xs):
    return statistics.median(xs) if xs else None


def cell(task, cond, rnd):
    return [r for r in rows if r["task"] == task and r["cond"] == cond and r["round"] == rnd]


def summary(rs):
    return {
        "n": len(rs),
        "pass_rate": sum(r["passed"] for r in rs) / len(rs) if rs else None,
        "time": med([r["wall_s"] for r in rs]),
        "time_range": (min(r["wall_s"] for r in rs), max(r["wall_s"] for r in rs)) if rs else None,
        "attempts": med([r["attempts"] for r in rs]),
        "edits": med([r["edits"] for r in rs]),
        "tools": med([r["tool_calls"] for r in rs]),
        "in_tok": med([r["input_tokens"] for r in rs]),
        "out_tok": med([r["output_tokens"] for r in rs]),
        "denials": sum(r["permission_denials"] for r in rs),
        "cost": med([r["cost_usd"] or 0 for r in rs]),
    }


def better(a, x):
    """사전 판정식: 해결률 ≥, 시간 중앙값 10% 이상 짧음, 시도 수 중앙값 ≤."""
    return (a["pass_rate"] >= x["pass_rate"]
            and a["time"] <= 0.9 * x["time"]
            and a["attempts"] <= x["attempts"])


def overlap(a, x):
    return not (a["time_range"][1] < x["time_range"][0] or x["time_range"][1] < a["time_range"][0])


out = []
p = out.append
p("## 1차 시도 (조건 A·B, 각 1회)\n")
p("| 작업 | 조건 | 통과 | 시도 수 | 시간(s) | 편집 | 도구 호출 | 입력 토큰 | 출력 토큰 |")
p("|---|---|---|---|---|---|---|---|---|")
for t in TASKS:
    for c in "AB":
        for r in cell(t, c, 1):
            p(f"| {t} | {c} {COND_NAME[c]} | {'O' if r['passed'] else 'X'} | {r['attempts']} | {r['wall_s']} | "
              f"{r['edits']} | {r['tool_calls']} | {r['input_tokens']:,} | {r['output_tokens']:,} |")

p("\n## 2차 시도 (조건마다 3회, 중앙값)\n")
p("| 작업 | 조건 | n | 해결률 | 시간 중앙값(s) [최소~최대] | 시도 수 | 편집 | 도구 호출 | 입력 토큰 | 출력 토큰 | 권한 거부 | 비용($) |")
p("|---|---|---|---|---|---|---|---|---|---|---|---|")
S = {}
for t in TASKS:
    for c in "ABC":
        rs = cell(t, c, 2)
        if not rs:
            p(f"| {t} | {c} {COND_NAME[c]} | 0 | 미확인 | 미확인 | | | | | | | |")
            continue
        s = S[(t, c)] = summary(rs)
        p(f"| {t} | {c} {COND_NAME[c]} | {s['n']} | {s['pass_rate']:.0%} | {s['time']:.1f} "
          f"[{s['time_range'][0]:.0f}~{s['time_range'][1]:.0f}] | {s['attempts']:g} | {s['edits']:g} | {s['tools']:g} | "
          f"{s['in_tok']:,.0f} | {s['out_tok']:,.0f} | {s['denials']} | {s['cost']:.3f} |")

p("\n## 사전 판정식 적용\n")
p("| 작업 | A vs B | A vs C | 시간 범위 겹침(A·B) | 시간 범위 겹침(A·C) |")
p("|---|---|---|---|---|")
win_b = win_c = 0
for t in TASKS:
    if (t, "A") not in S or (t, "B") not in S or (t, "C") not in S:
        p(f"| {t} | 미확인 | 미확인 | | |")
        continue
    a, b, c = S[(t, "A")], S[(t, "B")], S[(t, "C")]
    wb, wc = better(a, b), better(a, c)
    win_b += wb
    win_c += wc
    p(f"| {t} | {'A가 나음' if wb else '아님'} (시간 {a['time']:.0f}s vs {b['time']:.0f}s) | "
      f"{'A가 나음' if wc else '아님'} (시간 {a['time']:.0f}s vs {c['time']:.0f}s) | "
      f"{'겹침' if overlap(a, b) else '안 겹침'} | {'겹침' if overlap(a, c) else '안 겹침'} |")

if win_b >= 2 and win_c >= 2:
    verdict = "가설 지지"
elif win_b >= 2:
    verdict = "부분 지지 (원인 설명 기각: 위약 조건과 구분되지 않음)"
else:
    verdict = "기각"
p(f"\n**A가 B보다 나은 작업: {win_b}/3, A가 C보다 나은 작업: {win_c}/3 → 판정: {verdict}**")

text = "\n".join(out)
(EXP / "traces" / "summary.md").write_text(text + "\n", encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print(text)
