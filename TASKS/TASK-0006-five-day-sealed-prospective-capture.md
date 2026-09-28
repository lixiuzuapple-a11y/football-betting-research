# TASK-0006 — Five-day sealed prospective D01-B capture

- Task ID: TASK-0006
- Status: TODO
- Owner: Li
- Reviewer: ChatGPT
- Executor: WorkBuddy
- Risk: Medium
- Type: prospective sealed data collection / cloud operation
- Depends on: TASK-0005 = ACCEPTED
- Cloud SSH alias: `evlab-cloud`
- Formal dataset phase: `PROSPECTIVE_SEALED`
- Planned study duration: **120 consecutive wall-clock hours**
- Primary research question: **Does a reference-proxy price move become observable while the corresponding Sporttery HAD quote remains provider-declared sellable at its prior state?**
- Research result in this task: **NONE — capture only; no D01-B analysis during the run**

## 1. Objective

Turn the TASK-0005-qualified collector into a **sealed prospective acquisition run** lasting five days.

The run must collect all eligible current observations from:

1. official Sporttery football HAD / standard 1X2; and
2. BetExplorer homepage standard 1X2, still labelled exactly `reference_proxy`;

while preserving:

- raw bytes and SHA-256;
- request-start and response-receive clocks;
- Sporttery provider-side HAD update time;
- Sporttery per-pool executability facts;
- BetExplorer declared page variant;
- accepted same-variant reference changes;
- one immediate Sporttery confirmation snapshot per BetExplorer capture that carries one or more accepted changes.

**TASK-0006 is an acquisition task, not an analysis task.**

No one may inspect the captured odds/change outcomes during the run for research conclusions, rule changes, market selection, threshold tuning, or early stopping.

## 2. Experimental discipline

This run is **prospective and sealed**.

Once the formal run starts:

- the collector code is frozen;
- the data schema is frozen;
- the source pair is frozen;
- the 60-second target cadence is frozen;
- the declared-variant rule is frozen;
- the change rule is frozen;
- the 120-hour wall-clock end time is frozen.

The run must **not** be stopped early because the data look uninteresting, interesting, profitable, unprofitable, noisy, sparse, or promising.

The only permitted reasons to interrupt the run are operational/safety failures defined in §13.

Qualification data from TASK-0005 are permanently excluded from formal TASK-0006 evidence.

## 3. Mandatory reading

Before any change or cloud action, synchronize `origin/main` and read:

1. `COLLABORATION.md`
2. this task
3. `TASKS/TASK-0005-cloud-prospective-collector-qualification.md`
4. `REVIEWS/TASK-0005.md` — especially the final ACCEPTED section
5. `REPORTS/TASK-0005.md`
6. `REVIEWS/SCRAPLING-EVALUATION-20260924.md`
7. `docs/data-policy.md`
8. current collector / ledger / BetExplorer provider code and tests

Do not repeat TASK-0004/TASK-0005 source reconnaissance unless a new operational failure makes it strictly necessary.

## 4. Frozen source/market semantics

### 4.1 Sporttery

Use the already accepted official endpoint and ordinary same-site request context.

For HAD preserve at minimum:

- match ID;
- full `matchNumStr`;
- teams / league;
- kickoff;
- HAD odds;
- HAD provider update time;
- `bettingSingle`;
- `bettingAllup`;
- `poolStatus`;
- close date/time when present;
- collector request/receive clocks;
- raw hash.

No handicap/TTG/CRS/HAFU equivalence may be invented for this experiment.

### 4.2 BetExplorer

BetExplorer remains:

`reference_proxy`

It is **not** to be described as Pinnacle, Betfair, a named sharp bookmaker, or a provider-timestamped sharp feed.

The accepted TASK-0005 rule remains frozen:

- parse the page-declared variant tokens;
- compare price only like-for-like within the same declared variant;
- record variant switches separately;
- a variant transition is not a market move;
- no averaging across variants;
- no movement threshold;
- no small-move suppression;
- no invented provider update time.

### 4.3 Accepted reference change

A reference change exists only when the same `event_id` under the same declared `source_variant` has a different valid 1X2 tuple than its previous successful observation.

Its honest time bracket remains:

`change_time ∈ (previous_response_received_at, current_response_received_at]`

The upper bound is the BetExplorer response-receive time that carried the new tuple.

## 5. Minimal pre-run code changes required

TASK-0005 hard-coded qualification semantics. Before the formal run, make only the minimum changes needed for a sealed phase.

### 5.1 Dataset phase must be configurable and explicit

Add an explicit runtime dataset phase, e.g. CLI/config:

`--dataset-phase PROSPECTIVE_SEALED`

Requirements:

- default behavior for old qualification tests may remain `QUALIFICATION`;
- TASK-0006 service must explicitly pass `PROSPECTIVE_SEALED`;
- every formal row in all relevant tables must carry exactly `PROSPECTIVE_SEALED`;
- no TASK-0005 qualification row may be copied or migrated into the new root.

### 5.2 Sealed-run manifest

Create one immutable run manifest in the new data root before collection begins, e.g.:

`RUN_MANIFEST.json`

At minimum record:

- task ID;
- run ID;
- dataset phase;
- exact frozen Git commit;
- collector/parser version;
- data root;
- cloud hostname;
- planned start UTC;
- planned end UTC = start + 120h;
- source labels/endpoints;
- cadence;
- HTTP timeout;
- schema version/hash if available;
- service/unit name;
- statement that analysis is sealed until completion.

The manifest must not contain secrets.

Once the first formal capture is written, do not edit the manifest except for a clearly separate append-only completion record.

### 5.3 Absolute end time must survive process restart

The 120-hour end is **wall-clock**, not “120 hours of process uptime.”

A restart must not reset the experiment duration.

Implement one robust mechanism such that the service/process knows the immutable planned end UTC and stops cleanly at or after that time.

Acceptable examples:

- collector reads immutable `planned_end_utc` from the run manifest; or
- an equivalent persisted absolute stop deadline.

Do not implement the run as a counter that restarts from zero after process restart.

### 5.4 Restart-safe reference baseline

Before entering formal mode, make the accepted change detector restart-safe.

On process restart within the same TASK-0006 data root:

- hydrate the latest successful BetExplorer observation for each `(source_variant, event_id)` from the ledger;
- restore the prior successful variant/capture context needed to record variant transitions correctly;
- do not silently reset all reference baselines.

A real price change that occurred across a short process restart should therefore be bracketed by the last successful pre-restart observation and first successful post-restart observation.

The long interval remains visible in the timestamps; do not invent a tighter change time.

Add deterministic restart regression tests.

### 5.5 Sealed-mode logging

Formal service logs must be operational, not research-result feeds.

During `PROSPECTIVE_SEALED`:

Allowed log/health information:

- service start/stop;
- round ID;
- source request success/failure;
- latency;
- parser success/failure counts;
- scheduler lag;
- disk/runtime errors;
- current UTC and last successful capture time.

Do **not** print to ordinary logs:

- odds values;
- event-level change identities;
- number of accepted reference changes in a round;
- confirmation-trigger reason/event list;
- inferred stale windows;
- EV/ROI or any research conclusion.

The database/raw files may and should store the formal evidence; ordinary health logs should not unseal it.

## 6. Fresh sealed data root

Create a brand-new data root outside Git, following:

`/home/ubuntu/evlab-data/task0006-sealed-<RUN_ID>/`

Requirements:

- root must not contain any prior captures at formal start;
- TASK-0005 roots remain untouched:
  - `/home/ubuntu/evlab-data/task0005`
  - `/home/ubuntu/evlab-data/task0005-corrected`
- formal TASK-0006 service must point only at the new root;
- raw files, SQLite, logs and manifest stay outside Git;
- record exact path in `REPORTS/TASK-0006.md`.

Before starting, verify the new ledger contains zero capture rows.

## 7. Frozen deployment commit

The formal run must execute one exact Git commit.

Workflow:

1. implement only §5 changes + tests + TASK-0006 service/template/report scaffolding;
2. run full tests + Ruff;
3. commit/push;
4. record that exact commit as the **frozen run commit**;
5. deploy exactly that commit to `evlab-cloud`;
6. verify cloud `git rev-parse HEAD` equals the frozen commit and worktree is clean;
7. start the sealed run.

After first formal capture:

**no code changes may be deployed into that run.**

If a code defect requires a patch, follow §13 and invalidate/stop the run rather than hot-patching it.

## 8. Formal service

Use a dedicated formal service, preferably:

`evlab-task0006.service`

Do not repurpose the TASK-0005 unit in a way that obscures history.

Requirements:

- user/group = `ubuntu`;
- no new inbound network ports;
- no Docker;
- no browser automation;
- no Scrapling;
- no proxy/VPN/IP rotation;
- no WAF/access-control bypass;
- no credentials in the unit/repo/logs;
- `Restart=on-failure` with the already validated bounded restart policy;
- explicit `PROSPECTIVE_SEALED` phase;
- explicit fresh data root;
- explicit frozen deployed commit;
- explicit immutable planned end UTC/run manifest.

TASK-0005 service should remain stopped/disabled.

## 9. Cadence

Keep the accepted collector contract:

- target one regular round every **60 seconds, start-to-start**;
- Sporttery and BetExplorer regular legs launch concurrently;
- regular rounds never overlap;
- if a round lasts >60 s, the next starts only after completion;
- record scheduler lag honestly;
- BetExplorer slow responses are not backdated to request start.

Do not change cadence during the run.

## 10. Confirmation behavior

Keep TASK-0005 accepted F4 behavior:

- 0 accepted changes in one BetExplorer capture -> 0 confirmation fetches;
- 1 accepted change -> 1 Sporttery confirmation fetch;
- N accepted changes in the same BetExplorer capture -> **still exactly 1** Sporttery confirmation fetch;
- all N change rows link to the same confirmation capture;
- confirmation is launched immediately after the BetExplorer result becomes available and accepted changes are identified.

A failed confirmation remains a failed capture; do not fabricate or retry it in a way that changes event timing. Normal future rounds continue.

## 11. What may be monitored during the five days

The run is sealed, but operations may be monitored.

Permitted health checks:

- service active/inactive;
- process PID/restart count;
- last capture timestamp;
- total capture rows;
- total source successes/failures;
- HTTP/decode/parser failure counts;
- round cadence / scheduler lag;
- disk space;
- SQLite integrity;
- raw-file write success;
- deployed commit;
- phase label;
- cloud worktree cleanliness.

Do **not** query/report during the run:

- odds;
- specific fixtures because they moved;
- reference-change counts;
- variant-specific price differences;
- confirmation counts as a proxy for changes;
- stale-window candidates;
- D01-B results;
- EV/profitability.

Operational monitoring must not become iterative research.

## 12. Health report

Create a small operational health command/script if useful.

It must expose only the permitted fields in §11.

A health check must never require opening or printing market values.

No public dashboard or inbound port is allowed.

## 13. Failure policy — frozen before start

### 13.1 Non-fatal operational faults

Examples:

- transient HTTP failure;
- short source timeout;
- isolated parser/decode failure;
- normal systemd process restart;
- temporary scheduler lag.

Action:

- record honestly;
- allow the unchanged frozen service to continue;
- do not extend/restart the 120-hour clock.

### 13.2 Fatal/invalidation faults

Examples:

- collector code must change;
- schema must change;
- phase label is wrong;
- formal root accidentally contains prior data;
- frozen commit cannot be verified;
- service points to wrong root;
- secrets/access boundary violation;
- persistent corruption makes evidence unreliable.

Action:

1. stop formal service;
2. preserve the entire failed root untouched;
3. mark run `INVALIDATED` in the report/completion metadata;
4. do not delete/rewrite failed evidence;
5. do not restart a “fixed” formal run under the same run ID/root;
6. return to Reviewer for a new sealed-run authorization.

### 13.3 No outcome-based stopping

The following are **never** valid stop reasons:

- zero changes;
- too many changes;
- no apparent stale window;
- attractive stale window;
- apparent edge;
- poor-looking data;
- “enough examples already.”

## 14. No live analysis

During TASK-0006 do not:

- compute D01-B candidate windows;
- join specific BetExplorer changes to Sporttery confirmations for interpretation;
- calculate EV/ROI/CLV;
- tune thresholds;
- rank leagues/markets;
- create BUY/PASS;
- fit prediction models;
- search for profitable subsets;
- manually inspect interesting change events;
- alter collection because of observed outcomes.

This applies to WorkBuddy and to any helper script created for operations.

Formal analysis starts only after the sealed run is complete and Reviewer explicitly opens the dataset in a later task.

## 15. End-of-run procedure

At or after immutable `planned_end_utc`:

1. collector stops cleanly;
2. leave TASK-0006 service inactive/disabled;
3. checkpoint/flush SQLite;
4. do **not** analyze market content;
5. compute a run-level integrity manifest with:
   - run ID;
   - frozen commit;
   - actual first/last capture UTC;
   - planned start/end UTC;
   - total captures;
   - source success/failure counts;
   - phase distribution;
   - distinct round/session counts;
   - raw file count;
   - total disk bytes;
   - SQLite file hash;
   - raw-manifest hash / equivalent reproducibility digest;
   - service restart count if available;
   - operational downtime/gap summary;
6. preserve root read-only in practice: no content rewrites/deletions;
7. update `REPORTS/TASK-0006.md`;
8. set TASK status to `REVIEW`;
9. commit/push report/status only;
10. STOP.

Do not create the D01-B analysis task yourself.

## 16. Pre-start verification Gate

Before starting the 120-hour clock, WorkBuddy must prove all of the following:

- full test suite passes;
- Ruff passes;
- TASK-0005 service is inactive/disabled;
- TASK-0006 unit verifies with systemd;
- cloud repo is at frozen commit and clean;
- formal data root is new;
- formal ledger has 0 captures;
- phase is configured as `PROSPECTIVE_SEALED`;
- run manifest exists and planned end = planned start + 120h;
- restart-baseline hydration tests pass;
- sealed-mode log tests pass;
- no forbidden dependency/tool/network change occurred.

Only after all checks pass may the formal service start.

## 17. Required tests

Add deterministic tests for at least:

1. `PROSPECTIVE_SEALED` phase is persisted across all formal tables;
2. qualification remains the default/legacy behavior where expected;
3. planned end UTC survives process restart and does not slide;
4. collector refuses or exits after the immutable planned end;
5. restart hydrates prior `(source_variant,event_id)` baseline correctly;
6. a same-variant price change across a restart is detectable with the honest wide interval;
7. variant transition semantics still do not create reference changes;
8. 0/1/N confirmation behavior remains correct;
9. sealed-mode logs do not emit odds;
10. sealed-mode logs do not emit event-level change details or change counts;
11. fresh-root/phase guard fails closed on incompatible/pre-existing formal state;
12. all TASK-0005 regression tests remain passing.

## 18. Allowed repository changes

Expected/authorized:

- `TASKS/TASK-0006-five-day-sealed-prospective-capture.md` — status only after creation;
- `REPORTS/TASK-0006.md`;
- minimal collector/config/ledger changes required by §5;
- tests;
- one TASK-0006 systemd unit/template;
- minimal health command/script if needed;
- documentation strictly required to explain formal run operation.

Do not alter TASK-0004/TASK-0005 accepted conclusions.

Do not edit historical evidence to make TASK-0006 look cleaner.

## 19. Required report — staged, not analytical

Create:

`REPORTS/TASK-0006.md`

### Before start, record

- starting HEAD;
- changed files;
- tests/lint;
- frozen run commit;
- data root;
- run ID;
- manifest path/hash;
- planned start/end UTC;
- service name;
- phase;
- pre-start zero-row proof;
- cloud git/status proof;
- boundary self-check.

### During run

Only append operational incidents if necessary.

Do not append market outcome interpretation.

### At completion

Append only the integrity/operations summary in §15.

Do not report D01-B candidate events or price values.

## 20. Acceptance criteria

Reviewer may accept TASK-0006 acquisition only if:

1. one frozen commit ran the formal dataset;
2. phase is `PROSPECTIVE_SEALED` everywhere;
3. formal root was fresh;
4. planned duration was exactly 120 wall-clock hours and did not slide across restart;
5. any interruption is honestly recorded;
6. no hot patch occurred after first capture;
7. raw/hash/timing provenance is intact;
8. restart-safe baseline semantics were active;
9. sealed logging/monitoring rules were respected;
10. no forbidden research analysis occurred during collection;
11. end-of-run integrity manifest exists;
12. cloud and Git artifacts are independently inspectable;
13. service is stopped after completion;
14. no TASK-0005 qualification rows were promoted into the sealed dataset.

Acceptance of TASK-0006 means only:

> **the prospective sealed dataset is valid enough to open for a separately authorized analysis.**

It does not mean D01-B exists.

## 21. Completion message

When the formal run has ended and the report/status are pushed, send Owner only:

- TASK-0006
- status = REVIEW
- run ID
- frozen commit
- planned/actual start-end
- report path
- one-line operational integrity result

Do not include odds, change-event counts, stale candidates, EV, or conclusions in the completion message.

## 22. Stop condition for WorkBuddy

After pushing TASK-0006 status `REVIEW` at the end of the sealed run:

**STOP.**

Do not open/analyze the sealed market data.

Do not create TASK-0007.

Reviewer will independently verify the cloud root and decide whether/when to unseal it.
