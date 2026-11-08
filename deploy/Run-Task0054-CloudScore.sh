#!/usr/bin/env bash
# EV-Lab cloud TASK0048 scorer; real official result capture + independent QA.
# No result is fetched until the anchored candidate's kickoff plus three hours.
set -Eeuo pipefail
umask 077

ROOT=/home/ubuntu/evlab-forward-publisher-20261108
SHADOW=/home/ubuntu/evlab-forward-shadow-20261108
REPO="$ROOT/git"
FORWARD="$ROOT/evidence"
SCORES="$ROOT/score-evidence"
PYTHON="$SHADOW/venv/bin/python"
INVOCATIONS="$SCORES/scheduler/INVOCATIONS.jsonl"

mkdir -p -m 700 "$SCORES/scheduler" "$SCORES/journal" "$SCORES/attempts"
printf '{"task":"TASK0054-SCORE","phase":"STARTED","at_utc":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$INVOCATIONS"
finish() {
  rc="$?"
  printf '{"task":"TASK0054-SCORE","phase":"FINISHED","at_utc":"%s","exit_code":%d}\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$rc" >> "$INVOCATIONS"
}
trap finish EXIT

[[ -x "$PYTHON" && -d "$REPO/.git" && -d "$FORWARD/journal" ]] ||
    { echo 'Scoring prerequisites unavailable' >&2; exit 2; }
[[ "$(timedatectl show -p NTPSynchronized --value)" == yes ]] ||
    { echo 'Unsynchronized scorer clock' >&2; exit 2; }
[[ "$(git -C "$REPO" remote get-url origin)" == \
    'git@github.com:lixiuzuapple-a11y/football-betting-research.git' ]] ||
    { echo 'Unapproved Git remote' >&2; exit 2; }
[[ "$(git -C "$REPO" branch --show-current)" == main ]] ||
    { echo 'Unapproved Git branch' >&2; exit 2; }
[[ -z "$(git -C "$REPO" status --porcelain --untracked-files=all)" ]] ||
    { echo 'Dirty Git workspace' >&2; exit 2; }
timeout 55 git -C "$REPO" -c credential.interactive=never fetch origin main
git -C "$REPO" merge --ff-only refs/remotes/origin/main
cd "$REPO"
"$PYTHON" -m tools.task0048_scheduled_score \
    --repo "$REPO" --forward-base "$FORWARD" --score-base "$SCORES"
