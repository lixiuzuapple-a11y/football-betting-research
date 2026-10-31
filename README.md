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

## Current stage (updated 2026-10-31)

**Current boundary:** standalone tested research tools and command-line scripts
are available. The generic production `src/football_betting` model, data,
feature and backtest interfaces are **not wired to these tools**. The Stage 1
placeholder list later in this document is not a list of missing research tools.

**TASK0045 cloud collection: engineering ACCEPT.** The official-only 60-second
collector and 2-minute raw-SHA health monitor run on `evlab-cloud` under
persistent systemd units, with tested restart and immutable segment rotation.
Long-term soak, scheduled offsite backups and external alerts remain pending.

**TASK0043/TASK0044 forward forecast:** two real matches were frozen before
kickoff and published via Git. Their original Oct31 12:30 Beijing delayed
official scoring task is **pending until actual scoring and independent QA**.

**TASK0046 guarded forward publication:** a separate once-daily, one-shot
official source capture now reuses TASK0044/TASK0043; newly qualified fixtures
may be Git-published with exact four-model vectors and source hashes only
before kickoff. No eligible new fixture means no new Git commitment. The
previously audited two-league/35-crosswalk scope is unchanged.

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
| 6. Evaluation | Historic metrics; true prospective official blind score | Historic ACCEPT; forward scoring PENDING |
| 7. Backtest | 25,969 retrospective fixtures | Historical ACCEPT, market-PIT not proven |
| 8. Operations | Cloud collector, monitor, guarded daily forward task | Engineering partially ACCEPT, external alerts/backup PENDING |
| 9. Execution | *Deliberately unplanned* | Out of scope |

Stage 9 is not a backlog item. Automatic betting is excluded from the project as
currently chartered; revisiting it would be a separate decision with its own
risk review, not an increment on this one.

## Licence

MIT. See [`LICENSE`](LICENSE).
