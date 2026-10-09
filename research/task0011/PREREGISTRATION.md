# TASK-0011 Phase B preregistration — A04 rest differential vs opening market

- Date: 2026-10-09; freeze **before** any candidate-specific result computation.
- Evidence: HISTORICAL RETROSPECTIVE EXPLORATORY only; not independent OOS, not a Sporttery execution/EV study.
- Input: existing `history/_review/09_data_历史与赛程/data/hist_v2.csv`. Record SHA-256 at run. Never edit input.
- Fixture key: normalized (league `lg`, season `season`, date `date`, home `home`, away `away`) with duplicates excluded, exact date parsed day-first.
- Define prior fixture chronologically for same club within same `lg` + `season`; no future fixtures allowed to construct rest days. Exclude season debut and multiple ambiguous team fixtures on same calendar date. Rest = calendar days since last fixture in same league-season (not all competitions: known undermeasurement).
- Predictor = home rest days minus away rest days, restricted to [-30,30] and nonnegative input gaps; focus groups: home advantage >=3 days, away advantage <=-3 days. Exclude intermediate [-2,+2] from primary group comparison but report all-groups coverage.
- Opening market: finite `PSH/PSD/PSA` >1 each, multiplicative devig `p_i=(1/odds_i)/sum(1/odds)`. Opening quotes must be distinct from `PSCH` closing. Do not use results for feature calculation.
- Target: home-win indicator from `ftr` H/D/A. Residual `r=1(H)-pH`. **Primary contrast** = mean residual among home advantage group minus mean residual among away advantage group. Positive indicates rest advantage not fully reflected by opening 1X2 home-win probability.
- Units: distinct match rows, group comparison; do not treat repeated fixtures/teams as fully independent. Report league-season subgroup coverage and match counts.
- Uncertainty: fixed seed 1109, 2,000 bootstrap replications of **league-season clustered samples** resampling groups `(lg,season)` with replacement, all matches within each group; 95% percentile CI. If <8 league-season groups or <50 fixtures in either advantage group, deem INCONCLUSIVE. Report simpler descriptive result as secondary.
- Negative control: compare rest advantage group sign with actual baseline probability difference (descriptive); no tuning of advantage cutoff or thresholds.
- Decision: if CI includes zero => NOT VALIDATED. If CI excludes zero => exploratory association only; require separate point-in-time, independent competition and verified information coverage before any economics. No stake/ROI claims.
- Avoid selecting subsets or modifying cutoff after seeing result; duplicates, missing, and parse exclusions reported. Cross-check group counts and means with an independent minimal script that doesn't import main implementation.
