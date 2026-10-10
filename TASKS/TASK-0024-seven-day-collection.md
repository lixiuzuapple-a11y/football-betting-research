# TASK-0024 — Seven-day bounded official-only collection
- Date: 2026-10-10; Status: IN_PROGRESS
- Owner approved 7d official collection and two-minute health checks.
- Freeze: fresh root and no edits to TASK-0006/0017/0021; 60s interval; 7-day wall limit; 3 consecutive bad exits; Restart=no; archive source commit.
- Before launch: fix monitor planned successful completion to terminal COMPLETED, require count >= configured max rounds and service Result=success; running checks still verify freshness, SQLite, disk free >=2GB.
- Independently invoke monitor every 2min; persist JSONL; abnormal exit remains FAIL; no claim of automatic chat notification.
- Test synthetic terminal and failure cases, push versioned code, then deploy, confirm first capture and timer run; report/review.
