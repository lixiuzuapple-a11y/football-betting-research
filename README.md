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

## Current stage

**Stage 1: infrastructure only.** This repository currently contains a project
skeleton, a set of data contracts with enforced invariants, the look-ahead
guards, and a real test suite. It contains no data, no features and no
forecasting model.

- **No data source is configured.** `available_sources()` returns an empty tuple.
- **No features are built.** The guards that decide what a feature vector may
  read are implemented and tested; featurisation is not.
- **No model exists.** `available_predictors()` returns an empty dict.
- **No backtest has been run.**

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
- **191 tests**, run in CI on every push.

## What is not implemented

Listed explicitly so that nothing here reads as finished:

- Data acquisition. `data.loader.load_snapshot()` raises.
- Feature construction. `features.build_features()` validates, then raises.
- Any forecasting model. `models.available_predictors()` is empty.
- Backtest replay. `backtest.run_backtest()` validates, then raises.
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

There is no command-line entry point, because there is nothing to run yet. The
library raises `NotImplementedYetError` at every unimplemented boundary rather
than producing placeholder output.

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
| **1. Foundation** | Repository, contracts, guards, records, tests, CI | **This stage** |
| 2. Data | One licensed, traceable source; documented schema; snapshots | Not started |
| 3. Features | An agreed feature contract, built only from permitted inputs | Not started |
| 4. Baseline model | A simple, explainable model with a pre-registered experiment | Not started |
| 5. Odds and value | Closing-line and movement-based market signals | Not started |
| 6. Evaluation | Calibration, ROI and stability reporting over a real sample | Not started |
| 7. Backtest | Walk-forward replay over a real historical sample | Not started |
| 8. Operations | Scheduling, monitoring, durable storage | Not started |
| 9. Execution | *Deliberately unplanned* | Out of scope |

Stage 9 is not a backlog item. Automatic betting is excluded from the project as
currently chartered; revisiting it would be a separate decision with its own
risk review, not an increment on this one.

## Licence

MIT. See [`LICENSE`](LICENSE).
