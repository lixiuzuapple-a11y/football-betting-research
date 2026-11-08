#!/usr/bin/env bash
# EV-Lab TASK0054: single cloud Git publisher under a systemd flock.
# This is an entrypoint, not a standalone bookmaker/betting interface.
# The read-only official data, fixed source evidence and Git remote guards
# are enforced by the existing TASK0046 code (do not weaken its checks).
set -Eeuo pipefail
umask 077

ROOT=/home/ubuntu/evlab-forward-publisher-20261108
SHADOW=/home/ubuntu/evlab-forward-shadow-20261108
REPO="$ROOT/git"
EVIDENCE="$ROOT/evidence"
PYTHON="$SHADOW/venv/bin/python"
IDENTITY="$SHADOW/identity/strict-identity.json"
HISTORY="$SHADOW/history"
INVOCATIONS="$EVIDENCE/scheduler/INVOCATIONS.jsonl"

mkdir -p -m 700 "$EVIDENCE/scheduler" "$EVIDENCE/journal" "$EVIDENCE/runs"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '{"task":"TASK0054","phase":"STARTED","at_utc":"%s"}\n' "$started" >> "$INVOCATIONS"
exit_code=2
finish() {
  rc="$?"
  printf '{"task":"TASK0054","phase":"FINISHED","at_utc":"%s","exit_code":%d}\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$rc" >> "$INVOCATIONS"
}
trap finish EXIT

[[ -x "$PYTHON" && -f "$IDENTITY" && -f "$HISTORY/hf_manifest.json" ]] ||
    { echo 'Missing frozen model inputs' >&2; exit 2; }
[[ "$(sha256sum "$IDENTITY" | cut -d' ' -f1)" == \
  '13d373dbab8363e606cfaf39c478b6035c35c86ad0ffcbf4c53e6e5014f63f2f' ]] ||
    { echo 'Source identity SHA mismatch' >&2; exit 2; }
[[ "$(sha256sum "$HISTORY/hf_manifest.json" | cut -d' ' -f1)" == \
  'eb3c37793866a27f8c1520c78a69e6098fdf79f08622b37fed64070fa1f8748f' ]] ||
    { echo 'Source historical manifest SHA mismatch' >&2; exit 2; }
[[ "$(timedatectl show -p NTPSynchronized --value)" == yes ]] ||
    { echo 'Host NTP not synchronized; PIT fail closed' >&2; exit 2; }
[[ "$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')" -gt 3145728 ]] ||
    { echo 'Free storage below 3 GiB' >&2; exit 2; }

[[ "$(git -C "$REPO" remote get-url origin)" == \
  'git@github.com:lixiuzuapple-a11y/football-betting-research.git' ]] ||
    { echo 'Unapproved Git remote' >&2; exit 2; }
[[ "$(git -C "$REPO" branch --show-current)" == main ]] ||
    { echo 'Unexpected Git branch' >&2; exit 2; }
[[ -z "$(git -C "$REPO" status --porcelain --untracked-files=all)" ]] ||
    { echo 'Dirty cloud Git workspace' >&2; exit 2; }

# Sync exact remote main with no history rewrite. A lost/private remote access
# fails closed. Repeat boundedly for temporary network failures only.
fetched=0
for attempt in 1 2 3; do
  if timeout 55 git -C "$REPO" -c credential.interactive=never fetch origin main; then
    fetched=1
    break
  fi
  [[ "$attempt" == 3 ]] && break
  sleep $((5 * attempt))
done
[[ "$fetched" == 1 ]] || { echo 'Remote fetch failed after 3 attempts' >&2; exit 2; }
git -C "$REPO" merge --ff-only refs/remotes/origin/main
[[ -z "$(git -C "$REPO" status --porcelain --untracked-files=all)" ]] ||
    { echo 'Workspace dirty after fast-forward' >&2; exit 2; }

# A non-Git probe MUST NOT use this entrypoint. The actual TASK0046 Python
# remote check, kickoff lead, source evidence and create-only journal still
# determine whether any candidate is admissible.
commit="$(git -C "$REPO" rev-parse HEAD)"
cd "$REPO"
"$PYTHON" -m tools.task0046_forward_publication \
    --repo "$REPO" \
    --evidence-base "$EVIDENCE" \
    --identity "$IDENTITY" \
    --history "$HISTORY" \
    --source-commit "$commit" \
    --mode publish
