# TASK-0005 — Cloud prospective collector build + deployment qualification

- Task ID: TASK-0005
- Status: REVIEW
- Owner: Li
- Reviewer: ChatGPT
- Executor: WorkBuddy
- Risk: Medium
- Type: collector engineering / cloud deployment qualification
- Depends on: TASK-0004 = ACCEPTED
- Cloud SSH alias: `evlab-cloud`
- Formal research data: **NO — TASK-0005 data are qualification-only and must not be used as D01-B evidence**

## 1. Objective

Build, test and deploy a small unattended collector that can continuously capture:

1. official Sporttery current football quotes; and
2. BetExplorer current/pre-match 1X2 quotes as a labelled `reference_proxy`;

with strict point-in-time provenance.

The collector must run unattended on the Owner's trial Ubuntu cloud server and survive the WorkBuddy/SSH session ending.

**TASK-0005 is only the engineering qualification gate.**

Do **not** run the formal 5-day prospective study yet. After Reviewer accepts this task, a separate TASK-0006 will start a fresh sealed dataset for the multi-day pilot.

## 2. Why this task exists

TASK-0004 established:

- synchronized Sporttery + external-reference observation is feasible;
- Sporttery official data expose per-pool provider update timestamps and per-pool executability facts;
- BetExplorer can supply current 1X2 observations as `reference_proxy`;
- BetExplorer does **not** expose a provider-side quote-update timestamp;
- D01-B therefore remains unresolved.

The next research design is observation-based:

For each BetExplorer event, if the observed 1X2 tuple changes between two successful observations,

`change_time ∈ (previous_response_received_at, current_response_received_at]`.

At the moment the new reference quote becomes known to us, the collector must immediately obtain a fresh Sporttery confirmation snapshot. Later analysis can then ask whether the corresponding Sporttery HAD quote was still old and provider-declared sellable.

This task does **not** decide whether such an event is profitable or even economically meaningful.

## 3. Mandatory reading before work

Synchronize `origin/main` first, per `COLLABORATION.md`, then read in full:

1. `COLLABORATION.md`
2. `TASKS/TASK-0005-cloud-prospective-collector-qualification.md`
3. `REVIEWS/TASK-0004.md`
4. `REPORTS/TASK-0004.md`
5. `REVIEWS/SCRAPLING-EVALUATION-20260924.md`
6. `docs/data-policy.md`
7. `src/football_betting/data/sporttery_webapi.py`
8. legacy BetExplorer evidence, especially:
   - `history/_review/05_脚本_scripts/scripts/fetch_betexplorer.py`
   - the TASK-0004 homepage/current-page parsing notes.

GitHub `origin/main` is authoritative.

## 4. Fixed research/collection scope

### 4.1 Markets

For cross-source comparison, collect only:

- Sporttery **HAD / standard 1X2**;
- BetExplorer **standard 1X2**.

Sporttery may retain other pools already present in the official payload, but TASK-0005 must not invent cross-market equivalence between HAD and handicap/TTG/CRS/HAFU.

### 4.2 Sources

Primary pair:

- Sporttery official `getMatchCalculatorV1.qry`;
- BetExplorer current/pre-match page, labelled exactly `reference_proxy`.

Continue sending the normal same-site Sporttery header:

`Referer: https://www.sporttery.cn/`

even though one cloud reconnaissance observation reported HTTP 200 without it. That cloud observation is an environment note, **not** a reason to change the accepted collector contract.

500.com is **not** part of the primary TASK-0005 loop. It may be used only in a bounded diagnostic if the official Sporttery source fails, and any such use must be reported. Do not silently substitute it.

### 4.3 Cadence

Target one regular round every **60 seconds, start-to-start**.

Requirements:

- launch Sporttery and BetExplorer regular requests concurrently;
- never overlap two regular rounds;
- if a round runs longer than 60 seconds, start the next round after the previous round completes and record scheduler lag; do not create request piles;
- record source-specific request start and response receive times.

BetExplorer was observed once from this cloud server with ~45 s latency. The design must tolerate this without falsifying synchronization.

### 4.4 Reference-change confirmation

Maintain the previous successful BetExplorer observation by stable BetExplorer event identity.

When any event's valid 1X2 tuple changes:

1. persist the previous and new tuple;
2. persist:
   - `previous_response_received_at`
   - `current_response_received_at`
   - the implied change interval;
3. immediately launch one extra official Sporttery confirmation fetch;
4. mark that Sporttery capture as `change_confirmation`, distinct from a regular round;
5. do not claim the exact BetExplorer provider change time.

No threshold is required. Any actual tuple change is an observation event.

## 5. Time semantics — blocking requirement

Every HTTP observation must distinguish at least:

- `request_started_at`
- `response_received_at`
- `latency_ms`

All timestamps must be timezone-aware.

For Sporttery also preserve:

- the accepted per-pool provider timestamps from TASK-0004;
- `observed_at` / collector time semantics without overwriting provider time;
- per-pool availability/status.

For BetExplorer:

- our response receive time is the time the quote becomes knowable to this system;
- do not invent `source_updated_at`;
- do not label our timestamp as provider update time.

A slow response is not known at request start.

## 6. Storage design

Use only standard-library runtime dependencies unless there is a strong blocking reason.

Preferred durable layout on cloud:

- code clone: `/home/ubuntu/football-betting-research`
- runtime data root: `/home/ubuntu/evlab-data/task0005/`
- SQLite ledger: under that data root
- raw captures: under that data root, preferably gzip-compressed
- logs/health: under that data root

The runtime-data directory must be outside the Git working tree.

Minimum persisted evidence:

### Capture ledger

- unique capture/round ID
- capture kind: `regular` or `change_confirmation`
- source
- request URL/source identity
- request_started_at
- response_received_at
- latency_ms
- HTTP status or failure class
- raw byte length
- raw SHA-256
- raw file path if body captured
- parser/collector version
- deployed Git commit

### Sporttery normalized facts

At minimum retain what TASK-0004 already validated:

- match ID
- full `matchNumStr`
- teams / league
- kickoff
- HAD odds
- HAD provider update time
- HAD `bettingSingle`
- HAD `bettingAllup`
- HAD `poolStatus`
- close date/time when present
- collector response time
- raw hash

Other pools may be retained without being used as TASK-0005 comparison markets.

### BetExplorer normalized facts

At minimum:

- stable provider event URL/ID
- competition/group when available
- home / away
- kickoff with timezone or explicit parse status
- 1X2 decimal odds
- response_received_at
- raw hash
- parser status
- duplicate-collapse status

Do not guess a fixture identity if the page is ambiguous.

### Reference-change ledger

At minimum:

- event ID
- previous odds tuple
- current odds tuple
- previous response time
- current response time
- generated change interval
- ID of the immediately triggered Sporttery confirmation capture

## 7. Raw-data discipline

- Raw captures are append-only.
- Never edit a raw capture in place.
- Do not commit raw HTML/JSON/SQLite/CSV to Git.
- Do not silently discard decoding/parser failures.
- Keep raw byte hash even when parsing fails.
- Follow the mixed-encoding / identifier rules in `docs/data-policy.md`.
- BetExplorer parser must handle its actual current-page dialect and desktop/mobile duplicates without silently double-counting.

TASK-0005 qualification data must be marked:

`dataset_phase = QUALIFICATION`

It is **not** eligible for future research conclusions. TASK-0006 will start a fresh sealed prospective phase after Reviewer acceptance.

## 8. Cloud deployment

Target:

`ssh evlab-cloud`

Known verified facts:

- SSH connectivity is already working;
- remote user: `ubuntu`;
- host reports Ubuntu 24.04;
- no inbound web port is required.

### Authorized cloud changes

WorkBuddy may:

- clone/pull this repository under `/home/ubuntu`;
- create `/home/ubuntu/evlab-data/task0005/`;
- use the existing Python 3 runtime;
- create a Python venv if useful;
- install only `git` and/or Python venv support via the OS package manager **if genuinely missing**;
- create exactly one dedicated process-supervision unit for TASK-0005, preferably systemd, running as user `ubuntu`;
- use `sudo` only for that bounded service/package setup if non-interactive sudo is already available.

The deployed service must record the exact Git commit it runs.

### Forbidden cloud changes

Do not:

- change firewall/security-group rules;
- open ports 80/443 or any new inbound port;
- create public dashboards/APIs;
- install Docker unless separately authorized;
- install Scrapling/Playwright/browser stacks;
- install proxy/VPN software;
- rotate IPs/proxies;
- solve/bypass WAF challenges;
- create external accounts;
- alter SSH authorized keys except what Owner already configured;
- change cloud billing/instance plan;
- touch snapshots;
- store secrets in Git or logs.

If root/sudo access beyond the explicitly allowed bounded setup is required, stop and report instead of expanding scope.

## 9. Process supervision requirements

The collector must:

- continue after the SSH/WorkBuddy session ends;
- have an inspectable status;
- write stdout/stderr or structured logs to durable storage;
- fail loudly, not silently;
- recover from transient HTTP failures with bounded backoff;
- avoid a tight retry loop;
- never overlap regular rounds;
- restart safely without overwriting existing ledger/raw data.

No requirement to auto-start after an entire VM reboot in TASK-0005 if enabling that would require broader system changes; if it can be done safely within the dedicated service authorization, record it.

## 10. Required implementation tests

At minimum add deterministic tests for:

1. BetExplorer current-page 1X2 parsing;
2. desktop/mobile duplicate collapse;
3. ambiguous/invalid fixture rows fail closed;
4. request/response clocks remain distinct;
5. BetExplorer provider update time is absent, not invented;
6. reference change interval generation;
7. a changed reference tuple triggers exactly one Sporttery confirmation request;
8. unchanged reference tuple triggers no confirmation;
9. restart/ledger idempotency or equivalent no-overwrite guarantee;
10. raw-hash/provenance recording.

Existing Sporttery TASK-0004 tests must continue to pass.

## 11. Qualification run

After local tests pass and deployment is complete, run a **minimum 30-minute cloud qualification soak**, with:

- at least **20 attempted regular rounds**;
- service left unattended during the soak;
- process still healthy at the end;
- no overlapping-round bug;
- no silent crash;
- both source success/failure counts reported;
- latency distribution/report for both sources;
- scheduler-lag count reported;
- parsed fixture counts reported;
- any detected BetExplorer change events reported honestly;
- if zero changes occur, that is fine — do not manufacture a change.

Perform one controlled service restart during qualification and verify that:

- previous ledger/raw data remain intact;
- new captures append rather than overwrite;
- deployed commit identity remains explicit.

TASK-0005 does not require a real reference price change to occur.

## 12. Reviewer access requirement

Leave enough ordinary read access under the `ubuntu` account that Reviewer can independently SSH through `evlab-cloud` and inspect:

- service status;
- deployed commit;
- logs;
- SQLite schema/counts;
- raw hashes/files;
- timing evidence.

Do not weaken filesystem permissions merely for Reviewer convenience.

## 13. Allowed repository changes

Only files necessary for this task, expected to include:

- `TASKS/TASK-0005-cloud-prospective-collector-qualification.md` — status only after this task is created;
- `REPORTS/TASK-0005.md`;
- minimal BetExplorer provider/parser code;
- minimal prospective collector/runtime code;
- tests for those modules;
- a minimal versioned service/unit template or deployment note if needed.

Do not modify TASK-0004 or its accepted review.

Do not modify research conclusions / Edge Exhaustion Matrix in TASK-0005.

## 14. Forbidden research actions

Do not:

- calculate betting EV or ROI;
- run profitability backtests;
- tune thresholds;
- create BUY/PASS recommendations;
- rank leagues/markets by profitability;
- fit prediction models;
- infer edge from the qualification sample;
- call BetExplorer Pinnacle/Betfair/sharp when it is only the accepted `reference_proxy`;
- use qualification data as formal D01-B evidence.

## 15. Required report

Create:

`REPORTS/TASK-0005.md`

Include:

- starting HEAD;
- exact changed files;
- architecture/data-flow summary;
- timestamp semantics;
- SQLite/schema summary;
- raw-storage layout;
- source URLs/types and labels;
- tests run and results;
- cloud deployment path;
- service name/status;
- deployed commit;
- qualification start/end;
- attempted/successful rounds per source;
- latency summary;
- scheduler lag/overlap observations;
- parsed fixture counts;
- change-event count and confirmation count;
- restart test result;
- disk use / five-day projected disk use;
- exact blockers/limitations;
- security/boundary self-check;
- Git commit and push result.

Do not include passwords, private keys, cookies, tokens, or other credentials.

## 16. Acceptance criteria

Reviewer may ACCEPT only if all are true:

1. code and tests are committed/pushed;
2. existing full test suite still passes;
3. lint passes;
4. collector is demonstrably running on `evlab-cloud`;
5. at least 20 qualification regular rounds exist over at least 30 minutes;
6. request-start / response-receive timing is preserved per source;
7. Sporttery per-pool provider time and executability remain preserved;
8. BetExplorer provider time is not fabricated;
9. change detection and immediate Sporttery confirmation are tested;
10. restart append-safety is demonstrated;
11. raw/provenance hashes are retained;
12. qualification dataset is explicitly separated from future sealed research data;
13. no access-boundary or secret-handling violation occurred;
14. Reviewer can independently inspect the cloud artifacts over SSH.

## 17. Completion

When implementation + qualification are complete:

1. change status `IN_PROGRESS -> REVIEW`;
2. finish `REPORTS/TASK-0005.md`;
3. inspect diff/status and confirm only authorized repository paths changed;
4. commit and push `origin/main`;
5. leave the collector/service in a safe running state unless doing so would be harmful;
6. **STOP**.

Do not start the 5-day formal pilot.

Owner completion message must be short:

- TASK-0005
- status = REVIEW
- pushed commit
- report path
- cloud service status
- one-line qualification result

After Reviewer ACCEPTS TASK-0005, Reviewer will create TASK-0006 for the sealed multi-day prospective capture.
