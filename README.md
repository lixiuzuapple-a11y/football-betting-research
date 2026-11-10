# football-betting-research

Football Betting Recommendation & Research System.

Not a tipster, not a bot, and not a betting client. This is the engineering
skeleton for a reproducible, auditable pipeline that turns pre-match
information into recorded opinions and, eventually, measured results.

## What this project is

A research and recommendation system for football betting markets, built so that
every claim it makes can be traced back to the data that produced it.

The whole point is the order of operations:

```
pre-match data -> standardise -> features -> prediction -> odds / implied price
   -> value assessment -> recommendation / PASS -> record -> result
   -> post-match evaluation -> historical backtest
```

Each arrow is a layer boundary, and each layer is forbidden from reaching
across it. A prediction that knows the final score is not a prediction; a
recommendation that places itself is not research.

## Current stage (updated 2026-11-02)

**Current boundary:** standalone tested research tools and command-line scripts
are available. The generic production `src/football_betting` model, data,
feature and backtest interfaces are **not wired to these tools**. The Stage 1
placeholder list later in this document is not a list of missing research tools.

**TASK0045 cloud collection: engineering ACCEPT.** The official-only 60-second
collector and 2-minute raw-SHA health monitor run on `evlab-cloud` under
persistent systemd units, with tested restart and immutable segment rotation.
Long-term soak, scheduled offsite backups and external alerts remain pending.

**TASK0043/TASK0044 forward forecast:** two real matches were frozen before
kickoff and published via Git. Their delayed Oct31 official scoring task
**actually ran and independently passed 2/2 official-match blind score QA**
(TASK0044 first real prospective closure ACCEPT, N=2). This establishes
traceability and genuine prospective scoring, **not** statistical superiority,
market EV or reliable future automated scoring. See
`REPORTS/EVLAB-TASK0044-FIRST-REAL-OFFICIAL-BLIND-SCORE-20261031.md`.

**TASK0046 guarded forward publication:** a separate once-daily, one-shot
official source capture now reuses TASK0044/TASK0043; newly qualified fixtures
may be Git-published with exact four-model vectors and source hashes only
before kickoff. No eligible new fixture means no new Git commitment. The
previously audited two-league/35-crosswalk scope is unchanged.

**TASK0048 guarded automatic delayed official scoring: engineering ACCEPT
for actual daily Windows task and no-due condition.** The 18:30 Beijing
job reads only previously Git-anchored TASK0046 prospective cohorts, checks
pre-kickoff chronology and original hashes, scores official results after a
3-hour delay, and independently replays evidence. Failure and missing
official results remain in immutable attempt roots. **No new qualifying
Git-published forecast existed in the 2026-11-02 real run**, so actual
new-cohort auto-scoring remains PENDING. See
`REPORTS/EVLAB-TASK0048-BOUNDED-AUTOMATIC-SCORING-20261102.md`.
On 2026-11-02 the 11:15 TASK0046 run failed Git fetch exit128 (retained
as failure), then a real later scheduled-task retry succeeded with 9 official
fixtures but no new approved model cohort. A bounded Git fetch retry was
added; intermittent network failures are **not** ruled out.

**TASK0049 Nov3 forward-task incident and QA:** the 11:15 Windows TASK0046
attempt ended with 0xC000013A and no complete journal. New STARTED / FINISHED
invocation markers and NO_NEW eligibility-rejection counts were added. A real
direct wrapper run succeeded with 21 official fixtures, all excluded because
their leagues were outside the two approved forward-model competitions.
Both registered Windows research tasks were adjusted to permit battery power,
which cleared a queue block; however a subsequent true Task Scheduler start
still ended 0xC000013A without FINISHED. **Unattended scheduling remains
REJECTED/PENDING, not ACCEPTED.** Cloud TASK0045 is separate and healthy.
See `REPORTS/EVLAB-TASK0049-ACTUAL-RUN-BATTERY-TRIAGE-20261103.md` and
`REVIEWS/EVLAB-TASK0049-INDEPENDENT-QA-20261103.md`.

**TASK0051 Nov3 first real same-fixture market benchmark: RETROSPECTIVE
EXPLORATORY ACCEPT; PIT-MARKET ALPHA NO-GO.** Strictly matched 175 of 237
available market fixtures during June 11-30 against the frozen Phase3 model
records. On the same 175, market opening 1X2 de-vig Log Loss **0.998770**
versus EV-Lab league-Poisson **1.044675**; Brier3 **0.597135** versus
**0.630875**. Nominal daily-bootstrap interval favoured the market in this
short retrospective sample, but independent quote-time/PIT verification is
absent. No bookmaker EV, tradable alpha, CLV or profit is established.
See `REPORTS/EVLAB-TASK0051-175-SAME-FIXTURE-ODDS-BENCHMARK-20261103.md`.

**TASK0052 Nov8 pre-match public archive provenance audit: LIMITED ACCEPT.**
The first market benchmark was rechecked against the source publisher's
**12 separate June 20-30 daily track-record archives**, each SHA-verified
against the pinned public manifest. For its original 175 fixtures,
75 occurred in a provider-dated snapshot before kickoff and retained the
same provider-defined row hash in the later 1X2 CSV. Five pregame archive
rows failed identity/hash consistency, nine were absent from earlier
snapshots, and 86 had no provider archive before kickoff. On the 75 qualified
rows, market Log Loss=**1.062163**, Poisson=**1.073100**; the paired daily
nominal interval spans zero, and the source sample is selected, so the
apparent advantage remains **unproven**. Provider-controlled timestamps,
missing archived full 1X2 vectors, unverified OpenTimestamps attestation and
retrospective Phase3 model construction mean **still NOT independent PIT or
betting EV evidence**. Full report and QA:
`REPORTS/EVLAB-TASK0052-75-PREGAME-ARCHIVE-CHECK-20261108.md`.

**Nov8 operational caveat:** cloud TASK0045 capture/health is OK, but local
TASK0046 scheduled 11:15 pre-kickoff runs on Nov5/6 and the recovered Nov8
run ended in Windows `0xC000013A` without matching FINISHED journals.
TASK0048's local scoring log still recorded exit0. Windows forward scheduler
reliability is **REJECTED/PENDING**, and no new qualifying prospective
market comparison can be claimed from these failed attempts.

**TASK0053 Nov8 cloud shadow dry probe → real Git-anchored forward cohort:
RESEARCH ACCEPT; unattended cloud publish NO-GO.** An isolated Tencent cloud
environment reproduced the frozen historical/identity SHA-protected model,
actually fetched 26 official fixtures, and produced **one** future four-model
forecast for fixture 2042640, kickoff 2026-11-08 19:45 UTC. Original cloud
run was `probe` and therefore **not admissible** until its unchanged freeze
SHA was relayed to the existing Windows TASK0046 Git preflight/publisher.
That unmodified gate committed the forecast to remote Git before kickoff
(`632aced`, verified 2026-11-08 07:15:55 UTC). A create-only bridge placed
the same original frozen bytes into TASK0048's approved off-Git score root;
real TASK0048 then returned `WAIT_KICKOFF_PLUS_THREE_HOURS`, correctly
refusing premature result acquisition. No bookmaker quotes, no EV/no bet.
**Cloud auto-push was NOT enabled:** isolated shadow has no authenticated
private GitHub remote, and local Windows forward scheduler remains unreliable.
The authorized 14/R9 research project is temporarily closed and was not
accessed. See `REPORTS/EVLAB-TASK0053-CLOUD-PROBE-FIRST-ANCHOR-20261108.md`
and `REVIEWS/EVLAB-TASK0053-INDEPENDENT-QA-20261108.md`.

**TASK0054 Nov8 cloud forward/scoring daily scheduler cutover: ENGINEERING
ACCEPT for verified handover; multi-day unattended stability PENDING.**
An EV-Lab-repo-scoped GitHub write deploy key on Tencent cloud was verified
by creating, SHA-checking and deleting a temporary remote Git branch.
The isolated cloud Git checkout retains full origin/main integrity.
Cloud TASK0046 forward publisher and TASK0048 official scorer both passed
real systemd oneshot execution (exit 0), with one-time clock-triggered
canary runs that each produced STARTED/FINISHED journals and exit 0.
The forward run saw 25 official fixtures; its only eligible identity was
already anchored match 2042640 and was **correctly deduplicated**.
The scorer recognized that match's true Git anchor and returned
`WAIT_KICKOFF_PLUS_THREE_HOURS`. Both daily Asia/Shanghai systemd timers
were then **enabled and independently read back active** (11:15 forward,
18:30 score). **Only afterward** the Windows TASK0046 and TASK0048
schedules were exported with SHA receipts and disabled (not deleted).
Cloud and Windows no longer simultaneously schedule publication.
NTP, SHA, official identity, 60-min lead, Git remote, create-only records,
no betting and blind result-delay controls remain unchanged.
The next real production scheduled triggers and post-match scoring still
require future observation; this is not a positive-EV claim. See
`REPORTS/EVLAB-TASK0054-CLOUD-AUTOMATION-CUTOVER-20261108.md`
and `REVIEWS/EVLAB-TASK0054-INDEPENDENT-QA-20261108.md`.

**TASK0055 Nov8 first true scheduled cloud score + independent health audit:
LIMITED OPERATIONS ACCEPT.** The formally enabled 18:30 Asia/Shanghai
cloud score timer actually fired at **2026-11-08 18:30:00**, and the scorer
finished at **18:30:05** with systemd exit 0. Official match 2042640 was
still pending kickoff, so the legitimate outcome was
`WAIT_KICKOFF_PLUS_THREE_HOURS` (NOT a model score).
The separately executed TASK0055 read-only watchdog matched the *real*
systemd `LastTriggerUSec` to a paired STARTED/FINISHED invocation log,
verified the active/enabled timer and successful unit exit, and wrote
immutable `PASS` evidence. Daily independent health-audit timers are now
`enabled/active` at **11:40** (forward) and **19:00** (score).
Unlike code-only tests, the real cloud watchdog service was run and
verified end-to-end. These produce local systemd failure findings, **not**
phone/push alerts. Tomorrow's first real cloud forward timer, its watchdog,
and the first independently blind-scored official outcome are **PENDING**.
See `REPORTS/EVLAB-TASK0055-CLEANUP-AND-FIRST-LIVE-TIMER-20261108.md` and
`REVIEWS/EVLAB-TASK0055-INDEPENDENT-QA-20261108.md`.

**Traditional SFC14 / optional-nine research (framework only, DRAFT):**
`docs/traditional-sfc14-r9-research-framework-v0.1.md` unifies
the independent match-probability P, bettor-combination Q and audited
tax-after-payout W research tracks. This is not an approved betting signal,
implemented market model, new scheduled task or production change; the
EV-Lab football mainline remains unchanged.

**Phase 1 official data factory: offline ACCEPT.** `tools/phase1_data_factory.py`
verified two real capture runs, 9,519 raw payloads and 1,727 candidate quote
events. Historical raw inputs and SQLite outputs are kept off Git.

**Phase 2 controlled qualification (historical 2026-10-26 snapshot):**
A separately bounded official-only collector and 2-minute health timer were
started on 2026-10-26 under a fresh cloud root. That old transient unit later
failed; the independent persistent TASK0045 service above supersedes it.
A 135-result independent,
weak observed-frequency 1X2 baseline is now available in
`src/football_betting/models/observed_frequency.py`, with a create-only
future-fixture freeze/scoring CLI at `tools/phase2_forecast_lab.py`. The first
four future fixture predictions were frozen before kickoff; only two official
HAD market reference snapshots passed strict research eligibility.

**Phase 3 multi-model retrospective research: ACCEPT for historical benchmark.**
`tools/phase3_multimodel_walkforward.py` checked 54,621 historically completed
rows, de-duplicated 53,705, and chronologically evaluated 25,969 real fixtures
(181 test dates, 233 competitions). Frozen baseline, pooled Elo/Davidson and
league-Poisson models were compared with a full previous-day embargo. On the
22,370 fixture same-sample overlap, Elo and Poisson outperformed the raw
frequency baseline; Poisson scored slightly better than Elo. This is **not**
a point-in-time-verified odds-market or future-fixture profit study. See
`REPORTS/EVLAB-PHASE3-25969-MULTIMODEL-OOS-20261026.md`.

**Not yet accepted:** long-term cloud soak, integrated independent
production model training/feature binding, reliable unattended official result ingestion,
independent bookmaker market outperformance, CLV or positive EV. The generic
`available_predictors()` registry remains empty because no audited automatic
training-source binding exists. Production feature construction also remains
unimplemented. See `REPORTS/` and `REVIEWS/` for newer qualification evidence.

### Original Stage 1 foundation (historical)

The foundation introduced data contracts, time guards and a reproducible test
suite. The initial state had no configured source/model/features/backtest; those
old statements no longer describe all standalone research tools.

**This stage does not execute bets, and this repository contains no code capable
of placing one.** No wagering venue is integrated, no credentials exist, and a
test asserts that no execution module or callable is defined anywhere in the
package.

## Core objectives

1. Make "what did this prediction actually know?" answerable months later.
2. Make look-ahead leakage structurally impossible rather than merely forbidden.
3. Keep prediction, recommendation, betting decision and actual execution as
   four separate things, in the code as well as on paper.
4. Keep every experiment, including the failures, permanently on the record.
5. Build the container before the contents, so that the first real model is
   measured honestly instead of retro-fitted to a story.

## System architecture

```
Data Layer          data acquisition, standardisation, validation, provenance
      |
Feature Layer       build pre-match vectors from permitted inputs only
      |
Prediction Layer    forecast only
      |
Odds Layer          decimal odds, implied probability, margin removal
      |
Decision Layer      model probability vs market implied probability
      |
Record Layer        append-only storage of predictions, recommendations, results
      |
Evaluation Layer    forecast quality and realised outcomes
      |
Backtest Layer      historical replay under strict time discipline
```

A shared, dependency-free `domain` layer holds the data contracts that all eight
layers speak in. Full responsibilities and the allowed import directions are in
[`docs/architecture.md`](docs/architecture.md).

### Four things that must not be merged

| Concept | What it is | Where it lives |
|---|---|---|
| **Prediction** | A probability triple from a named model version | `models` |
| **Recommendation** | A recorded opinion that a price is generous, at a moment | `decision` |
| **Betting decision** | Whether a human acts on that opinion | outside the code |
| **Actual execution** | Money moving | not implemented, and out of scope |

A `Recommendation` with `decision == BUY` is a row in a table. Nothing in this
package consumes it as an instruction.

## What is implemented

Genuinely working, tested behaviour:

- **Data provenance** - `DataProvenance` requires source, collection time, data
  time, version and schema; a dataset cannot describe an instant later than the
  moment it was collected; `DataSnapshot.knowable_at()` reconstructs what had
  actually arrived by a given instant.
- **Look-ahead guards** - `validate_observations()` rejects post-match objects,
  quotes that describe the future, quotes that had not yet reached us, quotes at
  or after kickoff, and inputs from other fixtures.
- **Time discipline in the data contracts** - every timestamp is timezone-aware;
  `as_of <= created_at`; `data_time <= collected_at`; a prediction created at or
  after kickoff is refused.
- **Odds arithmetic** - implied probability, overround, multiplicative margin
  removal, fair odds, expected value per unit.
- **Decision engine** - compares a forecast with a price under an explicit
  policy and emits a `Recommendation` with a deterministic, reproducible id.
- **Append-only records** - `RecordStore` and `ExperimentRegistry` have no
  update, delete or clear path; `state_as_of()` reconstructs the world as it was.
- **Evaluation metrics** - multi-class Brier score, log loss, accuracy,
  calibration curve, ROI, profit, strike rate.
- **Walk-forward windows** - train/test splits with an explicit embargo gap that
  cannot train on the period they predict.
- **Regression tests**, run in CI on every push (see current CI for total).

## What is not implemented in the generic package API

Listed explicitly so that nothing here reads as finished:

- Generic data acquisition. `data.loader.load_snapshot()` raises; the
  standalone official capture programs in `tools/` are implemented.
- Feature construction. `features.build_features()` validates, then raises.
- Generic model registry. `models.available_predictors()` is empty; separate
  four-model historical and prospective research tools are implemented.
- Generic backtest replay. `backtest.run_backtest()` validates, then raises;
  `tools/phase3_multimodel_walkforward.py` completed a 25,969-game study.
- Persistence. The record stores are in-memory only.
- Stake sizing, bankroll management, portfolio construction.
- Any form of bet placement or wagering integration.

Each of these raises `NotImplementedYetError`, which is a distinct exception
type precisely so that "not built yet" can never be mistaken for a working
implementation returning a plausible number.

**TASK0056 Nov9 verified post-kickoff official result remains NOT FINAL:
controlled scoring retry ACCEPT, new blind score PENDING.** An actual
09:03 Beijing cloud scoring service run on Git-anchored fixture 2042640
captured official status `1` and an empty full-time score (correct teams
and date); the old combined failure reported exit 2, retaining the raw
result. The code now distinguishes this exact *verified fixture, no final
score* situation as `WAIT_OFFICIAL_FINAL` while still rejecting mismatched
team identity, unknown statuses and inconsistent result fields. The real
systemd `Restart=on-failure` mechanism retried at 09:08, fetched the new
GitHub fix and exited **0**, recording a new immutable journal and source
manifest. Independent runtime QA checked original freeze and official
page SHA, confirmed both failure and wait evidence retained, and verified
**no** blind score or QA acceptance file was written. All **527 tests
passed**. Future regular 18:30 official scoring remains active; no match
outcome, model accuracy or betting EV can be claimed until status `2` and
the full-time result pass independent audit. See
`REPORTS/EVLAB-TASK0056-OFFICIAL-NOT-FINAL-SCORING-20261109.md` and
`REVIEWS/EVLAB-TASK0056-INDEPENDENT-QA-20261109.md`.

**TASK0057 Nov9 authentic scored prospective N=3 cohort: RESEARCH
ARITHMETIC ACCEPT, MARKET ALPHA/EV NO-GO.** On 2026-11-09 11:15 CST,
the *real scheduled* Tencent cloud forward publication captured 4 official
matches but all 4 failed the previously frozen competition gate; at 11:40
the independent timer watchdog reported `PASS`, and no synthetic forecast
was committed. At 18:04 CST, the cloud official-only scorer finally received
status `2` and final `1–2` for frozen match `2042640` (Lens–Marseille,
away win) and generated genuine `INDEPENDENT_SCORE_ACCEPTED` evidence,
with byte-verified Git anchor `632aced` and complete standalone QA.
**All four models' top class predictions missed** that fixture.
TASK0057 independently checked both accepted, disjoint prospective cohorts
(Oct31 N=2; Nov9 N=1), preserving exact score and QA SHA proofs and
recomputing all 3 per-fixture loss/Brier/top-class totals. Result for N=3:
global-frequency Log Loss `0.9395`, league-frequency `0.8848`,
Elo `1.1026`, league-Poisson `1.0634`; top-1 accuracy respectively
`2/3,2/3,1/3,1/3`. **With only three matches, no model can be
selected, no bookmaker comparison is possible and no positive EV or CLV
is supported.** Exact aggregate output:
`research/task0057_prospective_official_n3_20261109.json`, report and
independent QA: `REPORTS/EVLAB-TASK0057-PROSPECTIVE-N3-AUDIT-20261109.md`,
`REVIEWS/EVLAB-TASK0057-INDEPENDENT-QA-20261109.md`. No changes to
the separately closed 14/R9 project.

**TASK0058 Nov10 official feed supply constraint audit: ACCEPT; new model
alpha/EV NO-GO.** Nov9 18:30 cloud official scoring and 19:00 watchdog
both actually ran exit 0/PASS, correctly returned
`ALREADY_INDEPENDENTLY_ACCEPTED` for the Nov8 Git-anchored sample.
Nov10 11:15 forward captured 8 fixtures, all rejected by the existing
league gate; the independent 11:40 watchdog returned PASS. The Nov9
forward had likewise captured 4 offers, all out of scope.
To distinguish collection cadence from eligibility, TASK0058 strictly
replayed **26 completed TASK0045 cycles** covering UTC Nov8 00:00–Nov10
03:15. Of **3,045** archived source observations, **3,044** were valid
(1 transport error isolated), with **35 unique offered fixtures**,
**34 visible before kickoff**, **3 from preapproved leagues** and **only
1 passing the preapproved BOTH-team identity+league checks**: match
`2042640`, which was already Git-frozen and officially scored.
Therefore *in this bounded window* extra collection times would not
create a distinct new eligible forward match, and must not be confused
with expanding model/identity coverage. This does not extrapolate to
other dates or all football matches. Full source-only audit replay was
byte-identical twice (SHA256
`7c690964a006481da2e003d4d882137f5435504732888a7f8801f3ed6420f85e`);
a **separately implemented independent SQLite/gzip/identity check**
reproduced the counts. No training, fixture whitelist, cloud scheduler,
model odds, or production data was modified. See
`research/task0058_official_supply_coverage_20261110.json`,
`REPORTS/EVLAB-TASK0058-REAL-OFFER-COVERAGE-20261110.md` and
`REVIEWS/EVLAB-TASK0058-INDEPENDENT-QA-20261110.md`.

**TASK0059 Nov10 verified 14-league prospective expansion:
ENGINEERING ACCEPT; true expanded forward N still PENDING.** Prior to
TASK0059 the safe TASK0043/TASK0046 forward model accepted **only Norway
Eliteserien + French Ligue 1** despite a frozen HF historical source
with 271 league definitions. The league allowlist was enlarged from **2
to 14** by explicitly pinning the pre-existing source's exact
`(league_id,name,country)` tuples: English Premier League,
Championship; Spanish La Liga; Italian Serie A; German Bundesliga, 2.
Bundesliga; Dutch Eredivisie; Portuguese Primeira Liga; French Ligue
1, Ligue 2; Norway Eliteserien; Brazilian Serie A; Japanese J1 League;
Korean K League 1. **No club identities are newly assumed**: exactly
the previous SHA-pinned 70 official-to-HF club ID mapping from the
35 independently verified cup fixtures remains in force; unknown clubs
and name contradictions still fail closed. No new team models or
historical training are downloaded or applied.

Using the previously SHA-audited TASK0058 Nov8–10 retrospective
official offer cohort, an **as-of source, NO-score counterfactual** found
6 distinct matches that pass strict both-club identity and all four
frozen model readiness gates under 14 leagues, compared with **1 under
2 leagues**. Six historical matches are **not** prospective predictions
or model wins, and may NEVER be included in real forward scoring.
The old TASK0058 two-league experiment was made replay-invariant by
pinning both its source-run IDs and 2-league policy; after the change
the original **full archived source result SHA256 remained exactly**
`7c690964a006481da2e003d4d882137f5435504732888a7f8801f3ed6420f85e`,
and this *exact digest* was re-observed byte-for-byte on the live cloud
after versioning. GitHub→Tencent cloud activation and a new genuine
read-only one-shot official capture probe succeeded at 2026-11-10
12:33 CST; that probe found **8 fixtures, 0 eligible**, correctly
produced **no new prospect** and left Git clean. Local **566 passed**
regression tests. Existing forward scoring and watchdog timers remain
enabled. See
`research/task0059_expanded_league_eligibility_20261110.json`,
`REPORTS/EVLAB-TASK0059-14-LEAGUE-EXPANSION-20261110.md` and
`REVIEWS/EVLAB-TASK0059-INDEPENDENT-QA-20261110.md`.

**TASK0060 Nov10 approved team expansion ACTUALLY DEPLOYED:
70→143 independently verified clubs; research profitability UNPROVEN.**
TASK0059 previously broadened league eligibility from 2 to 14 but
only 70 clubs could pass the exact two-team official-to-HF match gate.
TASK0060 reused independently accepted cross-source match identities:
76 from TASK0034 and 11 from TASK0036. Original Sporttery raw gzip
HTTP-body SHA, ESPN raw pages/event/team IDs and source-specific UTC
kickoff, frozen HF historical team ID/name and prior league games were
checked. **73 new clubs** passed as additive-only entries, **110
individual provenance witnesses** independently rechecked, and **6
source observations** refused (ambiguous names including Inter/Ath
Bilbao; no same-league unique HF ID; or fewer than five pre-July
historical league matches). The original **70 official and HF IDs and
Chinese team names are unchanged**. Source proof in
`research/task0060_verified_club_extension_20261110.json` with exact
SHA256 `9ac60ea590c0bdf0702024ccbe2712f27dfbe45445f74e70e8df34cd233056c8`,
which now survives Windows/Git/cloud byte-for-byte without line-ending
normalization. The frozen bridge loader requires both the original
SHA and this new SHA; new Git forecast ledgers record both source
hashes plus a combined identity version. Historic TASK0058's exact
two-league/26-run original remains replayable with its original
SHA `7c690964a006481da2e003d4d882137f5435504732888a7f8801f3ed6420f85e`.
Real Tencent cloud source probe (Nov10 **14:30 Beijing**) returned
HTTP200 with 8 non-approved-league offers, correctly **0 new Git
forecasts**; production timers remained active.

On the fixed *retrospective source-only* Nov8–10 window, new
143-club, 14-league eligibility increased distinct identity-qualified
matches **6→19** and complete four-model-ready matches **6→16**,
when compared with 70-club 14-league eligibility. Two source replays
were byte-identical; **these are NOT real pre-kickoff Git forecasts
or extra scored results**. True prospective independently scored
N remains **3**; no comparable real-time market odds, no demonstrated
CLV or positive EV. Full report:
`REPORTS/EVLAB-TASK0060-VERIFIED-143-CLUB-EXPANSION-20261110.md`,
independent QA:
`REVIEWS/EVLAB-TASK0060-INDEPENDENT-QA-20261110.md`,
source-only aggregate:
`research/task0060_club_expansion_source_counterfactual_20261110.json`.
The separately closed SFC14/R9 project was not accessed.

**TASK0061 Nov10 two-stage audit: canonical 14-league identity census
ACCEPT; same-match + same-time international odds still NO-GO.**
The project now has a persistent, source-versioned, extensible *historical*
club registry at `research/registry/v1-20261110/`: **501 distinct HF club
keys** associated with **605 league-member records** across all 14
preapproved leagues, original **143 preapproved official↔HF identities**,
**358 HF-only unapproved candidates**, **503 source-name alias candidates**
(never automatically accepted) and a separate 14-league summary.
Frozen HF source as-of July 5 2026 and both approved identity ledger
SHA values remain immutable. These are historic league members, **NOT
the 2026/27 active roster**. New names, 90% similarity or a single matched
opponent never authorize a prediction; aliases need independently verified
two-side event ID/time/type witnesses.

The real original Git-frozen Lens–Marseille Nov8 match was joined as a
*research-only candidate* to the Nov10-retrieved, CC BY-4.0 TipsAudit
public postmatch page (`643fa7f841c65a737487ca406a2eefb5dcf307ba24289f967e658fb90a95172e`);
this page self-reports a Nov1 prediction record and shows Pinnacle-style
2.06/3.94/3.20 prices, but was observed by EV-Lab **after the game**,
has no independently approved event crosswalk, and proves no market quote
was contemporaneously available when the model froze Nov8 07:14 UTC.
The actual strict gate correctly returned **0/1 accepted contemporaneous
international quotes**. The production-independent
`tools/task0061_same_time_odds.py` now enforces exact two-side identity,
kickoff, all three full-time 1X2 selections, bookmaker update time,
<10-minute pre-model raw-response receipt, separate pre-model Git
receipt anchor and original raw SHA; no guessed timestamps, no odds in
the prediction model, no EV/ROI claim. The Odds API requires a licensed
key and paid history for retrospective snapshots; NO new price
collector, API key or subscription has been installed. See
`REPORTS/EVLAB-TASK0061-14-LEAGUE-REGISTRY-AND-PIT-ODDS-20261110.md`
and `REVIEWS/EVLAB-TASK0061-INDEPENDENT-QA-20261110.md`.
Previously accepted prospective N=3 remains unchanged; 14/R9 remains closed.

**TASK0062 Nov10 live free The Odds API pilot: source/format PARTIAL
ACCEPT; same-time model-market comparison remains 0/NO-GO.** An existing
free key was configured **locally only after TASK0061 signoff** (the earlier
TASK0061 historical statement that no key was installed applied at its
signoff). One no-cost sports catalogue listed 11/14 target leagues; one
1-credit Ligue 1 EU h2h call produced 18 upcoming events, 20 bookmakers
(Pinnacle in all 18), 244 complete three-way markets. Independently parsed
raw UTC timestamps put 244/244 bookmaker-market observations within
0.12–1.34 minutes of receipt. However no provider event↔official fixture
identity bridge or pre-model Git quote anchor exists: PIT eligible remains
zero. No recurring odds collector and no historical purchase were made.
See `REPORTS/EVLAB-TASK0062-FREE-ODDS-API-QUALIFICATION-20261110.md`
and `REVIEWS/EVLAB-TASK0062-INDEPENDENT-QA-20261110.md`.

## Research principles

Stated in full in [`docs/project-charter.md`](docs/project-charter.md):

1. **No future information.** Nothing knowable only after kickoff may enter a
   pre-match artefact. `pre-match`, `live` and `post-match` are distinct.
2. **Traceable data.** Source, collection time, data time, version, schema.
3. **Recommendation is not execution.** They are separate modules; stage 1
   implements no execution at all.
4. **Failures are retained.** Every formal experiment carries an id, a
   hypothesis, a data version, a model version, its parameters, its result and a
   status - and there is no delete path.
5. **No data leakage.** Future information, look-ahead bias, selection bias,
   survivorship bias, and leakage through labels, odds or post-match data.

Supporting documents:

- [`docs/data-policy.md`](docs/data-policy.md) - the bar a data source must clear
- [`docs/experiment-protocol.md`](docs/experiment-protocol.md) - pre-registration
  and how results are reported
- [`docs/reproducibility.md`](docs/reproducibility.md) - how to reproduce a run

## How to run

Requires Python 3.10 or newer. Runtime dependencies: none.

```bash
git clone https://github.com/lixiuzuapple-a11y/football-betting-research.git
cd football-betting-research

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Import the layers:

```bash
python -c "import football_betting; print(football_betting.LAYERS)"
```

There is no single installed production console entry point. Working on-demand
research CLIs include `python -m tools.task0044_forward_orchestrator --help`
and `python -m tools.task0046_forward_publication --help`. These require
previously audited off-Git sources and are **not** a generic market or betting
interface. Unimplemented package boundaries still raise
`NotImplementedYetError`.

## How to test

```bash
pytest
```

Lint and format:

```bash
ruff check .
ruff format --check .
```

The suite covers, among other things, the seven checks required of the first
milestone: package import, model instantiation, probability constraints,
odds-to-implied-probability arithmetic, recommendation generation, the refusal of
post-match data as a pre-match input, and experiment recording.

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| **1. Foundation** | Contracts, guards, tests, CI | ACCEPT |
| 2. Data | Official source capture and archive; generic package loader | Research tool ACCEPT; generic API PENDING |
| 3. Features | Production point-in-time feature builder | PENDING |
| 4. Baseline model | Historical Elo, Poisson and frequency models; future freeze | Research ACCEPT; forward sample accumulating |
| 5. Odds and value | Independently sourced simultaneous market quotes | NOT ACCEPTED |
| 6. Evaluation | Historic metrics; true prospective official blind score | Historical ACCEPT; first genuine N=2 blind score ACCEPT; sufficient future sample PENDING |
| 7. Backtest | 25,969 retrospective fixtures | Historical ACCEPT, market-PIT not proven |
| 8. Operations | Cloud collector, monitor, guarded daily forward task | Engineering partially ACCEPT, external alerts/backup PENDING |
| 9. Execution | *Deliberately unplanned* | Out of scope |

Stage 9 is not a backlog item. Automatic betting is excluded from the project as
currently chartered; revisiting it would be a separate decision with its own
risk review, not an increment on this one.

## Licence

MIT. See [`LICENSE`](LICENSE).
