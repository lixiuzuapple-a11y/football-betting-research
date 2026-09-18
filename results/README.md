# results/

Output of formal experiments. **Currently empty.**

Nothing here is versioned; `.gitignore` excludes everything except this file and
`.gitkeep`. A result is only meaningful next to the experiment record that
produced it, and experiment records live in the code and in
[`../docs/experiment-protocol.md`](../docs/experiment-protocol.md).

## Every reported number travels with

1. **Sample size** - an ROI over 40 bets is noise with a decimal point.
2. **Data version** - `2026-09-18.1`, not "the data".
3. **Model version.**
4. **Period covered**, in `data_time` terms.
5. **Margin assumption** - gross and net are different numbers.
6. **Commit SHA** - the code that ran.

Without that context a number is a rumour, and a rumour in this directory is
worse than an empty directory.

## Layout convention

```
results/
├── <experiment_id>/
│   ├── manifest.json     the (data_version, model_version, parameters) triple
│   ├── metrics.json      the measurements
│   └── notes.md          what surprised us, and what we now believe less
```

## Rules

1. **Failed experiments are kept.** A `FAILED` result stays, with its reason.
   `ExperimentRegistry` has no delete path for exactly this reason.
2. **Never overwrite a result.** A re-run is a new file under a new id.
3. **Never report an in-sample number as out-of-sample.** Label which is which.
4. **Never drop the denominator.** Accuracy and ROI without a sample size are
   unreadable.
5. **Never present a backtest as a forecast.** A backtest measures a sample; it
   does not promise a return.

## Status

No experiment has been run. There is no data source and no model, so there is
nothing to measure yet. The empty directory is the accurate report.
