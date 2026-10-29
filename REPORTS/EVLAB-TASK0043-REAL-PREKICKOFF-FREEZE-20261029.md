# EV-Lab TASK-0043 — Verified genuine pre-kickoff multi-model freeze

Date: 2026-10-29 (Beijing). Research-only, actual external source and real future fixtures.

## Source, model and time facts

- One genuine official HTTP200 capture, **19 matches**, at
  `2026-10-29T07:31:11.376632+00:00` (=15:31:11 CST); original SHA256
  `4fecde60266a7f99fcf10b6aeed3ab1883ad17d8394e0f2f56bc3f93f1b42767`.
  Original raw+SQLite stored **off Git** in
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0043-live-single-20261029`,
  source code commit `6549e90df1d64feb808f8d8ef1c5031a50d4a25c`.
- **Freeze created 2026-10-29 15:36:26.021565 CST** before both matches.
  Create-only complete artifact off Git,
  `task0043-multimodel-forward-20261029/TASK0043-PROSPECTIVE-FORECAST-FREEZE.json`.
  Full artifact SHA256 `3bb96003e370f45bc60c9656d76542bf3444cd5b19a3d2575c303e66e4d670b3`.
- History: source HF July 2026 published `2026-07-05T01:23:18Z`,
  manifest SHA `eb3c37793866a27f8c1520c78a69e6098fdf79f08622b37fed64070fa1f8748f`,
  fixtures SHA `7ba90661dbed29eb940daf5ea385c7d76d5751d16be86bd9063293a982abc7b7`.
  **53,705** unique games after deduplication (916 identical duplicates removed);
  latest training match date **2026-07-04**. No October 2026 labels or
  target match results in training. Publisher timestamp, while retained,
  is not a third-party cryptographic notarization.
- Pinned prior independent 35-match TASK0037 cup-identity ledger SHA
  `13d373dbab8363e606cfaf39c478b6035c35c86ad0ffcbf4c53e6e5014f63f2f`,
  then reused its vetted official IDs/Chinese names→ESPN names→HF team IDs.
  Reconfirmed exact HF team table and domestic league name/country pairs.
  No new approximate aliases derived from today’s fixture outcomes or prices.
- Reused *unchanged* frozen Phase3 `State` 1X2 implementation,
  global+league frequency, pooled Elo/Davidson and league Poisson.
  Only a score-free `Scheduled` model input was added to reuse the exact
  tested numerical routines without manufacturing target score fields.

## Eligibility: 2 of 19

- **15** excluded because the league was not in the deliberately frozen
  France/Norway model scope; **2** rejected because both official team
  identities were not independently approved. **2** qualified with both
  Elo and Poisson; no team or model parameter was tuned to these matches.
- No official HAD/Pinnacle price is sent to model; these forecasts are
  not buy recommendations.

| Official matchId / real future fixture | Beijing kickoff | Fixed Elo/Davidson H/D/A | Fixed league Poisson H/D/A |
| --- | --- | --- | --- |
| `2042359` 博德闪耀—维京 | 2026-10-31 02:00 | 0.425773 / 0.257185 / 0.317042 | 0.700542 / 0.171237 / 0.128221 |
| `2042364` 里尔—朗斯 | 2026-10-31 04:05 | 0.351726 / 0.259013 / 0.389261 | 0.326940 / 0.256829 / 0.416231 |

Both also have independent global/league frequency control vectors in the
frozen derivative `research/task0043_pre_kickoff_multimodel_freeze_20261029.json`,
which pins source and training hashes. The considerable inter-model
disagreement, especially the Norwegian fixture, is an uncertainty marker,
not an opportunity to select a model after results are known.

## Reproducibility / regression

- Independently reloaded each unchanged original file, re-verified the
  full historical raw manifest, reconstructing all 53,705 training matches;
  reran the production freeze with exactly the original freeze timestamp.
  Entire resulting dictionary matched frozen original **EXACT**.
- Eight new source/time/identity/outcome-price isolation tests:
  market odds and target result mutations cannot change model predictions;
  bad time, stale/future capture, SHA tamper, duplicate match, unknown
  league/team and changed historical approved bridge fail closed.
- New tests **8/8 passed**, including in pinned DuckDB sandbox.
  Full EV-Lab repository **405 passed**.
- During test-first validation an incorrectly transcribed bridge SHA
  initially caused safe failure before any freeze was created; corrected
  by comparing file digest. No partial model output was accepted or
  overwritten. An irrelevant test-fixture missing-parent-directory error
  was also corrected, then all tests rerun.

## Verdict and next engineering gate

**ACCEPT** first two real, ahead-of-kickoff research Poisson+Elo forecasts
reusing approved historical models and frozen pre-match identities.
**PENDING** automation: safe recurring capture → strict identity admission
→ proactive model freeze → independent official final-score capture/scoring
on a future cohort. Also PENDING actual price timing, real Pinnacle market,
CLV and any economic profitability. Refuse automatic bets/BUY.
