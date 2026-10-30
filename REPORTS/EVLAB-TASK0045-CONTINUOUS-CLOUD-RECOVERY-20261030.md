# EV-Lab TASK-0045 — Real persistent cloud collector restored (2026-10-30)

Scope: EV-Lab exclusively. Actual remote inspection, code deployment, service
status, process-fault injection, normal-rollover exercise, full source SHA
audits and off-cloud restore were performed, not proposed.

## Previously failed service and cause

- Cloud prior unit `evlab-phase2-official-20261026.service`: `failed`,
  `ExecMainStatus=2`, `Restart=no`; Oct27 old parser marked normal
  HTTP200 no-offer as `empty`, then aborted on three consecutive empties
  at Oct27 **07:05:42 CST**, after 1,018 captures. This old unit remains
  *untouched* for provenance and was not restarted.
- TASK0041 corrected collector `tools/task0017_official_only.py` already
  demonstrated genuine `no_offer` continuing normally. TASK0041 bounded
  canary ended after its specified 120 rounds by design; it did not form
  a permanent service.

## Actual deployment

- New dedicated cloud path:
  `/home/ubuntu/evlab-ops/task0045/tools/`; isolated new evidence:
  `/home/ubuntu/evlab-data/task0045-continuous/`.
- Service `evlab-task0045-official.service`: `enabled` + `active`,
  `Restart=always`, 30-second restart cooldown, unique new root for
  every 120-round/60-second cadence (~2 hours) epoch, max 2.5 hours,
  20-second HTTP timeout, at most 3 consecutive bad responses, max 350MB
  resident memory, preserve all evidence and stop new writes below 3GiB
  disk free.
- Monitoring `evlab-task0045-health.timer`: `enabled` + `active`,
  every two minutes. Health check reads SQLite and **all** current-epoch
  raw gzipped source bytes and SHA256 through the previously validated
  TASK0041 read-only audit. Checks source freshness (<=360 seconds),
  disk, unit process, status type, and records append-only JSON health
  events. Separate watchdog can restart only this EV-Lab service.
- Collector pinned deployed Git commit `054ec244f541a50f5561627746b683601cb50b37`
  (also present in every newly observed capture row) and exact source
  SHA256 `7abec388783d33eb11db52b1523cd59ff90da47eecab1d4122c6bf1e9842b5fd`.
  Collector wrapper SHA256
  `afa1068a9df4721fd69183e7cbcbda55a14ae3c67e6b8444eec30e614152ac16`.
  Independent raw audit SHA256
  `830fc59b517790eb5746a4dd40c3e85dc0eb8e7fb10aa3ddb6436ea80f40b82b`.
- Cloud watchdog upgraded after live negative-controls into
  `tools/task0045_cloud_health.py` SHA256
  `73e1169a8eb285c4b9365198f650611f87aaaf3efb5a0bdbb24883a737b09cc5`,
  Git commit `6bc863acb5b340ede043a89911c4611d3a602eab`.
  This upgrade was atomic, retained backup of the earlier health module,
  and did *not* interrupt the collector service.

## Real remote evidence

- Initial service started **2026-10-30 15:34:08 CST** and immediately
  captured 55 real official matches, HTTP200; next 60s later HTTP200.
  Independent source root audit: SQLite quick_check `ok`, both raw
  gzip SHA256 and byte counts correct, actual source commit pinned.
- Health first fired 15:34:08 CST: `status=OK`, 1/1 raw SHA verified.
  Timer subsequently ticked and recorded status.
- **Independent watchdog crash recovery**: at 15:35:47 CST deliberately
  SIGKILLed collector; at 15:36:12 the health timer detected unit
  `activating`/PID0, logged `ALERT collector_not_running` and
  `watchdog_action=systemd_restart_requested`, and new collector
  PID1532356 began collecting in a fresh second root.
  At 15:38:22 health check returned `OK`, 3/3 raw SHA verified.
- **Native systemd restart independent of watchdog**: the health timer
  was temporarily stopped with an always-restore shell trap.
  SIGKILL at 15:39:07 CST; systemd itself logged
  `Scheduled restart job, restart counter is at 1` at **15:39:37**;
  new PID1533472, `NRestarts=1`, new third root, healthy real HTTP200.
  The watchdog timer was reactivated.
- Read-only full audits at **15:41:25 CST**:
  3 production epoch roots preserved: 2/2 raw SHA, 3/3 raw SHA, and
  2/2 raw SHA respectively, **7 actual HTTP200 captures, zero SHA
  mismatches, all three SQLite quick_check=ok**. Old unmodified roots
  remained auditable after intentional process termination.
- At **15:45:43 CST**, newly upgraded health tool read latest third root,
  **7/7** SHA verified, consecutive_bad_responses=0,
  `status=OK`, collector PID1533472 active, approximately **39.95 GiB**
  cloud disk free. This is more recent than the 15:41 full root census.

## Normal bounded epoch rollover / off-cloud recovery

- A separate **temporary** EV-Lab-only transient service ran the *same*
  deployed wrapper with `max_rounds=1`, `Restart=always`,
  `RestartSec=8s`, isolated
  `/home/ubuntu/evlab-data/task0045-rotation-qa`. Two independent
  epochs completed around **15:40:17** and **15:40:25 CST**:
  both `collector_exit=0`, 1/1 real HTTP200 and original raw SHA
  verified, SQLite quick_check=ok, and both
  `CYCLE_OUTCOME.json` create-only outcomes recorded. The temporary
  service was stopped, main collector left running.
- Copied those **fully closed** two source roots and outcome manifests
  to E-drive outside Git:
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0045-rotation-QA-offcloud-20261030\task0045-rotation-qa`.
  Both restored SQLite+raw files independently replayed with the
  TASK0041 audit. Restored SQLite SHA256:
  `636ccac09c7f21ab7d56475b212440175f8a79818df1093db59e5f6cefd45f66`
  and `5bd2853e2ad1d695e5f9b99728ca51039f44961e54953d506b7d48d4d7d067bc`.

## Testing / interpretation

- **11 new TASK0045 tests** with actual on-disk fake SQLite/gzip fixtures,
  no-offer classification, mutated raw SHA, process errors and disk gate,
  latest/disabled watchdog health states, single error DEGRADED and
  consecutive failures ALERT, append-only health events, unit target
  allowlist and persistent timer spec.
- **430 whole EV-Lab repository tests passed** after final watchdog patch.
- Original source and all old captures preserved; no A-share services
  or programs modified, no betting or predictions generated in this task.
- **Stage ACCEPT** for actual persistent, real continuously running
  official-only cloud collector, independent integrity timer and two
  independently exercised restart paths plus natural rollover and
  an off-cloud restore check.
- **Not yet accepted**: actual reboot, 48-hour/7-day soak, automated
  independent offsite backup, external alert channel, CLV/ROI, wagering.
  Do not infer these from service `enabled` alone.

Operational runbook: `docs/EVLAB-TASK0045-CLOUD-COLLECTOR-RUNBOOK.md`.
