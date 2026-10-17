# EV-Lab official corpus off-host backup verification — 2026-10-18

## Outcome
**ACCEPT, scope limited to TASK-0024 and TASK-0025 official bounded captures.**

- Windows independent destination: `E:\WebCodex-Workspace\EVLab-Data-Backups\official-20261018`
- Source: `/home/ubuntu/evlab-data/task0024-official-20261010`, `/home/ubuntu/evlab-data/task0025-official-20261015`
- Transport: authenticated SCP over existing `evlab-cloud` SSH alias; source directories read-only.
- Each cloud source file SHA-256 computed and listed in separate source manifest. Independently compute SHA-256 for every Windows local file and compare relative paths, including all metadata/SQLite and raw payload files.
- Locally reopen both SQLite with read-only URI and check `pragma integrity_check = ok`; decompress and JSON-parse every `*.json.gz` file.
- Local audit result: `BACKUP_VERIFICATION.json` in backup destination; source SHA manifests kept alongside it.

| Run | Local files | Local gzip/JSON valid | SQLite rows | Missing | SHA mismatch | DB integrity |
|---|---:|---:|---:|---:|---:|---|
| TASK-0024 | 1,012 | 1,007 | 6,402 | 0 | 0 | ok |
| TASK-0025 | 715 | 710 | 3,120 | 0 | 0 | ok |

Local directory contents for these two runs total 37,664,010 bytes (file bytes; excluding root-level audit and manifest files). Transport finished exit 0 and audit finished exit 0.

## Deliberate boundaries / remaining risk
- This is **one independent Windows copy** in addition to the original cloud files. It is not equivalent to an independently tested third-location backup or ransomware protection.
- Other historical directories in `/home/ubuntu/evlab-data` (entire directory ~354M at time of audit) **are not included** and remain outside this ACCEPT.
- File-level SHA equality is proven at backup time, not an ongoing immutable retention policy.
- The external backup itself is intentionally **not pushed to ordinary GitHub**; GitHub preserves only metadata and this verification report.
- Prior historical corpus quality conclusions and outcome joining remain separate research gates.

## Next
Inventory and select preservation policy for the other historical EV-Lab assets; establish scheduled separate-location backups with periodic restore audits before reopening predictive research.
