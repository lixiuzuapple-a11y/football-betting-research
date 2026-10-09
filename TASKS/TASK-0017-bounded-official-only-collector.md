# TASK-0017 — Bounded official-only cloud collector

- Status: RUNNING_BOUNDED — deployment ACCEPTED; 12h data outcome pending
- Date: 2026-10-09
- Owner: Li; Executor/Reviewer: ChatGPT
- Trigger: TASK-0016 found current official Sporttery endpoint operational, but legacy dual-source rounds >60 sec and unqualified reference source.
- Objective: new **official Sporttery only** capture (HAD, HHAD, TTG, CRS, HAFU raw), with no BetExplorer, clean dataset and bounded run.
## Frozen safety gates
1. Never touch frozen TASK-0006 folder or its service/unit. New root `/home/ubuntu/evlab-data/task0017-official-20261009`.
2. Use existing documented GET URL and headers, no bypass/proxy/rotating identity; 60 sec cadence, timeout 20s, 12-hour absolute runtime maximum; explicit per-round raw gzip and SQLite atomic record. Record UTC receive timestamp, raw SHA256, match count, HTTP/parse status, request URL. No result/EV evaluation.
3. Stop and exit nonzero upon three consecutive HTTP errors or unsuccessful/empty official responses; fail closed. Preserve errors/empty response bytes where readable.
4. First commit code and test, run full suite, then cloud **single-round dry run into separate qualification root**. Start bounded transient unit only if verification PASS. Check unit state, output and log, count at least one nonempty capture before declaring RUNNING.
5. New transient service must have automatic hard stop; no indefinite auto-restart, no recurring changes to system startup. Keep detailed output on cloud; version command/manifest/report/QA in Git.
6. No new paid resources, wagering or human account activity.
## Acceptance
Engineering TESTED / STARTED_BOUNDED / BLOCKED statuses separately. Same-agent QA limitations disclosed. If provider empties, system exits automatically; restart only under fresh evidence.
