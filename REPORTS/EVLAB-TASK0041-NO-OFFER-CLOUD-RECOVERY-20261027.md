# EV-Lab TASK-0041 — Root cause, complete historic audit, bounded canary

Date: 2026-10-27, Beijing time. Work performed only on EV-Lab using WebCodex/SSH.

## Historical service — independently verified
- `evlab-phase2-official-20261026.service`, frozen `/home/ubuntu/task0024_collector.py` SHA256 `a3ae6db246ba2cd52cdfc3798efe66462fc27d13fb11a8d5345572c4144b162a`.
- Started 2026-10-26 14:08:41 CST; exited 2026-10-27 07:05:42 CST; `Result=exit-code`, `ExecMainStatus=2`, `Restart=no`. Journal IDs 1016,1017,1018: HTTP200 labeled `empty`, then collector logged `STOP consecutive non-successful/empty responses` (ID 1014 was also `empty`, ID 1015 `ok`).
- Historical root `/home/ubuntu/evlab-data/phase2-official-20261026` was copied to the isolated off-Git path `E:\WebCodex-Workspace\EVLab-Data-Backups\task0041-phase2-stopped-20261027\phase2-official-20261026`; no original capture rows were rewritten.
- Independently ran `python tools/task0041_cloud_capture_audit.py --root <copied-root> --parser tools/task0017_official_only.py` on that copy: `PRAGMA quick_check=ok`; **1018/1018** source byte lengths and SHA256 verified across **92** distinct gz files; all HTTP200; recorded counts **1014 ok / 4 empty**, reviewed parser reclassified the four as legitimate **no_offer**. Observed span 2026-10-26 06:08:42.185634–2026-10-26 23:05:42.145295 UTC.
- This proves premature termination caused by an outdated interpretation of a valid no-sale/zero-fixture response. It does not prove a network outage, invalid provider odds, or lost data.

## New bounded cloud canary — startup/continuity evidence
- Corrected existing repository collector: `tools/task0017_official_only.py`; `no_offer` is successful in the bounded loop; actual source errors still count toward stop threshold.
- Deployed source commit `369ff3abc1e011b023120758854a2b77eae21379` verified as an ancestor of local HEAD. Cloud `/home/ubuntu/task0041_collector_v369ff3a.py` SHA256 **7abec388783d33eb11db52b1523cd59ff90da47eecab1d4122c6bf1e9842b5fd**, equal to current local corrected collector.
- Already-running `evlab-task0041-official-20261027.service` started 2026-10-27 10:44:06 CST; independent root `/home/ubuntu/evlab-data/task0041-official-20261027`; configured **120 rounds / max 4 hours / 120s cadence / 20s timeout / three consecutive bad threshold**. This continuation did **not** create a duplicate unit or restart the old root.
- Startup first HTTP200 at 2026-10-27 02:44:06 UTC was `no_offer`. A later direct stdin-only **read-only** audit of the live root (through 2026-10-27 03:26:06 UTC) checked every row and all raw source hashes: **22/22 verified**, SQLite quick_check ok; **11 no_offer + 11 ok**; all HTTP200; five distinct gz files. Unit observed still active after these records.
- Normal no-sale did not stop the process. **Full four-hour service completion still PENDING**, without future success claims.

## Test evidence and limits
- `python -m pytest -q tests/test_task0041_cloud_capture_audit.py tests/test_task0041_no_offer_soak.py`: **8 passed**.
- `python -m pytest -q`: **395 passed in 10.63s**.
- Attempted `python -m ruff check ...` but local Python had **No module named ruff**; lint not claimed as passed.
- No past corpus overwrite; no odds/public raw redistribution; no completed 48h continuous qualification; no reboot recovery; no proof of executable Pinnacle price, model EV, CLV, or profit.

**Decision:** historic failure + provenance, negative regression, and new canary startup/continuity ACCEPT; 120-round/four-hour final audit remains PENDING. Next observation must read the terminal result and verify all canary rows without overwriting any existing root.
