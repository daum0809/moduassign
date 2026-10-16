#!/usr/bin/env bash
# 실험 02: 권한 모드만 조작 (P0=acceptEdits, P1=auto). notes 없음. 작업 3개 병렬, 조건 번갈아 5회.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${WORK:-/c/mh/runs02}"
TRACES="$HERE/../traces/exp02"
export RESULTS="$HERE/../results-02.jsonl"
rm -rf "$WORK" "$TRACES" && mkdir -p "$WORK" "$TRACES"
rm -f "$RESULTS"
for t in parse-log refactor-util fix-failing; do
  ( for rep in 1 2 3 4 5; do
      PERM_MODE=acceptEdits python "$HERE/run_trial.py" "$t" P0 2 "$rep" "$WORK" "$TRACES"
      PERM_MODE=auto        python "$HERE/run_trial.py" "$t" P1 2 "$rep" "$WORK" "$TRACES"
    done ) &
done
wait
echo ALL_DONE
