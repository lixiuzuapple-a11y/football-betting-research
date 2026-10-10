# TASK-0021 — FINAL bounded two-hour collector acceptance

- Audit: 2026-10-10 18:16 CST onwards (read-only final inspection).
- Unit `evlab-task0021-official-20261010.service`: **inactive/dead**, `Result=success`, `ExecMainStatus=0`, log terminal `STOP max_rounds reached` at 2026-10-10 13:10:55 CST. Correct **planned completion**, NOT crash.
- New root `/home/ubuntu/evlab-data/task0021-monitored-20261010`; original TASK-0017 and TASK-0006 immutable roots untouched.

## Independent source QA
- **120/120 captures HTTP200/result=ok**, observed UTC 2026-10-10 03:11:55.009338 to 05:10:54.998874.
- **120/120** raw gzip decompress and SHA256 compare equal to ledger, JSON parse, match counts reconcile. Corrupt/unreadable = **0**.
- SQLite `PRAGMA integrity_check` = `ok`.
- **67 distinct match IDs** over run; 113 captures with 67 fixtures, 7 later captures with 65; not an invariant per capture. 40 distinct full-response payload SHA256.
- Inter-capture 119 gaps range **59.630374..60.406088 seconds**, **0 intervals over 90s**. No rows recording non-ok results.

## Independent health monitor QA
- Independent `evlab-task0021-health.timer` ran and persisted **63** JSONL inspections.
- **59 OK and 4 FAIL**; all four FAIL occurred AFTER successful planned completion at 13:10:55 CST: first 13:11:01 CST, last 13:17:01 CST, both `active=inactive` with capture id 120, last result ok.
- Thus these are **false positives for anomalous shutdown** given planned max-rounds stop, and illustrate missing terminal-success awareness in the monitor. During collector running: no recorded health failure.
- Collector ended and health timer/its stop timer are inactive; confirmed no indefinite monitoring.
- **Mandatory correction before production:** incorporate separate terminal state (COMPLETED) when `systemd Result=success` and the capture-count target reached, stop timer promptly or classify terminal success; retain failure on premature exit or stale data. This correction has not been executed or tested in the current turn.
- Monitoring is local log/systemd-only, not push notification to user.

## Verdict
**Collector two-hour qualification ACCEPTED**; **health monitoring alert semantics CONDITIONALLY ACCEPTED for running state, terminal-shutdown false alerts REJECTED**. Do not represent 63 checks as all OK. Do not automatically start long-running capture without an explicit finite rollout plan and separate final review. No confirmed predictive wagering edge.
