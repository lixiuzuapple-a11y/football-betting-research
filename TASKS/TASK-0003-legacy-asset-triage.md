# TASK-0003 — Collect legacy football-research assets into local staging

- Task ID: TASK-0003
- Status: TODO
- Owner: Li
- Reviewer: ChatGPT
- Executor: WorkBuddy
- Risk: Medium
- Type: local file collection / manifest only

## Objective

Collect the actual legacy football-betting research files into one controlled local staging directory so ChatGPT/Reviewer can inspect the real files directly.

This task is **collection only**.

WorkBuddy must not decide what is useful, useless, reusable, scientifically valid, profitable, or safe to delete. Those decisions belong to ChatGPT/Reviewer after the collection is complete.

## Authoritative GitHub context

Before starting, synchronize:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git status -sb
```

Then read:

- `COLLABORATION.md`
- `TASKS/TASK-0003-legacy-asset-triage.md`
- `REVIEWS/TASK-0002.md`
- `legacy/2026-09-21-inventory/`

GitHub is the authoritative task ledger.

## Two-conversation rule

WorkBuddy may see this task notification in:

1. the old **竞彩足球研究** conversation;
2. the current **GitHub / WebCodex 尝试** conversation.

These are not two tasks.

- Old 竞彩足球研究 chat: historical retrieval aid only.
- Current GitHub/WebCodex chat: notification/coordination only.
- Formal task state: GitHub only.
- If either chat conflicts with synchronized `origin/main`, GitHub wins.

The old research chat may be used to locate old files or remember names/paths, but no chat-only claim is evidence that a file/result is valid.

## Required staging location

Create/use exactly:

`E:\OneDrive\OneDrive - Swire Properties Limited\football-betting-legacy-staging\`

This directory is **outside the Git repository**.

Required structure:

```text
football-betting-legacy-staging/
├── 00_INBOX/
├── 00_MANIFEST/
│   ├── manifest.csv
│   ├── tree.txt
│   └── SOURCE_NOTES.md
├── 90_QUARANTINE/
└── 99_DECISIONS/
```

For TASK-0003:

- put collected files only under `00_INBOX/`;
- put inventory metadata only under `00_MANIFEST/`;
- leave `90_QUARANTINE/` empty;
- leave `99_DECISIONS/` empty.

ChatGPT/Reviewer will use `99_DECISIONS/` later.

## Collection scope

Collect **all actual legacy football-betting research assets that can be located on the Owner's machine / WorkBuddy-managed research workspace**, including where present:

- data files: CSV, JSON, JSONL, XLS/XLSX, parquet, sqlite/db and similar;
- raw API responses / snapshots;
- normalized/cleaned/derived datasets;
- forward/prospective ledgers;
- scripts and utilities;
- collector/orchestrator/backfill code;
- experiment code;
- notebooks if any;
- model/parameter/output files;
- reports, markdown, text, HTML;
- methodology/protocol documents;
- old manifests and inventories;
- logs only when they are research evidence rather than disposable runtime noise;
- backup copies where needed to determine duplication;
- files referenced by the frozen inventory;
- relevant files discovered from the old 竞彩足球研究 conversation.

Do not omit a file merely because WorkBuddy thinks it is obsolete or wrong.

## Copy rules

1. **Copy, do not move.**
2. Do not modify source files.
3. Preserve source-relative directory structure as much as practical.
4. If two source roots would collide, place them under distinct top-level source labels inside `00_INBOX/`.
5. Never overwrite a different file silently.
6. Preserve timestamps where the copy mechanism safely supports it.
7. Do not deduplicate by deleting files in this task.
8. Do not rename files merely to make them prettier.
9. Do not change file contents.
10. Do not copy credentials, tokens, cookies, SSH keys, browser profiles, secret config, or personal authentication material.

If a possible secret-bearing file is encountered, do not copy its contents; record path/type in `SOURCE_NOTES.md` as excluded-for-security.

## Manifest requirements

Create `00_MANIFEST/manifest.csv` with one row per copied file and at least:

- source_root
- source_path
- staging_path
- filename
- extension
- bytes
- modified_time
- SHA256
- copy_status
- notes

Create `00_MANIFEST/tree.txt` showing the staged directory tree.

Create `00_MANIFEST/SOURCE_NOTES.md` with:

- source roots searched;
- source roots not accessible;
- files intentionally excluded and why;
- possible missing assets;
- duplicate-hash groups summary;
- copy errors;
- total copied file count;
- total copied bytes;
- unique SHA256 count;
- duplicate SHA256 count/group count.

## Important principle: completeness before cleanliness

TASK-0003 optimizes for **recoverability and completeness**, not for a clean final archive.

Do not delete duplicates.
Do not delete bug-affected data.
Do not delete failed experiments.
Do not delete old reports.
Do not decide which dataset is canonical.

That review comes next.

## Forbidden actions

Do not:

- delete any legacy source file;
- move any legacy source file;
- modify any legacy source file;
- rerun experiments/backtests;
- train models;
- repair historical scripts;
- restart/stop collectors;
- backfill data;
- perform new research;
- browse the external web;
- upload the staged legacy bulk files to GitHub;
- commit large data blobs to GitHub;
- change Git remotes/config;
- rewrite history or force-push;
- classify assets as KEEP/DELETE on your own.

## GitHub changes allowed for TASK-0003

Only:

1. `TASKS/TASK-0003-legacy-asset-triage.md` — status changes;
2. `REPORTS/TASK-0003.md`.

The staged files themselves remain local and **must not** be committed.

## Validation

Before submission verify:

1. staging path exists;
2. `00_INBOX/` contains the collected files;
3. manifest rows correspond to staged files;
4. SHA256 can be recomputed for a sample and matches manifest;
5. `90_QUARANTINE/` is empty;
6. `99_DECISIONS/` is empty;
7. no source file was moved/deleted;
8. no bulk legacy data was staged in Git;
9. only the two allowed GitHub paths changed.

## Required report

Create `REPORTS/TASK-0003.md` containing:

- synchronized starting HEAD;
- exact staging path;
- source roots searched;
- copied file count;
- copied total bytes;
- unique hash count;
- duplicate groups/count;
- excluded files and reason;
- inaccessible/missing source roots;
- copy/manifest validation results;
- Git files changed;
- blockers;
- submission commit hash and push result.

Do not paste the full manifest into GitHub if it is excessively large; summarize it in the report. The authoritative detailed manifest remains in local staging for ChatGPT inspection.

## Completion

When collection is complete:

1. set TASK-0003 status to `REVIEW`;
2. commit only the task status + `REPORTS/TASK-0003.md`;
3. push to `origin/main`;
4. STOP.

Chat message to Owner should contain only:

- TASK-0003
- status = REVIEW
- commit hash
- report path
- staging path
- blockers if any

Do not classify assets.
Do not delete anything.
Do not upload the legacy bulk files to GitHub.
Do not start the next phase.

## Next phase (not part of TASK-0003)

After WorkBuddy submits TASK-0003:

1. ChatGPT/Reviewer inspects the real staged files directly via WebCodex.
2. ChatGPT produces explicit decisions in `99_DECISIONS/`:
   - KEEP
   - DELETE / QUARANTINE
   - REVALIDATE
   - UNKNOWN
3. Only after Owner/Reviewer approval will WorkBuddy receive a separate formal task to:
   - execute deletion/quarantine;
   - copy/synchronize approved retained materials;
   - push only approved GitHub-suitable files/manifests;
   - verify hashes and final state.

This separation is mandatory: **WorkBuddy collects; ChatGPT decides; WorkBuddy executes the approved cleanup/sync.**
