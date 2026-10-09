# TASK-0018 — Five-pool independent field and update-event validation
- Status: IN_PROGRESS
- Date: 2026-10-09
- Prerequisites: TASK-0015 raw reconstruction and TASK-0017 live bounded official-only collection.
- Data: original **immutable** TASK-0006 cloud official regular gzip files and ledger. Do not touch active TASK-0017 service or any running SQLite.
## Prespecified tests
1. Independently parse original nested `value.matchInfoList[].subMatchList[]` and five pools HAD, HHAD, TTG, CRS, HAFU; compare one-by-one odds keys, all odds flags, handicap line, pool permissions, pool clocks to TASK-0015 reconstructed NDJSON. Do NOT import TASK-0015 extractor.
2. Preserve (capture_id, match_id, pool) as join key. Confirm counts/uniqueness, input raw hash, price/flag field sets and total price cells.
3. Count distinct match/pool provider-update timestamps and order of first observation and source updates. Distinguish observed quote changes from timestamp-only updates and repeated polling; assess cross-pool pair timing only if grounded.
4. Reject causal lead/lag inference without synchronized provider clocks and proven offer executability. Report observed event density, effective fixtures and timestamp anomalies.
5. Run tests, independent data audit, REPORT/REVIEW and push. No betting, no new source, no model.
- Gate: ACCEPTED only for concrete schema/time reconstruction; hypothesis alpha NOT TESTED.
