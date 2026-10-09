# TASK-0014 — Official Sporttery-only prospective data requalification

- Status: ACCEPTED
- Owner: Li; Executor/Reviewer: ChatGPT
- Date: 2026-10-09
- Existing cloud dataset: /home/ubuntu/evlab-data/task0006-sealed-20260928a/ledger.sqlite3
- Prior gate TASK-0006: REJECTED strict sealing, preserved prospective raw/data.
- This is **data fitness/capability audit**, not a hypothesis/ROI hunt.
- Official source only. BetExplorer observations are excluded from all calculations.

## Freeze before analysis
Read SQLite using immutable read-only URI; don't restart collector or alter frozen checkout. Examine official regular and confirmation captures separately; count distinct rounds, unique provider timestamps, match IDs, date and pool executable availability; avoid treating repeated poll rows as independent events. Assess presence of HAD standardized facts, and separately inspect bounded raw official payload to determine actual availability of HHAD/TTG/CRS/HAFU and whether there is maintained extraction for these. Check observed timestamp vs source timestamp and run integrity, quote-change frequency, and playable intervals. Identity and close-time constraints must be measured, not inferred.

## Outputs
- executable audit with transparent exact SQL, denominator and safeguards
- independent cross-check counts by alternative query
- table of supported/unsupported question families
- REPORT/REVIEW, technical limits and next falsifiable experiment proposal if feasible
- no economic/positive-EV claim, no live wagering
- commit and push repo, clean tree

## Gate
ACCEPT only the documented measured source/data qualification and identify next test support. A statistically attractive residual without real contract/executability is not a passing result.
