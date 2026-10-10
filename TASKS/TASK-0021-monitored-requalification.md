# TASK-0021 — Fixed collector qualification and frequent independent monitoring
- Date: 2026-10-10; Owner Li; Executor/reviewer ChatGPT
- Status: IN_PROGRESS
- Source: 657f566 TASK-0017 fix; original crashed data root frozen.
- Only official Sporttery, no BetExplorer, no trading.
- New root task0021-qual-20261010; pilot one round then bounded 2-hour run only if gate passed; 60s cadence, 20s HTTP timeout, 3 bad consecutive stops, no auto-restart, explicit runtime limit.
- Monitor independently through systemd timer every ~5 min, writing status JSONL; classify missing service/failed state, stale capture (>3 min), non-ok row, SQLite/WAL errors; record actionable FAIL. No false promise of proactive user notification.
- On failed integrity/availability stop new service, preserve data; avoid restart loops. Historical TASK-0006/TASK-0017 left unchanged.
- Test synthetic failure and exact deployed script, verify timer and first observations, report/review, commit push.
