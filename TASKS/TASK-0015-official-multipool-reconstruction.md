# TASK-0015 — Official five-pool reconstruction and empty-universe diagnosis
- Status: ACCEPTED
- Date: 2026-10-09
- Owner: Li; Executor/Reviewer-of-record: ChatGPT.
- Prior evidence: TASK-0014 at commit 15e6ba9.
- This task is engineering/data-quality reconstruction only; no ROI or hypothesis fishing.
## Frozen scope
1. Read original TASK-0006 `ledger.sqlite3` via read-only immutable SQLite and its raw official gzip, confirm 640 retained raw files stay unchanged.
2. Produce reproducible versioned extractor for HAD, HHAD, TTG, CRS, HAFU. Preserve exact match ID, pool identity, handicap line, provider pool update date/time, collector observation received timestamp, pool status, single/all-up eligibility, quote states and provenance raw hash. Do not collapse separate price versions or represent repeated captures as distinct games.
3. Compare reconstructed HAD tuples against existing official `sporttery_facts` where possible; independent separate-algorithm audit of per-pool record count and critical fields; synthetic parser tests.
4. Diagnose Oct 1–3 empty responses by actual request URL parameters, capture status/failure, raw response flags, existing collector source/config, chronological empty transition. Do not presume API failure from empty match lists.
5. Store compact derived manifests, aggregate tables and diagnostic summaries in Git, bulk detailed rows outside Git; ensure machine-reproducible CLI and explicit data custody.
6. No new collection, no extra credentials, no payment, no cloud service restart, no live bet.
## Acceptance and stop
PASS only if reconstructed source provenance, pool line/quotes/clocks, and comparison denominators are independently checked and exceptions declared. If real root cause cannot be proved, mark UNKNOWN and recommend bounded diagnostic instead of inventing one. Submit REPORT/REVIEW with same-agent review caveat, push, clean Git worktree.
