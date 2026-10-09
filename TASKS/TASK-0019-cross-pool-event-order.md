# TASK-0019 — Official five-pool event ordering and timestamp integrity
- Status: ACCEPTED
- Date: 2026-10-09
- Owner Li; Executor/Reviewer ChatGPT
- Source frozen TASK-0006 only, TASK-0015 NDJSON independently verified under TASK-0018.
## Frozen analysis contract
1. For each (match_id,pool) order snapshots by capture_id. State includes (line, full prices, per-selection flags). Emit event only when state differs from prior observed state. Do not treat 92,935 sampled rows as independent events.
2. Compare provider_update_date/time among successive events: count backwards, unchanged, forwards, invalid; compare distinct pools' event clocks and first observed events. A one-off timestamp lead does not establish causal actionable lag.
3. Define immediate state reversion A→B→A within 3 consecutive *state changes* as backtracking indicator, report matches with any reversion. Do not tune threshold from result.
4. Cross-pool temporal ordering: for each unique fixture, compare median provider-clock timestamp of deduplicated price-change events by pool where both have >=2 events and parseable clocks. No significance/predictive claims unless ample distinct fixtures; report pairwise eligible denominators, tie shares, order shares only descriptive.
5. Independently recompute event totals and time regression checks from raw/source via separate algorithm; run tests. Write summary, report and review; commit and push. Never modify active TASK-0017 or frozen raw; no wagering/ROI.
