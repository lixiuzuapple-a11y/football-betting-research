# EV-Lab decisive independent vs market prediction study — 2026-10-18

## Decision
**NO EVIDENCE that the available independent pre-match model outperforms China's Sporttery normalized 1X2 market probabilities.** On a strictly same-fixture, chronological rolling holdout, the independent model loses materially. This rejects this **specific** independent baseline as useful alpha; it does not demonstrate that all possible richer independent models are inferior.

**Stage ACCEPT for actual evaluation; research branch STOP / no claim of positive betting EV.** Return to larger verified pre-match historical feature sourcing only if justified by a separate scoped research proposal, not by tweaking these 93 outcomes.

## Method
- Frozen 135 official-result-score fixture candidates, prior TASK0031 strict pre-kickoff odds: 126 eligible.
- Independent model uses only **earlier calendar dates' final 1X2 score classes**; no Sporttery/Pinnacle/bookmaker odds, no same-day outcomes and no current future results. Categorical Dirichlet(1,1,1) smoothed rolling past 1X2 outcome frequency.
- Chronological evaluation begins after at least 20 earlier eligible labelled matches. Grouped same kickoff date, so no intra-day forward knowledge. Gives **93 test matches across 7 days**, and both methods scored only on exactly those matches.
- Market comparator uses frozen selected quote normalized inverse-odds probabilities from TASK0031, not a newly fitted model.
- Metrics are multiclass log-loss, 3-outcome Brier *sum* (not the Brier average over classes), argmax class accuracy. No stake, revenue, ROI or BUY/PASS signals.
- Day-cluster bootstrap 5,000 fixed-seed resamples for paired Log Loss difference (independent minus market), nominal 95% interval; only 7 days so sampling uncertainty is not fully characterized.

| Metric | Independent rolling history | Sporttery normalized market |
|---|---:|---:|
| Matched evaluation fixtures | 93 | 93 |
| 1X2 accuracy | 41.94% | 58.06% |
| Log Loss (lower better) | 1.101636 | 0.908573 |
| 3-class Brier sum (lower better) | 0.668098 | 0.530657 |

Paired market advantage in Log Loss = **0.193063**, bootstrap nominal 95% CI for independent-minus-market **[0.126331, 0.296260]**.

Sensitivity of min-prior training cutoff 10 and 30 produces same test N and results because complete date buckets jump across thresholds; this is **not independent replication**.

## Feature sufficiency audit
The 135 joined matches involve **202 distinct team IDs**, with **146 teams appearing only once**, 56 at least twice, max three appearances. This corpus alone is insufficient to construct well-supported team-strength trajectories or estimate a serious dynamic Elo/Poisson model. Such a model without externally verified earlier team results would mainly encode noise or hindsight. This phase did not find an authoritative independent long-run pre-2026 historical league/team rating feed in existing stored assets.

## Important limits
- This is a deliberately weak independent baseline, and there was **no candidate richer team-level independent model actually tested**. The user question is answered within available evidence: **we have not demonstrated any independently better prediction than market.** Do not write stronger universal impossibility claims.
- 126/135 strict HAD candidate price observations had non-uniform lag to kickoff; timestamp and selling status require final source-contract validation before suggesting actionable investments.
- Predictions came from genuine earlier labels, but those labels were acquired retrospectively. Date-only frozen chronological holdout prevents test-label leakage in the independent model.
- Small, temporally clustered sample and conditional scored-fixture eligibility; uncertainty claims limited to a paired test, not general profitability.
- Testing a large number of variants on these fixtures would introduce selection bias. This stage makes the conservative **STOP** decision instead of backfitting a winning parameter.
- **No EV, no ROI, no profitability claim**.

## Reproducible evidence
Program `tools/task0032_independent_baseline.py`; tests `tests/test_task0032_independent_baseline.py`; underlying score table in independent offline evidence `TASK0031-ACTUAL-SCORING.json`, results `TASK0032-INDEPENDENT-COMPARISON.json` at `E:\WebCodex-Workspace\EVLab-Data-Backups\official-20261018`. Full repo test suite **305 passed**. Re-run `python -m tools.task0032_independent_baseline --scoring <TASK0031-ACTUAL-SCORING.json> --out <result.json>`.

## Final phase conclusion
**We have no empirical evidence that EV-Lab currently generates better independent probabilities than Sporttery de-vigged prices.** This project branch should stop trying to force alpha from this 135-match dataset. A future attempt requires independent validated pre-kickoff historical information and a new frozen out-of-sample time window; absent those, the market probabilities remain the stronger demonstrated benchmark.
