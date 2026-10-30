# TASK-0045 — Restore EV-Lab durable cloud official capture

Date: 2026-10-30. Scope: EV-Lab only, not A-share.

## Root cause
Prior failed transient service `evlab-phase2-official-20261026.service` used
unfixed `task0024_collector.py`: normal HTTP200 `no_offer` was incorrectly
stored as `empty`; three consecutive responses exited status 2 and
`Restart=no` left collection stopped. The corrected TASK0017 collector was
qualified in TASK0041 but its 120-round canary intentionally terminated.

## Recovery specification (do not mutate old evidence)
- Deploy exactly reviewed SHA-pinned `tools/task0017_official_only.py` and
  `task0041_cloud_capture_audit.py` plus new bounded epoch wrapper and
  independent watchdog under EV-Lab-only cloud directory.
- A persistent enabled systemd service creates a unique, create-only
  two-hour (120 × 60-second) capture root, preserves raw gzip SHA256 + SQLite,
  writes a cycle summary on normal exit; `Restart=always` plus 30-second
  cooldown automatically starts the next fresh epoch. A complete bounded epoch
  is *not* the end of the continuous service.
- A separate root-owned systemd health timer every two minutes verifies the
  full current-epoch SQLite and all raw source SHA256 using the accepted
  TASK0041 audit, watches freshness and disk, logs append-only alarms, and
  restarts only the designated EV-Lab service after an unhealthy assessment.
- A low free-disk threshold fails closed, preserving all data. No retention
  deletion, model predictions, result inference, bookmaker bet, or other repo
  filesystem modification.
- Stage tests: no_offer continuity; fault exit creates new root; correct
  normal rollover, manual forced restart and recovered service; verified 2+
  actual HTTP200/no_offer raw captures; health monitor independent SHA check,
  invalid raw detection, forced corruption/stale alarm tests; persistent
  systemd enablement and reboot-target configuration. Whole repo QA passes.
- Raw cloud bytes and local backup stored outside Git; Git holds immutable
  task/deployment/test/report/QA evidence.

## Acceptance boundaries
Engineering **ACCEPT** only after full deployed service and health timer
status, genuine live response/SQLite audits, verified new root after restart
without old data mutation, and remote GitHub push. Long-run availability,
actual 48h/7d uptime and physical reboot resilience remain unproven at
immediate stage close; cannot be claimed from configuration alone.

## Final stage decision (2026-10-30)
Engineering **ACCEPT** after direct remote deployment, two independent live
restart paths (watchdog and native systemd), normal epoch rollover,
independent raw-SHA validation and offcloud closed-epoch restore. Full 430
repository tests passed. Full documented evidence is in
`REPORTS/EVLAB-TASK0045-CONTINUOUS-CLOUD-RECOVERY-20261030.md`
and independent review is in
`REVIEWS/EVLAB-TASK0045-INDEPENDENT-CLOUD-QA-20261030.md`.
Long-run endurance, actual reboot and automated offsite alerts/backups remain
explicitly **PENDING/OUT OF SCOPE**, not inferred to be complete.
