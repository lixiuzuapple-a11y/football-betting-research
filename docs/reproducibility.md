# Reproducibility

A result that cannot be reproduced is an anecdote. This document states what
"reproducible" means for this project, and how to check it.

---

## 1. Environment

| Requirement | Value |
|---|---|
| Python | 3.10 or newer (CI runs 3.10, 3.12 and 3.13) |
| Runtime dependencies | **none** - standard library only |
| Development dependencies | `pytest`, `ruff` (installed via `.[dev]`) |

Runtime dependencies are deliberately empty at stage 1. Every import in
`src/` resolves to the standard library, which means a research result depends on
Python and this repository's own code and on nothing else. A test asserts the
empty dependency list so that adding one is a visible decision.

The CI matrix pins the *minor* version range and runs the full suite on each. A
result that only reproduces on one interpreter is reported as such.

## 2. Setting up

```bash
git clone https://github.com/lixiuzuapple-a11y/football-betting-research.git
cd football-betting-research

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Verify:

```bash
pytest
ruff check .
ruff format --check .
```

## 3. What makes a run reproducible

Every run is identified by a triple:

```
(data_version, model_version, parameters)
```

Given those three, a third party must be able to reach the same numbers. That
requires four things:

### 3.1 The exact data

A `data_version` identifies one immutable `DataSnapshot`. Capture its
`DataProvenance` alongside every result:

```
source            where the rows came from
version           the snapshot label
collected_at      when we pulled it
data_time window  the instants it covers
row count         how many rows
schema            the payload contract version
```

Datasets are not committed (see [`data-policy.md`](data-policy.md)). The
provenance record is what allows a snapshot to be re-fetched or verified. Without
it, a result is unreproducible by construction.

### 3.2 The exact code

The `model_version` string on every `Prediction` identifies the code. In
practice, record the commit SHA. `git log --oneline -1` is sufficient at current
project size.

### 3.3 The exact parameters

Every choice fixed in advance - thresholds, thresholds, tolerances, sample
windows, the `DecisionPolicy` - is recorded on the `Experiment` under
`parameters`. Not the choices that turned out to matter: **all** of them.

Parameters are stored behind a read-only proxy, so mutating the caller's dict
after registration cannot rewrite research history.

### 3.4 The exact time discipline

Reproducing a *decision* also requires reproducing what was known. Two rules:

- `as_of` on every `Prediction` and `Recommendation` records the information
  cutoff used.
- `RecordStore.state_as_of(t)` reconstructs the world at `t` from what had
  actually been recorded, not from what we know now.

A replay that reads today's tables without an `as_of` filter is not a
reproduction; it is a re-run with hindsight.

## 4. Determinism

What is deterministic today:

| Component | Determinism |
|---|---|
| Odds arithmetic | Fully deterministic |
| Decision engine | Fully deterministic |
| Recommendation ids | Deterministic - derived from the decision inputs |
| Evaluation metrics | Fully deterministic |
| Walk-forward windows | Fully deterministic given the schedule |
| Ordering of validated observations | Deterministic - sorted by `(data_time, snapshot_id)` |
| Experiment ids | **Not** deterministic - `uuid4` |

Recommendation ids are derived by hashing the decision inputs, so re-running the
same decision produces the same id. That is what makes a duplicate detectable
rather than silently appended as a second row.

Experiment ids are random. They are labels for a run, not derivations of it; pass
an explicit `experiment_id` when a stable identifier is required.

There is no random number generation anywhere in the package. When a model
introduces one, its seed becomes a required parameter and must appear in the
experiment record.

## 5. Floating point

Metrics are computed in double precision in plain Python.

- Compare with tolerances, never with `==`. The test suite uses `pytest.approx`.
- Probability vectors are checked against `1.0` with a tolerance of `1e-6`
  (`domain.validation.PROBABILITY_TOLERANCE`), not exactly.
- `implied_probability == 1 / odds` is checked to `1e-9`.
- Results are reported to the precision the sample supports. A Brier score to six
  decimal places on 50 matches is false precision; report it to two.

## 6. Reproducing a specific result

1. Check out the commit SHA recorded with the result.
2. Re-fetch or restore the `data_version` and verify its row count and hash.
3. Run the experiment with the recorded `parameters`.
4. Compare against the recorded `result`, using tolerances from section 5.

If step 2 cannot be completed - the source is gone, the licence changed, the feed
was revised - the result is marked **not independently reproducible**. It stays
in the record, flagged, rather than being quietly dropped.

## 7. Anti-reproducibility checklist

These make a result unreproducible. Each one has happened somewhere:

- [ ] A result reported without a data version.
- [ ] A snapshot whose provenance was never written down.
- [ ] A parameter tuned after seeing the result and not recorded.
- [ ] An in-sample number presented as out-of-sample.
- [ ] A refetch that silently overwrote an earlier capture.
- [ ] A rolling statistic computed with a centred, hence future-aware, window.
- [ ] A result that only reproduces on one machine, with no note saying so.
- [ ] A number copied from an earlier report rather than recomputed.

## 8. CI as the reproducibility gate

`.github/workflows/ci.yml` runs on every push and pull request:

```
checkout
   |
setup Python (3.10, 3.12, 3.13)
   |
install project with dev extras
   |
ruff check  +  ruff format --check
   |
pytest
```

A green build means the suite and the lint pass on all three interpreters from a
clean checkout. It does **not** mean any research result is correct - it means the
machinery is intact. Those are different claims, and the difference matters.
