# EV-Lab actual 135-score prediction baseline — empirical stage 2026-10-18

## Evidence / research decision
**Full corpus scoring actually executed.** Strict pre-kickoff 1X2 market implied probabilities (inverse decimal sporttery HAD odds, normalized by sum to remove overround) scored against official final score. **126 / 135** official scored fixtures have an eligible strict odds snapshot; **9 excluded**, rather than imputed.

This demonstrates *market forecast information versus a no-information uniform baseline*, **NOT an EV-Lab alpha, profitable strategy, executable prices, or superior model**.

| Metric | Strict pre-kickoff market probability | Uniform 1/3 each |
|---|---:|---:|
| N | 126 | 126 |
| Winner/predicted 1X2 class accuracy | **59.52%** | not compared |
| Multiclass Log Loss (lower better) | **0.901876** | **1.098612** |
| Three-outcome Brier sum (lower better) | **0.526216** | **0.666667** |

Empirical average forecast (home/draw/away) = **42.37% / 23.17% / 34.46%**, empirical class frequencies = **45.24% / 23.81% / 30.95%**. These aggregates alone do not prove calibration.

As sensitivity check, allow numeric valid HAD without strict match-sale/market-status/flag gates: **128 / 135**, hit rate **59.38%**, Log Loss **0.901221**, Brier sum **0.525904**. Different samples, so do not infer strict gating improves or worsens forecasting accuracy.

## Time and leakage gates
- Each original capture observed_at_utc is compared with fixture matchDate + matchTime treated as UTC+08; **only capture observed before scheduled kickoff** qualifies.
- Each quote's provider updateDate/updateTime must not lie more than 2 minutes in the future relative to observed_at.
- Strict policy requires matchStatus Selling, sellStatus 1, poolStatus Selling for HAD and HAD selection flags hf/df/af exactly zero.
- Latest eligible quote per fixture selected on **observed timestamp**, tie broken by provider update timestamp; only then join immutable historical fixture ID to retrospective final scores.
- Selected strict candidate snapshot median was **161.94 minutes pre-kickoff**, minimum **0.229 minutes** and maximum **954.65 minutes**. This near-kickoff tail must be tested against a stricter frozen cutoff (e.g. 60 minutes) before any actionable strategy/backtest assertion.
- No accepted order evidence; match-time timezone semantics require independent source contract confirmation. No bookmaker comparison, stakes, EV or ROI tested.

## Results by kickoff date
| Date | N | Market log loss | Accuracy |
|---|---:|---:|---:|
| 2026-10-10 | 4 | 0.9161 | 50.0% |
| 2026-10-11 | 29 | 0.8784 | 65.5% |
| 2026-10-12 | 8 | 1.0027 | 50.0% |
| 2026-10-13 | 13 | 1.0276 | 38.5% |
| 2026-10-14 | 12 | 0.7214 | 91.7% |
| 2026-10-15 | 10 | 0.9491 | 40.0% |
| 2026-10-16 | 13 | 0.9096 | 53.8% |
| 2026-10-17 | 31 | 0.9441 | 61.3% |
| 2026-10-18 | 6 | 0.6458 | 66.7% |

## Uncertainty and interpretation
Simple fixture-IID bootstrap (5,000 draws, fixed seed 20261018) for the **Log Loss gain over uniform**: mean **0.196736**, 95% percentile interval approximately **[0.11244, 0.27363]**. This describes uncertainty under an *IID assumption*, not a robust estimate across correlated leagues/days. The market baseline can beat uniform without yielding any profitable or superior proprietary recommendation.

The label set consists of 135 official score candidates matching original fixture ID, team IDs, date and finished status. The remaining 34/169 remain outside this stage. Valid labelled sample used in this stage is only 126, not 135.

## Reproducible engineering
Code: `tools/task0031_actual_scoring.py`; regression: `tests/test_task0031_actual_scoring.py`. Full suite **302 passed**. Read-only original data: the verified TASK0024/TASK0025 independent Windows backups. Official score evidence: `TASK0030-RESULT-EVIDENCE/VERIFIED_SCORE_CANDIDATES.json` and preserved publisher raw official responses and SHA-256. Numerical experiment output: `TASK0031-ACTUAL-SCORING.json`, in the Windows `EVLab-Data-Backups/official-20261018` evidence root.

## Decision
**ACCEPT** this stage as a real and auditable predictive-quality *market baseline*.
**NO-GO** on EV claims/return optimization yet. Next substantive investigation should benchmark an independently justified probability estimate against these fixed quote-derived probabilities, with pre-kickoff cutoff sensitivity and no outcome leakage, or establish whether the 126 samples are sufficient for reliable calibration. No value in adding more generic infrastructure.
