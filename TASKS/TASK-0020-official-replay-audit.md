# TASK-0020 — Official source replay vs genuine update, frozen/live comparison
- Date: 2026-10-09
- Status: IN_PROGRESS
- Owner Li, Executor/Reviewer ChatGPT
- Frozen source TASK-0006 official regular raw, previously verified TASK-0015 NDJSON.
- Live source TASK-0017 newly bounded official-only SQLite, **read-only**; service untouched.
## Frozen rules
1. Compare previous chronological snapshot of each (fixture,pool) to current: strict quote-state signatures include handicap line, price cells, price flags. An event requires signature difference. A full raw digest returning to a previously seen SHA-256 is 'payload replay' (not proof upstream replay cause).
2. A→B→A based on contiguous *state changes*, first distinguish whether transition coincides with known prior full raw digest; separately count clock regression, quote-only changes and simultaneous pool transitions for same capture/fixture.
3. Report total fixtures and unique raw SHA vs capture multiplicity, rows/price states, live collection continuity and fixture diversity. No profit claims, no business logic changes, no assumption source timestamps monotonic.
4. Independent recheck of critical replay counts via a distinct algorithm, run tests and archive exact command+hashes. Submit REPORT/REVIEW and push.
5. No new capture, service change, account access, payments or bets.
