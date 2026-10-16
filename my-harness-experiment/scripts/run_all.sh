#!/usr/bin/env bash
# 전체 실험 실행: 1차(A,B) → A의 notes 작성 → 2차(A,B,C × 3회). 작업 3개는 병렬, 조건은 번갈아 실행.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${WORK:-/c/mh/runs}"            # 저장소 밖 작업 폴더
TRACES="$HERE/../traces"
rm -rf "$WORK" && mkdir -p "$WORK"
rm -f "$HERE/../results.jsonl"
TASKS="parse-log refactor-util fix-failing"

for t in $TASKS; do
  ( python "$HERE/run_trial.py" "$t" A 1 1 "$WORK" "$TRACES"
    python "$HERE/run_trial.py" "$t" B 1 1 "$WORK" "$TRACES" ) &
done
wait
cp -r "$HERE/placebo_notes" "$WORK/notesC"
cp -r "$WORK/notesA" "$TRACES/notesA_snapshot"

for t in $TASKS; do
  ( for rep in 1 2 3; do
      for c in A B C; do python "$HERE/run_trial.py" "$t" "$c" 2 "$rep" "$WORK" "$TRACES"; done
    done ) &
done
wait
echo ALL_DONE
