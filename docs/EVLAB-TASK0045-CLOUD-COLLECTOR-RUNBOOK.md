# EV-Lab TASK-0045 — Cloud production collector runbook

This is **EV-Lab only**. Deployed on SSH alias `evlab-cloud` as Ubuntu
systemd units, without editing A-share resources.

## Service / files

- Persistent collector: `evlab-task0045-official.service`, enabled for
  `multi-user.target`. User `ubuntu`, `Restart=always`, cooldown 30 seconds.
- Independent two-minute watchdog: `evlab-task0045-health.timer`, enabled
  for `timers.target`; starts `evlab-task0045-health.service`.
- Collector source and pinned wrappers:
  `/home/ubuntu/evlab-ops/task0045/tools/`.
- Live append-only evidence:
  `/home/ubuntu/evlab-data/task0045-continuous/runs/run-<UTC>-<UUID>/`;
  each epoch gets its own SQLite `official.sqlite3`, `CONFIG.json`, raw
  `raw/<date>/<sourceSHA>.json.gz`. On normal end, a create-only
  `CYCLE_OUTCOME.json` records exit and counts. Aborted SIGKILL epochs
  may lack `CYCLE_OUTCOME.json`, but raw and SQLite WAL persist.
- Health evidence `health/events.jsonl` (append-only) and
  `health/LATEST.json` (atomic refresh). Health files are written by root;
  inspect via `sudo cat` or `sudo tail`.

### Read-only operations

```sh
ssh evlab-cloud
systemctl is-enabled evlab-task0045-official.service evlab-task0045-health.timer
systemctl is-active evlab-task0045-official.service evlab-task0045-health.timer
systemctl show evlab-task0045-official.service -p MainPID -p NRestarts -p Restart -p Result
systemctl list-timers --all --no-pager | grep evlab-task0045
sudo cat /home/ubuntu/evlab-data/task0045-continuous/health/LATEST.json
sudo tail -n 15 /home/ubuntu/evlab-data/task0045-continuous/health/events.jsonl
journalctl -u evlab-task0045-official.service -n 30 --no-pager
df -h /home/ubuntu/evlab-data/task0045-continuous

cd /home/ubuntu/evlab-ops/task0045
root=$(find /home/ubuntu/evlab-data/task0045-continuous/runs -mindepth 1 -maxdepth 1 -type d | sort | tail -1)
/home/ubuntu/venv311/bin/python -m tools.task0041_cloud_capture_audit --root "$root" --parser tools/task0017_official_only.py
```

### Failure behavior / meaning

- Official valid HTTP200 `no_offer` is normal, its raw bytes are retained,
  and it resets the collector's consecutive-bad counter. Do not restart
  a healthy collector just because no matches are being sold.
- A single transport/source error remains a captured real event; monitor
  status becomes `DEGRADED`, not incorrectly `OK`. Three consecutive bad
  rows are `ALERT`; original collector fails at 3, and systemd restarts
  it with a **new** epoch root.
- If no latest capture for 360 seconds, raw SHA/SQLite invalid, low free
  space (below 3 GiB) or unit not running, the independent watchdog logs
  `ALERT` and requests restart of *only* the designated EV-Lab unit. It
  never erases or changes the corrupt old source root.
- The collector itself automatically creates a new root after 120 rounds
  (one per 60 seconds) or 2.5 hours, whichever first, with the normal
  30-second restart interval.
- Failed old transient `evlab-phase2-official-20261026.service` remains
  failed for forensic truth. **Do not restart the old unfixed service.**

### Recovery / updates

```sh
# Only if operationally necessary, restarts into a fresh epoch.
sudo systemctl restart evlab-task0045-official.service
# If timer was stopped for maintenance, start again.
sudo systemctl start evlab-task0045-health.timer
```

Before any future code update, compare source hashes to Git, create a new
versioned deployment manifest and require separate QA. Never overwrite
current/previous cloud capture roots. Always preserve `official.sqlite3-wal`
and `-shm` for an interrupted epoch when making a filesystem backup.
Only copy *completed/closed* epochs off-host unless using a SQLite online
backup/snapshot.

### Explicit remaining limitations

- The boot-enable setting is verified, but **no actual full-server reboot
  was attempted**, since it would interrupt other projects. A long 48h
  or 7d unattended soak has not elapsed at deployment.
- This health mechanism logs **locally** to journald/JSONL. **No external
  pager/email/Slack/webhook alert delivery is installed** under this task.
- There is a working **manual off-cloud restore test for two completed
  one-round epochs**, not a scheduled offsite backup to independent storage.
- Disk safety is fail-closed; there is **no automatic raw retention deletion**.
  Watch free disk, and provision storage/backups before it approaches 3 GiB.
- Official-only source collection is not model retraining, blind scoring,
  Pinnacle CLV, executable betting odds or profitability proof.
