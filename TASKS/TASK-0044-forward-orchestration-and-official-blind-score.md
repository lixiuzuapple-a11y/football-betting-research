# TASK-0044 — Bounded prospective orchestration and official-only blind scoring

Date: 2026-10-30. Project scope: EV-Lab football-betting-research only.

## Objective
Close the gap between the already verified TASK-0043 prospective prediction freeze and future matched official final-result scoring. Reuse original official collector, prior identity/model freeze, and official result endpoint; do not build a new predictor.

## Requirements
1. Bounded **one-off** official capture from fixed public Sporttery endpoint into a fresh off-Git evidence root. Reuse fixed historical model and previously reviewed identity bridge, fail closed on invalid source and no valid fixtures. No overwrite.
2. Previously committed fixture IDs must not be included in subsequent freeze outputs. Protect against selection/re-forecast after observing other model outputs or future results. New local output is explicitly *not* externally anchored until a subsequent pre-kickoff Git commit; never claim automatic Git publication.
3. Scoring gate must load the immutable original prospective full freeze and match its SHA and probabilities to Git's prior immutable commitment. No scoring until **three hours after the latest fixture kickoff**.
4. Reuse the official Sporttery result API; preserve received raw bytes and SHA/URL/time evidence off Git; accept only verified full-time status (2), full-time score and exact official match+home/away/date identity; require *all* frozen targets before claiming full-stage scoring.
5. Score all four fixed models with Log Loss, Brier3 and accuracy. Never optimize/select a winner on just the two future results. No betting, no executable Pinnacle, no CLV/ROI/profit inference.
6. Negative controls: source mutations, manipulated forecast, premature results, duplicate/missing results, unknown teams, empty cohort, capture repetition, no overwrite. Entire existing regression suite must pass.
7. End-to-end manual bounded live test from genuine official capture and final independent QA; only claim active unattended scheduling if an actual installed and independently verified schedule exists.

## Boundaries
This is primarily a **reusable on-demand command line pipeline**. Building working subcommands does not itself deploy a scheduler/daemon, and pending October 31 results must remain PENDING until independently observed. The machine's wall clock and Git record are not trusted timestamp authority.

Status: **ACCEPTED for engineering and scheduled-job registration**, independent
review 2026-10-30. The one-time future Oct31 real final-result score and
permanent production-grade scheduling remain **PENDING / NOT ACCEPTED**.
See REPORTS/EVLAB-TASK0044-FORWARD-PIPELINE-AND-SCHEDULE-20261030.md
and REVIEWS/EVLAB-TASK0044-INDEPENDENT-QA-20261030.md.
