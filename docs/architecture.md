# Architecture

## 1. Layer map

```
                         ┌──────────────────────────────┐
                         │  domain  (shared contracts)  │
                         │  imports nothing in-package  │
                         └──────────────┬───────────────┘
                                        │ (every layer may depend on domain)
    ┌───────────────────────────────────┴───────────────────────────────────┐
    │                                                                       │
    ▼                                                                       │
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│    data     │──▶│  features   │──▶│   models    │──▶│   decision  │◀──┐   │
│             │   │             │   │             │   │             │   │   │
│ acquisition │   │ pre-match   │   │ forecast    │   │ value       │   │   │
│ provenance  │   │ vectors     │   │ only        │   │ assessment  │   │   │
│ validation  │   │ + guards    │   │             │   │             │   │   │
└─────────────┘   └─────────────┘   └─────────────┘   └──────┬──────┘   │   │
                                                             │          │   │
                          ┌──────────────────────────────────┘          │   │
                          ▼                                             │   │
                   ┌─────────────┐        ┌──────────────────────────┐  │   │
                   │   records   │───────▶│       evaluation         │  │   │
                   │ append-only │        │  scoring & diagnostics   │  │   │
                   └─────────────┘        └────────────┬─────────────┘  │   │
                                                        │                │   │
                                                        ▼                │   │
                                                 ┌─────────────┐         │   │
                                                 │  backtest   │─────────┘   │
                                                 │ walk-forward│             │
                                                 └─────────────┘             │
                                                                             │
                   ┌─────────────────────────────────────────────────────────┘
                   ▼
            ┌─────────────┐
            │    odds     │  decimal odds, implied probability, margin removal
            └─────────────┘
```

Reading the arrows: `decision` consumes a forecast from `models` **and** a price
from `odds`. Those two inputs are never allowed to see each other. That is the
whole reason the value judgement can be audited.

## 2. Layer responsibilities

### `domain` - shared contracts

Not one of the eight functional layers. It holds the data contracts
(`Match`, `OddsSnapshot`, `Prediction`, `Recommendation`, `MatchResult`,
`BetRecord`, `Experiment`, `Team`) and the validation helpers, and it **imports
nothing inside this package**. This is what stops the eight layers from growing
private, mutually-incompatible dialects for the same noun - and what stops
`records` from having to import `decision` in order to store its output.

### `data` - what do we have, and where did it come from?

Acquisition, standardisation, validation and provenance. Produces immutable
`DataSnapshot` objects.

Must not: build features, model, or look at outcomes.
Unknowable to it: anything about the research question.

### `features` - what was knowable before kickoff?

Turns permitted observations into a pre-match vector, under a named
`feature_version`.

Must not: fetch data, predict, or read anything post-match. It owns
`validate_observations()`, which is the single chokepoint for look-ahead
leakage.

### `models` - what does the model think?

Consumes a `PredictionRequest` (a fixture plus a pre-match `FeatureSet`) and
returns a `Prediction`.

Must not: read market prices, see outcomes, or decide anything. It receives no
store handle and no result table, so it cannot leak what it cannot reach.

### `odds` - what does the price imply?

Decimal-odds arithmetic: implied probability, overround, multiplicative margin
removal, fair odds, expected value per unit.

Must not: hold an opinion about what to bet, or know what the model thinks.
It is pure arithmetic on numbers the caller supplies.

### `decision` - is this price generous?

The comparison layer, and the only place the two sides meet:

```
prediction.probability(selection)   vs   implied_probability(odds)
```

Emits a `Recommendation` with a `BUY` or `PASS` decision and a written reason.

Must not: place bets, size stakes, or reach a wagering venue. `BUY` is a label.

### `records` - what did we record, and when?

Append-only storage plus `state_as_of()`, which reconstructs everything knowable
at a past instant. Also the experiment registry.

Must not: predict, decide or evaluate. It stores and reconstructs.

There is no update path and no delete path. Corrections are new rows.

### `evaluation` - how good was it?

Scoring rules (Brier, log loss, accuracy), calibration diagnostics, and realised
outcome measures (ROI, profit, strike rate).

Must not: model, decide, or recommend what to do next. A backtest ROI is a
measurement of a sample, not an expectation of return.

### `backtest` - would this have worked?

Orchestrates the other layers over history under walk-forward windows with an
explicit embargo gap.

Must not: invent its own notion of time. It uses the same contracts and the same
`as_of` discipline as live operation, which is the only way a backtest can be
evidence about live behaviour.

## 3. Dependency rules

1. `domain` depends on nothing inside the package.
2. Data flows in one direction: `data → features → models → decision`.
3. `odds` is a leaf: anyone may call it; it calls no one.
4. `records` collects the outputs of `models`, `decision` and `data`. It is a
   sink, not a source, for anything except replay.
5. `evaluation` reads records; it never writes them.
6. `backtest` may orchestrate everything, but it may not bypass a guard. It calls
   the same `features.validate_observations()` that live operation calls.
7. No layer may import a private module (`_name`) of another layer.

Breaking rule 1 or 2 is an architectural bug, not a style preference. If a layer
needs something from a layer above it, the shared noun belongs in `domain`.

## 4. Why the comparison lives in its own layer

Two failure modes motivate splitting `decision` out of both `models` and `odds`:

- **Model contamination.** If the model can see the price, it will eventually be
  trained to agree with the price, and the "edge" becomes a restatement of the
  market.
- **Price contamination.** If odds arithmetic knows the forecast, de-vigging
  choices start being made to flatter the model instead of to describe the book.

Keeping them is a one-way street: `odds` produces numbers, `decision` compares
them. Neither knows the other exists.

## 5. The four concepts, architecturally

```
Prediction      models/      a probability triple, versioned, with an as_of
Recommendation  decision/    an opinion at a moment about a specific price
Betting decision            a human act; deliberately not in this repository
Actual execution            not implemented; out of scope for stage 1
```

There is no code path from `Recommendation` to money. A test asserts that no
execution module, execution callable or wagering endpoint exists anywhere in the
package, so an accidental addition fails CI rather than shipping quietly.

## 6. Where time is enforced

| Boundary | Rule | Enforced by |
|---|---|---|
| Data contract | every timestamp timezone-aware | `domain.validation.require_aware` |
| Odds snapshot | `data_time <= collected_at` | `OddsSnapshot.__post_init__` |
| Snapshot | covered window within `collected_at` | `DataProvenance.__post_init__` |
| Snapshot | no row outside the claimed window | `DataSnapshot.__post_init__` |
| Features | `as_of` strictly before kickoff | `features.validate_observations` |
| Features | no post-match object; no late arrival; no wrong fixture | same |
| Prediction | `as_of <= created_at` | `Prediction.__post_init__` |
| Prediction request | `features.as_of <= request.as_of` | `PredictionRequest.__post_init__` |
| Decision | pre-match; forecast not newer than the decision | `decision.decide` |
| Records | no prediction or recommendation stamped post-kickoff | `RecordStore.record_*` |
| Replay | `train_end <= test_as_of` | `WalkForwardWindow.__post_init__` |

## 7. Extension points

Adding capability is expected to happen at exactly these seams:

| To add | Change | Must also |
|---|---|---|
| A data source | `data.loader.load_snapshot` | document it in `data-policy.md`; add a schema version |
| A feature | `features.build_features` | extend `PERMITTED_INPUT_TYPES` deliberately, with the source documented |
| A model | a new module in `models/`, registered in `available_predictors()` | pre-register an experiment; never copy `UnimplementedPredictor` and tweak it |
| A market | `domain.enums.Market` and, if a plain 1X2 forecast cannot price it, a new model | add it to `ONE_X_TWO_MARKETS` only if the distribution genuinely applies |
| A metric | `evaluation.metrics` | report it with a sample size |
| A storage backend | a new implementation of the `records` interfaces | keep it append-only |

`UnimplementedPredictor` exists to make the absence of a model explicit. It is
not a template for one. A uniform `0.40 / 0.28 / 0.32` forecast is trivial to
write and would be indistinguishable from a real model in every downstream
report, which is exactly why it is not in this repository.

## 8. Known limitations

Honest list, current as of the foundation commit:

1. **No data.** The pipeline has never seen a real row.
2. **No model.** Every downstream metric is untested against reality.
3. **In-memory records.** `RecordStore` and `ExperimentRegistry` do not survive
   the process.
4. **No CLI.** There is nothing to run.
5. **`Market.HANDICAP_ONE_X_TWO` and `TOTAL_GOALS` are declared but not
   priceable.** A handicap shifts the outcome distribution, so reusing the plain
   1X2 vector would be a modelling error; it needs its own model.
6. **`MatchResult` knowledge is coarse.** A result becomes known at
   `recorded_at`; partial knowledge during a live match is not modelled, because
   live operation is out of scope.
7. **`DataSnapshot.knowable_at()` treats fixtures as known at the snapshot's
   collection time**, because fixture rows carry no arrival time of their own.
   This is conservative, not precise.
