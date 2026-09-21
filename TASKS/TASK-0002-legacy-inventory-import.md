# TASK-0002 — Register Legacy Inventory baseline

- Task ID: TASK-0002
- Status: ACCEPTED
- Owner: Li
- Reviewer: ChatGPT
- Source executor: WorkBuddy (legacy inventory task `INVENTORY-20260921-01`)
- Repository migration: ChatGPT
- Risk: Low

## Objective

Register the already-reviewed 2026-09-21 legacy football-betting research inventory as a frozen documentation baseline in this repository, without importing raw historical data or restarting research.

## Context

The legacy inventory was produced by WorkBuddy outside the current GitHub task lifecycle and was reviewed through multiple correction rounds. The Owner then instructed ChatGPT to place the accepted material into the authoritative GitHub ledger.

This task is a **migration/registration task**, not a new research task and not a rerun of the legacy inventory.

## Allowed changes

1. Create exactly five migrated legacy documents under `legacy/2026-09-21-inventory/`:
   - `INVENTORY-20260921-01_竞彩足球研究资产只读盘点.md`
   - `REVISION_NOTES.md`
   - `资产关系说明.md`
   - `清单_数据资产.md`
   - `目录树.md`
2. Restore the previously reviewed REV-3 documentation corrections in the repository copy only.
3. Create `TASKS/TASK-0002-legacy-inventory-import.md`.
4. Create `REPORTS/TASK-0002.md`.
5. Reviewer may later create `REVIEWS/TASK-0002.md` and change this task status from REVIEW to ACCEPTED or REJECTED.

## Forbidden changes

Do not modify legacy source files in the WorkBuddy folder. Do not modify files under `src/`, `tests/`, `data/`, `research/`, or `results/`. Do not rerun historical experiments, train models, backfill research data, restart collectors, alter Git configuration/remotes, rewrite history, force-push, or import large/raw legacy data blobs.

## Required steps

1. Synchronize `main` with `origin/main`.
2. Locate the five legacy Markdown files on the Owner's machine and copy them into the allowed legacy directory.
3. Preserve the three companion documents byte-identically unless a previously reviewed correction requires otherwise.
4. Restore the accepted REV-3 corrections in the main inventory and revision notes:
   - H1 99/250 and H2 42/100 are snapshot values; future auto-accumulation status is `UNKNOWN`.
   - BUG-009 root cause remains `UNKNOWN`; process disappearance is observation, not proof that sandbox sleep is the unique root cause.
   - BUG-001/002/003 are three distinct defects: ROI denominator error, selection-mask/hit-mask error, and unflattened `cKDTree.query` index.
   - Remove stale duplicate bug-table rows.
   - Replace the stale “4 favorable/inflated bugs” count with the accepted count of 3: BUG-001, BUG-002, BUG-004.
   - Remove “orchestration chain currently active” as a present-state claim.
5. Record source/final SHA256 hashes and validation evidence in `REPORTS/TASK-0002.md`.
6. Remove temporary transfer artifacts created during migration.
7. Verify the task scope with `git status` / diff and set this task to REVIEW.

## Acceptance criteria

- Exactly the five intended legacy documents are present under `legacy/2026-09-21-inventory/`.
- No raw legacy data is committed.
- REV-3 corrections are present and the known stale phrases are absent.
- No forbidden research/code path changed.
- A migration report with source/final hashes and validation evidence exists.
- Task state is REVIEW before reviewer acceptance.

## Required report path

`REPORTS/TASK-0002.md`
