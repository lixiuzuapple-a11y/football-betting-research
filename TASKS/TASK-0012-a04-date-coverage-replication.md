# TASK-0012 — A04 mixed-date complete-coverage replication
- Status: ACCEPTED
- Date: 2026-10-09
- Owner: Li; Executor/reviewer: ChatGPT
- Parent frozen outcome: TASK-0011 inconclusive, SHA c5cd9dbb3f75ed06136146b8eb5c9baa54edb880b0d27f2c893fe2c6920e568a.
## Frozen correction before any rerun
Only parser correction: accept exact `%d/%m/%y` OR `%d/%m/%Y`, day-first. No date inference, no outcome-conditioned filtering. Keep original TASK-0011 other rules: same league-season previous fixture, no ambiguous/duplicate identities, previous rest 1–30 days, diff >=+3 vs <=−3, Pinnacle PSH/PSD/PSA proportional de-vig, primary home-win residual contrast, 2000 league-season bootstrap draws seed 1109, >=8 clusters >=50 fixtures per primary arm. Data path hist_v2.csv and SHA before execution; abort on mismatch. This is historical retrospective, not independent temporal OOS; known historical outcomes were already in old project.
## Execution/review
Clone TASK-0011 scripts to new version; modify date parser only; add synthetic mixed-format test; run primary and algorithmically independent audit with mixed format; verify exclusions, group counts, CI and output hashes. Inspect possible date ambiguity/era defects, season chronology and clustering. If additional implementation bugs observed, document and fix only non-research algorithm defects with test; substantive hypothesis changes require future task. Report meaningful limitations and explicit result gate. No data collection/betting.
## Deliverables
`tools/task0012_rest_a04.py`, `tools/task0012_rest_a04_audit.py`, tests, `research/task0012/` results, REPORT and REVIEW; Git commits for frozen spec and final submission.
