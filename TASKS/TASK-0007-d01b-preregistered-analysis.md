# TASK-0007 — D01-B pre-registered prospective lead-lag analysis

- Task ID: TASK-0007
- Status: IN_PROGRESS
- Owner: Li
- Lead / Executor / Reviewer-of-record: ChatGPT
- Dataset: TASK-0006 run `20260928a`
- Evidence grade entering task: **prospective acquisition valid / strict seal defective**
- Frozen input root: `/home/ubuntu/evlab-data/task0006-sealed-20260928a`
- Input collector commit: `9e8fbc1368859df4be08148585257e9639c10517`
- Analysis code: must be versioned in this repository before result interpretation.
- Scope: D01-B only. No B01, no ROI backtest, no outcome settlement, no BUY/PASS.

## 1. Question

Test the already-defined D01-B mechanism on the preserved prospective dataset:

> After a same-variant `reference_proxy` 1X2 price change is observed, is the corresponding official Sporttery HAD quote still observable at its prior state **and** still provider-declared executable?

This task does **not** assume that BetExplorer is Pinnacle, Betfair, a named sharp bookmaker, or true fair probability.

## 2. Known information before preregistration

Before this task was created, closure/audit had already disclosed acquisition-level aggregates including total captures/rounds/raw files and aggregate counts of reference-change / confirmation activity.

The following were **not** inspected before this task was committed:

- event-level reference changes;
- event identities associated with changes;
- previous/current odds tuples;
- Sporttery quote values around a change;
- candidate stale windows;
- event-level proxy-implied EV;
- rankings by league/team/market;
- match outcomes.

The analysis rules below must not be changed merely because the opened data look convenient or inconvenient.

## 3. Reuse-first inventory

Reuse before writing new logic:

1. `src/football_betting/prospective/ledger.py` — canonical schema and timing fields.
2. `src/football_betting/data/betexplorer.py` — reference variant/event semantics.
3. `src/football_betting/data/sporttery_webapi.py` — HAD provider time and executability semantics.
4. `src/football_betting/odds/implied.py` — implied probability / multiplicative devig / conditional EV arithmetic.
5. `history/_review/05_脚本_scripts/scripts/team_map_index.py` and `history/_review/18_data_其他派生素材/data/team_name_map.json` — legacy team identity asset.
6. Historical pairing lessons in `pair_markets.py`: fail closed on ambiguous identity; never use post-kickoff/future information; do not pair by arbitrary first match.

Any reusable new matching/analysis helper created here must be promoted into tracked source/tests, not left as a one-off shell snippet.

## 4. External-method reconnaissance

Existing market microstructure / betting-market work supports studying cross-market price discovery with matched, timestamped observations and lead-lag/event-study methods. It also shows that exchange and bookmaker markets can differ in information aggregation and liquidity.

For this task the methodological import is limited to:

- preserve actual observation order;
- treat latency windows explicitly;
- compare matched contracts only;
- do not infer provider update times that were not observed;
- do not treat a reference proxy as a named sharp source.

No external paper supplies the result of TASK-0007.

## 5. Identity matching — frozen before event-level result opening

Matching must be independent of odds movement.

### 5.1 Build the crosswalk from the full captured fixture universe

Use **all** BetExplorer fixture identities and **all** Sporttery fixture identities in the five-day dataset, not only events that later appear in `reference_changes`.

Allowed identity inputs:

- home/away names;
- existing versioned team-name map / aliases;
- provider event/match IDs;
- advertised kickoff time;
- league identity when defensible from existing mappings.

Forbidden for identity matching:

- odds values;
- change frequency;
- proxy-implied EV;
- result/outcome;
- “this pairing gives a nicer signal”.

### 5.2 Conservative matching rule

Primary automatic match requires:

1. mapped home identity agrees;
2. mapped away identity agrees;
3. home/away direction agrees;
4. absolute kickoff difference <= **15 minutes** after converting Sporttery Beijing time to UTC;
5. exactly one Sporttery match satisfies the pair.

If zero or >1 candidates remain, primary mapping = unmatched/ambiguous.

No fuzzy string distance by itself may force a match.

### 5.3 Identity-only supplementation

If the legacy map misses current teams, an identity-only crosswalk may be added **after TASK-0007 commit but before any analytic join** using the full fixture universe and public/current schedule identity only.

Every manual/added alias must be versioned with provenance. It must not use odds or whether the fixture changed.

Report mapping coverage before D01-B interpretation.

## 6. Reference-change semantics

Use only existing `reference_changes` rows, which already mean:

- same BetExplorer `event_id`;
- same declared `source_variant`;
- valid previous/current 1X2 tuple;
- tuple changed;
- honest interval:
  `(previous_response_received_at, current_response_received_at]`.

Do not manufacture cross-variant changes.

The task must also report source-quality diagnostics before interpreting stale-price candidates:

- changes per confirmation/round batch;
- distribution of batch size;
- distinct changed events;
- variant distribution;
- one-step/rapid reversion diagnostics where measurable.

Pre-registered batch strata:

- 1
- 2–5
- 6–20
- >20 changes per confirmation capture.

`batch_size=1` is the strongest source-quality stratum; `<=5` is a sensitivity stratum. Large synchronized batches are reported, not silently filtered away.

## 7. Primary stale-executable definition

For each uniquely matched reference-change row:

### 7.1 Pre-change Sporttery baseline

Find the latest successful Sporttery observation of the matched Sporttery `match_id` with capture `response_received_at <= previous_response_received_at`.

Require:

- valid HAD H/D/A tuple;
- non-null HAD provider update timestamp.

This is the baseline known no later than the **lower bound** of the reference-change interval.

If absent, primary status = not analyzable.

### 7.2 Post-change confirmation

Use the `confirmation_capture_id` already linked to the reference change.

Require:

- confirmation capture exists;
- confirmation capture response time >= `current_response_received_at`;
- matched Sporttery fact exists in that capture;
- valid HAD tuple;
- non-null HAD provider update timestamp.

### 7.3 “Observed stale”

Primary stale=true only when both hold:

1. confirmation HAD tuple == pre-change baseline HAD tuple exactly;
2. confirmation HAD provider update timestamp == baseline HAD provider update timestamp exactly.

This is deliberately strict. A provider timestamp change with unchanged odds is **not** counted as primary stale.

The claim is “observed unchanged across the bracket”, not proof that no unseen update/reversion occurred between snapshots.

### 7.4 “Executable”

At confirmation time require all:

1. `had_pool_status` case-insensitively equals `Selling`;
2. at least one of `had_betting_single == 1` or `had_betting_allup == 1`;
3. if a complete parseable HAD close datetime is present, confirmation observed time <= close time.

Missing/ambiguous availability => executable status unknown, not true.

### 7.5 Primary D01-B mechanism candidate

`primary_candidate = matched AND analyzable AND stale AND executable`.

This definition is frozen before event-level results are opened.

## 8. Economic relevance — proxy only

For each reference change, convert previous/current BetExplorer 1X2 odds to multiplicatively de-vigged probabilities using the existing `odds.implied` implementation.

For each H/D/A outcome:

- `delta_q = q_current - q_previous`
- consider only outcomes with `delta_q > 0`;
- for a primary stale/executable candidate, compute:
  `proxy_implied_ev = q_current * O_sporttery_confirmation - 1`
- and:
  `change_induced_ev_gain = delta_q * O_sporttery_confirmation`.

Terminology is mandatory:

- **proxy-implied EV**, not true EV;
- **reference_proxy**, not sharp/Pinnacle/Betfair.

Pre-registered reporting thresholds for `proxy_implied_ev`:

- > 0
- >= 0.02
- >= 0.05
- >= 0.10

Report counts and distinct matched fixtures for each threshold. Do not tune thresholds after opening results.

## 9. Persistence secondary analysis

For every primary candidate, scan subsequent successful Sporttery observations of that `match_id` after the reference-change upper bound.

Measure observed time until first:

- HAD tuple changes; or
- HAD provider update timestamp changes; or
- HAD becomes provider-declared non-executable.

If none occurs before the earlier of kickoff / dataset end, mark right-censored.

This is secondary. Immediate confirmation remains the primary D01-B test.

## 10. No pseudo-replication

Report at least:

- reference-change row count;
- distinct BetExplorer event IDs;
- distinct matched Sporttery match IDs;
- distinct primary-candidate fixtures;
- distinct calendar days.

Do not use a naive row-level p-value treating thousands of changes on the same event as independent.

This task is mechanism/falsification analysis, not a significance-hunting exercise.

## 11. Pre-registered interpretation gate

### A. No mechanism evidence

If there are **zero** primary stale+executable candidates after conservative matching:
- D01-B is not demonstrated in this five-day prospective sample.

### B. Mechanism exists but economic relevance not shown

If primary candidates exist but no outcome has positive proxy-implied EV:
- stale lead-lag exists observationally;
- no reference-proxy economic candidate is shown.

### C. Economic candidate(s) exist

If at least one primary candidate has `proxy_implied_ev > 0`:
- record a **prospective reference-proxy candidate**, not a proven edge.

Strength is reported by distinct fixtures/days and by batch-quality strata; one example is not called robust.

A second strict prospective replication is justified only if the candidate pattern is not obviously dominated by:
- unmatched identity;
- large synchronized reference batches;
- one-snapshot reversions;
- non-executable Sporttery state;
- tiny/rounding-scale movement;
- or a single isolated fixture.

No profitability/positive-EV claim may be promoted solely from this dataset.

## 12. Seal-defect handling

TASK-0006 was rejected as a strict sealed run because:
- ordinary logs leaked confirmation activity;
- closure disclosed aggregate change/confirmation counts.

Carry this limitation into every TASK-0007 conclusion.

Do not use the known aggregates to tune definitions.

## 13. Implementation / reusable assets

Expected additions:

- reusable identity matching module under `src/football_betting/matching/` or equivalent;
- reusable prospective-analysis module under `src/football_betting/analysis/` or equivalent;
- a deterministic CLI/tool that reads a ledger path and writes analysis outputs;
- unit tests for matching, timing brackets, stale/executable classification, devig/EV use, batch strata, and persistence logic;
- `REPORTS/TASK-0007.md`;
- compact machine-readable outputs under `results/task0007/`.

Do not modify TASK-0006 raw data.

Analysis outputs must be written outside the sealed root.

## 14. Validation

Before interpreting results:

1. full existing test suite passes;
2. new TASK-0007 tests pass;
3. analysis code passes lint if the environment supports the repository lint tool;
4. a synthetic fixture proves the primary candidate logic end-to-end;
5. a negative synthetic fixture proves provider timestamp change blocks primary stale classification;
6. ambiguous team match fails closed;
7. same match across timezone conversion is tested;
8. analysis is deterministic on repeated runs.

## 15. Self-execution audit discipline

Because ChatGPT is both implementer and final reviewer in this task:

1. freeze this task/preregistration in Git **before** opening event-level results;
2. implement reusable code against synthetic fixtures first;
3. commit implementation/tests before running on TASK-0006;
4. run the real analysis once with the frozen analysis commit;
5. do not edit thresholds/definitions afterward;
6. independently recompute headline counts with a second, simple audit path;
7. compare both outputs;
8. preserve discrepancies rather than “fixing toward” the preferred result.

## 16. Deliverables

- `research/literature/D01B_LEAD_LAG_SCOUT_20261008.md`
- reusable analysis/matching code + tests
- `results/task0007/summary.json`
- `results/task0007/mapping_summary.json`
- `results/task0007/candidates.csv` (only after preregistration)
- `REPORTS/TASK-0007.md`
- final `REVIEWS/TASK-0007.md`

## 17. Stop/decision point

After analysis and independent audit:

- if D01-B shows no meaningful prospective candidate, close/downgrade it;
- if a credible candidate survives, define a corrected strict-seal replication task before any live betting interpretation.

No BUY/PASS or wagering automation is authorized here.
