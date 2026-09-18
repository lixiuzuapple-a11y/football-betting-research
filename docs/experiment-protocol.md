# Experiment Protocol

How a research question becomes an experiment, and how its result is reported.

The governing idea: **a hypothesis written after seeing the number is not a
hypothesis.** Everything here exists to make that distinction enforceable.

---

## 1. The record

Every formal experiment carries all seven fields. A record missing any of them is
not an experiment:

| Field | What it holds |
|---|---|
| `experiment_id` | Stable identifier |
| `hypothesis` | A falsifiable statement, written before the run |
| `data_version` | The snapshot version tested |
| `model_version` | The model tested, or `none` |
| `parameters` | Every choice that was fixed in advance |
| `result` | Measurements, or the reason there are none |
| `status` | `PLANNED` / `RUNNING` / `COMPLETED` / `FAILED` / `ABANDONED` |

Enforced by `records.ExperimentRegistry`, which additionally:

- **pre-registers** - an experiment is created `PLANNED` before it runs;
- **freezes results** - a resolved experiment cannot be re-resolved; a correction
  is a new experiment;
- **has no delete path** - `FAILED` is terminal and permanent.

## 2. Lifecycle

```
PLANNED ──▶ RUNNING ──▶ COMPLETED
                   └──▶ FAILED
                   └──▶ ABANDONED
```

Terminal states never reopen. `FAILED` is retained because a failed experiment
that vanishes is a failed experiment waiting to be repeated.

## 3. A hypothesis must be falsifiable

Not a hypothesis:

> The model should work well on the Premier League.

A hypothesis:

> On the 2026-27 Premier League sample, predictions with model probability at
> least 0.05 above the de-vigged market probability will show a positive ROI
> after a 5% margin, over at least 300 settled recommendations.

The second one names the sample, the threshold, the metric, the constraint and
the size. It can lose.

## 4. Pre-registration checklist

Before running, write down and commit:

- [ ] The hypothesis, in falsifiable form.
- [ ] The **data version** and its provenance.
- [ ] The **model version**, or `none`.
- [ ] The **decision rule** and its parameters (`DecisionPolicy`).
- [ ] The **metric** that decides the outcome.
- [ ] The **sample** and the minimum size.
- [ ] The **stopping rule** - when the run is over.
- [ ] What result would **refute** the hypothesis.

If any of these is decided after seeing results, the experiment is exploration,
not confirmation, and must be labelled as such.

## 5. Reporting rules

Every reported metric travels with:

1. **Sample size.** An ROI over 40 bets is noise with a decimal point.
2. **Data version.** `2026-09-18.1`, not "the data".
3. **Model version.**
4. **The period covered**, in `data_time` terms.
5. **The margin assumption.** Gross and net are different numbers.

Format:

```
experiment_id:  exp_0001
hypothesis:     <one sentence>
data_version:   <snapshot label>
model_version:  <label or none>
period:         <data_time_start> .. <data_time_end>
sample:         n = <settled recommendations>
metrics:        brier / log loss / accuracy / roi / strike rate
status:         COMPLETED | FAILED
notes:          what surprised us, and what we now believe less strongly
```

## 6. Metrics, and what each one actually says

| Metric | Answers | Does not answer |
|---|---|---|
| Brier score | Are the probabilities good probabilities? | Whether money was made |
| Log loss | How costly was over-confidence? | Whether money was made |
| Accuracy | How often was the top pick right? | Whether the price was good |
| Calibration curve | Is 70% really 70%? | Whether the edge is real |
| ROI | What did the sample return? | What the next sample will return |
| Strike rate | How often did recommendations win? | Whether they were profitable |

**A model can improve on the first four while making the fifth worse.** This is
not a paradox; it means it is pricing correctly into an efficient market. Report
the forecast metrics and the ROI together, always.

Accuracy is the most misleading single number in this list: backing a 0.9
favourite gives high accuracy and a negative expectation at a short price.

## 7. Sample size discipline

Rules of thumb, not laws:

- Below ~100 settled recommendations, an ROI difference is a coincidence.
- Below ~300, do not attribute an ROI difference to skill.
- Split the sample. Report in-sample and out-of-sample separately, and label
  which is which.
- The number of configurations tried is part of the result. Twenty variants
  tested and one reported is a selection effect, not a finding.

## 8. Attribution

Every result is attributable to a triple:

```
(data_version, model_version, parameters)
```

A reported number without that triple is not reproducible and is therefore not
evidence. When a metric changes, the triple explains why - or the reason is
unknown, and is reported as unknown.

## 9. Failures

A failure is a result. The registry keeps it, and the report states it.

```
status:  FAILED
result:  {"error": "no data source configured"}
```

Do not:
- delete a failed experiment;
- retry the same configuration hoping for a different number;
- report a failure as "not yet run";
- bury a failure in a footnote while the headline quotes a different sample.

## 10. From result to belief

A single positive result does not change the system. Progression requires:

1. A pre-registered hypothesis.
2. A positive out-of-sample result.
3. A stability check across sub-periods or leagues.
4. An explanation of *why* the effect should exist, stated before the test.

Step 4 is the one most often skipped. A pattern in historical odds is easy to
find and usually means the data was assembled with hindsight.
