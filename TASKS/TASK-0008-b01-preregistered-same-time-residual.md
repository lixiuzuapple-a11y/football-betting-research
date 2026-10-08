# TASK-0008 — B01 pre-registered same-time Sporttery vs reference_proxy residual

- Task ID: TASK-0008
- Status: ACCEPTED
- Owner: Li
- Lead / Executor / Reviewer-of-record: ChatGPT
- Input dataset: TASK-0006 run `20260928a`
- Input evidence grade: prospective acquisition valid / strict seal defective
- Depends on: TASK-0007 = ACCEPTED
- Scope: B01 only
- No BUY/PASS, no stake sizing, no live deployment, no claim that BetExplorer is fair probability or a named sharp market.

## 1. Research question

Using only synchronized observations already captured prospectively:

> At the same regular collection round, when the official Sporttery HAD market is provider-declared executable, does its fixed price contain a systematic residual relative to the simultaneously observed BetExplorer `reference_proxy` 1X2 probability after multiplicative de-vig?

This is a pricing-diagnostic question. A positive residual is called **proxy-implied edge**, not true EV.

## 2. Known information before this preregistration

Known from TASK-0007 before TASK-0008:

- current identity layer conservatively matches 19 Sporttery fixtures to BetExplorer events;
- BetExplorer source variants can behave materially differently;
- D01-B change events for matched fixtures were dominated by mass synchronized batches;
- almost all positive D01-B proxy-EV instances were already positive before the detected reference move.

Not inspected for B01 before this task:

- the full synchronized-round distribution of Sporttery-vs-reference residuals;
- residual frequency by selection;
- persistence across rounds;
- variant-stratified B01 residual distributions;
- fixture-level concentration of residuals;
- later reference-direction validation for all synchronized B01 observations;
- realised-outcome calibration/ROI for B01.

Rules below are frozen before opening those B01 results.

## 3. Reuse-first inventory

Must reuse where applicable:

1. `src/football_betting/prospective/ledger.py` — canonical capture timing/schema.
2. `src/football_betting/matching/teams.py` — conservative identity matching.
3. `assets/team_name_map.json` — versioned current identity layer.
4. `src/football_betting/odds/implied.py` — multiplicative de-vig.
5. TASK-0007 fixture-universe/crosswalk logic where semantically identical.
6. TASK-0007 independent-audit pattern for second-path recomputation.
7. Historical B01 framing in:
   - `research/P0_EVIDENCE_RECONSTRUCTION_20260923.md`
   - `research/EDGE_EXHAUSTION_MATRIX_20260923_v1.md`

Any new reusable helper must be committed under `src/`, `tools/`, `tests/`, or `assets/`; do not leave the main calculation as a one-off shell command.

## 4. Unit of observation

Primary unit:

**one matched fixture × one regular round × one 1X2 selection**.

A synchronized round is accepted only when:

- both official Sporttery and BetExplorer regular captures share the same `round_id`;
- both captures succeeded;
- fixture identity is in the frozen conservative crosswalk;
- both observations are pre-kickoff according to the captured fixture kickoff;
- Sporttery HAD tuple is present and valid;
- BetExplorer 1X2 tuple is present and valid;
- Sporttery HAD is provider-declared executable at that capture.

Do not substitute a nearby round when one leg is missing.

## 5. Executability definition

Primary executable Sporttery HAD requires the captured HAD availability facts to support sale at that moment.

Fail closed:

- missing availability is not executable;
- closed/non-selling status is not executable;
- do not infer executability from HTML/page presence;
- do not use another pool''s availability as HAD availability.

Report single/all-up semantics separately if necessary; do not silently equate them.

## 6. Probability and residual definition

For BetExplorer decimal 1X2 tuple `O_ref = (H,D,A)`:

1. raw implied probabilities: `q_i = 1/O_i`;
2. multiplicative de-vig:
   `p_ref_i = q_i / sum(q)`.

For Sporttery executable decimal price `O_jc_i`:

`proxy_implied_edge_i = p_ref_i * O_jc_i - 1`.

Interpretation:

- `>0` means Sporttery pays more than the contemporaneous BetExplorer de-vig proxy would require for break-even;
- it is **not** true expected value unless the reference proxy is an unbiased fair probability source, which is not established.

No alternative de-vig method becomes primary after seeing results.

## 7. Pre-registered thresholds

Report the full continuous distribution and these fixed thresholds:

- > 0%
- >= 2%
- >= 5%
- >= 10%

Thresholds are diagnostics, not buy rules.

For each threshold report at minimum:

- observation rows;
- distinct fixture-selection pairs;
- distinct fixtures;
- distinct calendar days;
- concentration by fixture;
- longest/median consecutive persistence in regular rounds.

Do not present raw round counts as independent sample size.

## 8. Variant discipline — primary source-quality gate

Because BetExplorer declared variants are known to matter, results must be reported:

1. pooled across all declared variants only as a descriptive total;
2. separately by `source_variant`;
3. by fixture × variant.

A B01 residual is considered **source-robust** only if its qualitative sign/threshold presence is not dependent on one rendering variant.

Pre-registered diagnostics:

- number of variants contributing;
- residual frequency per variant;
- same fixture seen under multiple variants: compare residual sign and magnitude;
- whether threshold-positive observations cluster overwhelmingly in one variant.

Do not select a preferred variant post hoc.

## 9. Temporal persistence diagnostics

A real pricing residual should not be represented by thousands of duplicated minute snapshots as if independent.

For each fixture-selection-threshold episode:

- collapse consecutive qualifying regular rounds into one persistence episode;
- report episode count;
- start/end observation times;
- duration;
- number of constituent rounds.

Primary descriptive evidence unit for persistence is the **episode**, not every minute row.

## 10. Forward reference diagnostic

This is diagnostic only, not the primary B01 definition.

For each synchronized observation with proxy-implied edge above each threshold, examine the next valid same-variant BetExplorer observation(s) at fixed horizons where available:

- next same-variant observation;
- approximately +5 min;
- approximately +30 min;
- approximately +60 min or last pre-kickoff observation if sooner.

Question:

> Does the reference proxy subsequently move in the direction that reduces the observed Sporttery residual?

Use only future observations that were actually captured. Do not interpolate provider update times.

Report right-censoring and missing horizons.

## 11. Realised outcomes — secondary and low-power

If official/verified match outcomes are already available from a trusted source without new ambiguous matching, a secondary calibration check may be run **only after** the pricing analysis is frozen and saved.

Because the dataset covers very few independent fixtures:

- no ROI/profitability conclusion from minute-level rows;
- no repeated round from one fixture may be treated as an independent bet;
- at most one pre-defined observation per fixture-selection can enter any outcome-based check.

Default representative observation if outcome validation is performed:

**last executable synchronized observation at least 10 minutes before kickoff**.

If no such observation exists, exclude that fixture.

Outcome analysis must be labelled exploratory/low-power unless independent fixture count is sufficient.

## 12. Concentration and effective sample size

Always report:

- distinct fixtures;
- distinct fixture-selection pairs;
- episodes;
- calendar days;
- per-fixture share of all threshold-positive rows/episodes.

Flag any result where a small number of fixtures dominate.

No IID confidence interval over minute-level rows.

If uncertainty is estimated, cluster/resample at fixture level, not row level.

## 13. Primary falsification / downgrade conditions

B01 with current `reference_proxy` is downgraded if any of the following dominates:

1. apparent positive residuals are primarily one rendering variant and reverse/disappear under other variants for the same fixtures;
2. threshold-positive rows collapse to only a trivial number of independent fixture episodes;
3. the residual is mostly a persistent static cross-source level difference with no supporting forward-reference movement;
4. positive residual magnitude is not stable enough across fixtures/days to support a general mechanism;
5. identity/executability/timing coverage is too sparse for an honest test.

B01 is **not validated** merely because many minute rows exceed zero.

## 14. What would count as useful support

Support requires all of:

- exact same-round matched observations;
- provider-declared Sporttery executability;
- multiple independent fixtures and days;
- residual episodes not dominated by one fixture;
- no single source variant solely creating the sign;
- at least some forward-reference evidence consistent with a genuine relative-pricing residual.

Even then the result remains `reference_proxy` evidence, not named-sharp/fair-value proof.

## 15. Required implementation

Prefer extending TASK-0007 assets rather than creating parallel matching logic.

Expected reusable outputs may include:

- `src/football_betting/analysis/b01.py`
- `tools/task0008_b01.py`
- `tools/task0008_independent_audit.py`
- `tests/test_task0008_b01.py`
- `results/task0008/`
- `REPORTS/TASK-0008.md`
- `REVIEWS/TASK-0008.md`

If existing TASK-0007 code can cleanly generalize, refactor it rather than copy/paste.

## 16. Validation before real analysis

Before reading real B01 results:

1. synthetic tests for same-round pairing;
2. executable/non-executable fail-closed cases;
3. de-vig/residual arithmetic tests;
4. variant stratification tests;
5. episode-collapse tests;
6. future-horizon censoring tests;
7. full repository test suite;
8. `git diff --check`;
9. Ruff where available.

Commit analysis code/tests **before** the first real B01 result run.

## 17. Independent recomputation

After main analysis:

- build/run a second audit path that does not import the primary B01 analysis module;
- independently recompute at least:
  - accepted synchronized observation count;
  - threshold counts;
  - distinct fixtures;
  - episode counts;
  - variant strata;
  - forward-reference direction summary.

Any material disagreement blocks acceptance.

## 18. Output and interpretation rules

Report separately:

- acquisition/matching coverage;
- continuous residual distribution;
- fixed-threshold counts;
- fixture/episode concentration;
- variant robustness;
- forward-reference diagnostics;
- optional outcome check.

Never call `proxy_implied_edge` true EV.

Do not create BUY/PASS.

Do not tune thresholds/leagues/teams after seeing results.

## 19. Final decision vocabulary

Use one of:

- `B01 WITH CURRENT REFERENCE_PROXY = NOT VALIDATED / DOWNGRADE`
- `B01 WITH CURRENT REFERENCE_PROXY = WEAK SUPPORT / NEEDS REPLICATION`
- `B01 WITH CURRENT REFERENCE_PROXY = PROSPECTIVE SUPPORT / NEEDS NAMED-SHARP OR LIVE VALIDATION`

No stronger wording is authorized by this task.

## 20. Stop condition

After the analysis, independent audit, report, review decision and Git push:

**STOP.**

Do not launch live betting or a new collector automatically.
