# NBA totals: early-season market-bias pilot (frozen before data evaluation)

- Date: 2026-10-30 (Asia/Shanghai)
- Status: exploratory research exception authorized by Owner on 2026-10-30; **not** full basketball project activation. Football mainline remains primary.
- Source candidate: `https://raw.githubusercontent.com/aaryanshah607/nba-line-sheet/main/nba_odds_clean.csv`, independently downloaded with HTTP status, byte size, SHA256. Public third-party compilation, *not* yet independently licensed/provenanced or matched to China Sports Lottery odds.
- Aim: test whether an early-season NBA **total-points line** shows a stable over/under settlement imbalance.

## Frozen definition before outcomes

1. Season key: season starts in calendar year `Y` if game date month >= 9; otherwise `Y-1`. Use complete seasons 2007..2025 as available. `season_day = date - earliest recorded game date of that season` (not official season-opener; a limitation). This September split correctly groups the exceptional July/August 2020 NBA restart with 2019-20 rather than 2020-21. **Pre-outcome correction after inspecting only file schema; no outcome-rate analysis yet.**
2. `early`: season days 0..29. `comparison`: season days 30..119; later games excluded, as are invalid/missing totals or final scores. Each record must be identifiable by (date, home, away). No in-game or future features used.
3. Outcome: final combined points > recorded `OU` = OVER; < `OU` = UNDER; equal = PUSH. Pushes are excluded from over-rate denominators and separately reported. Only raw final points and historical OU are read.
4. Exploratory (training) seasons 2007..2020; **holdout** seasons 2021..2025. Neither definitions nor thresholds may be changed after seeing holdout results. Per-season rates are required.
5. Primary statistic: difference in over-rate early minus comparison, both overall and by chronological split. Two-sided pooled-proportions z test on the holdout; require n>=500 graded early games in holdout, p<0.05, absolute gap >=3 percentage points, same sign as training gap, and at least 3/5 holdout season-level differences with same sign to consider a candidate signal. Otherwise NO-GO for this fixed hypothesis.
6. Secondary descriptive metric: early over-rate relative to 50%, Wilson 95% confidence interval. No multiplicity-adjusted discovery claims; no exploration of month cutoffs or subgroups to search for a success in this pilot.
7. Missing odds/actual stake prices, uncertain open/close timestamps, external provenance and book comparability mean **no EV / ROI / CLV** conclusions are permitted even if a statistically significant over-rate is found. Selection odds can absorb any hit-rate edge. These issues are independent blockers for real-money conclusions.
8. Reject or downgrade if source has duplicates, erroneous season coverage, suspicious line/result patterns, or unreliable provenance. A simulation on this public sample is not the Chinese lottery.

## Intended deliverables

- Source URL, download hash and audit counts; deterministic standard-library script and full numerical outputs; independent QA and concise GO / NO-GO / INCONCLUSIVE verdict.
- Persist only light reproducible evidence to this repository; no continuous basketball collection, paid data, live service, gambling action or modification of football infrastructure.
