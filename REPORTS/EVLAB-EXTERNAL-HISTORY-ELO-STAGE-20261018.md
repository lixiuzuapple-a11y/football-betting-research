# EV-Lab independent historical team-strength trial — 2026-10-18

## Decision
**Stage ACCEPT** for tested external history ingestion and independent out-of-season football prediction benchmark. **NO-GO for claim of independent superiority over market; NO-GO for transferring these scores to the original 135 Chinese Sporttery-labelled fixtures.**

## External evidence
Football-Data public result CSV source: https://www.football-data.co.uk/downloadm.php and https://www.football-data.co.uk/mmz4281/{season}/{league}.csv . Twelve real CSV artifacts downloaded for prior 2025/26 and held-out 2026/27 seasons (E0 English Premier League, E1 Championship, D1 Bundesliga, SP1 La Liga, I1 Serie A, F1 Ligue 1). Files and SHA256 manifest kept off-repo at `E:\WebCodex-Workspace\EVLab-Data-Backups\external-history-20261018`. No user protected data uploaded.

## Fixed method; actual execution
- Prediction features: only earlier final scores. Static Elo-style initial rating 1500, K=20, home bonus +65 rating points, fixed draw probability 0.26. Chosen for a feasibility baseline, NOT tuned/learned from the held-out test; do not call it statistically optimal.
- 2025/26 historical training, 2026/27 held-out evaluation, chronological dates with same-day scores withheld from all predictions of that date.
- Test only if both teams have at least five prior results. Cross-season promotions can lead to exclusion. Market benchmark: normalized inverse three-way `AvgH/AvgD/AvgA` source odds, used **for comparative scoring only**, never to form independent predictor.
- Holdout includes **323 same-fixture comparisons across six leagues and 39 distinct match dates**.

| Metric | Independent Elo-style | Market normalized odds |
|---|---:|---:|
| Accuracy | 47.99% | **52.63%** |
| Multiclass log loss (lower better) | 1.023310 | **0.976332** |
| Three-class summed Brier (lower better) | 0.613416 | **0.581307** |

Paired difference independent-minus-market log loss = **+0.046978** (worse independent). Nominal date-cluster bootstrap percentile 95% **[+0.02648, +0.07143]**, 5000 draws fixed seed. Six leagues sample counts E0 46, E1 92, D1 31, SP1 64, I1 46, F1 44.

## Caveats / scope boundary
- These 323 are external European historical fixtures, **not** the EV-Lab official 135 labelled fixtures, and no controlled one-to-one linkage to the 135 was established. This supports methodological feasibility, not EV-Lab-specific predictive gain.
- At the 2026-10-18 evaluation date, the external recent files were available as downloaded; season holdout is chronological, but not a truly preregistered prospective trial. Draw probability and home advantage are simple heuristics; sensitivity and richer independently pretrained models are separate research questions and cannot be answered by this experiment.
- Source CSV bookmaker odds are comparison only and may be updated after matches; use these as observational odds benchmark, not guaranteed time-stamped available opening or executable Sporttery quotes.
- No stake, BUY/PASS, PnL, ROI, alpha, model-calibration superiority or real betting claim.
- A separate 27-country GitHub data candidate (xgabora/Club-Football-Match-Data) was identified, but its Elo post-Jun-2025 is self-described provisional continuation, with snapshots ending Sep 3 2026; it was not accepted as authoritative October 2026 pre-match ratings. Do not confuse derived Elo with historical observations.

## Status and next research boundary
**The independent route remains unproven against market on both tests:** prior 93-fixture rolling-frequency score and current 323-fixture external Elo-style trial. Do not keep tuning this specific baseline on held-out dates. A scientifically appropriate next phase requires frozen team/league ID mapping for official 135 matchIDs, earlier historical match records for those clubs with timestamp provenance, and a genuinely held-out subsequent observation window. Current progress makes external history sourcing demonstrably real but does not clear this mapping/coverage gate.

## Reproduce
`python -m tools.task0033_external_elo_trial --data <external-history-20261018-dir> --out <ELO_TRIAL.json>`.
Stored `ELO_TRIAL.json` and `SOURCE_MANIFEST.json` in data directory. Code `tools/task0033_external_elo_trial.py`; tests `tests/test_task0033_external_elo_trial.py`. Full suite: **308 passed**.
