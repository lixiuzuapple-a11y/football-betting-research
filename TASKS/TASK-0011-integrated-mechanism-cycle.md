# TASK-0011 — Integrated mechanism selection and falsification cycle

- Status: IN_PROGRESS
- Owner: Li
- Lead / Executor / Reviewer-of-record: ChatGPT
- Start date: 2026-10-09
- Prerequisite: TASK-0010 executable evidence audit at `bdf16c8`.
- No external executor unless necessary.
- Scope: ONE integrated research cycle; no further sub-TASKs for normal phases.

## Hard boundaries
No live betting, BUY/PASS, account/credential changes, paid data, lengthy cloud collection, production service restart or alterations to frozen TASK-0006 raw data. No performance fishing or outcome-based mechanism selection. Preserve historical failures and known data limitations. Treat GitHub as canonical.

## Phase A — candidate triage (before experiment results)
Inspect existing Edge Exhaustion Matrix, TASK-0010 evidence, actual data schema/density, available reusable analysis/tests and known bug lineages. Score candidate mechanisms on: novelty vs prior tests; testability with existing point-in-time data; contract/executability validity; credible falsification; expected incremental information; data/compute cost. Record all candidates, disqualifications and fixed ranking rule in `research/task0011/SELECTION.md`. Do not pick based on favorable past ROI/target outcomes. Choose ONE with a strictly defined hypothesis. Prefer a diagnostic/falsification test feasible using existing data over speculative profit forecasts.

## Phase B — preregister before opening candidate result data
Freeze `research/task0011/PREREGISTRATION.md` in its own Git commit and push before executing the selected experiment or reading its candidate-specific results. Prespecify input manifest/path/hash, experimental unit, time split, exact feature and outcome/proxy definition, inclusion/exclusion, negative controls, baseline, primary metric, uncertainty, stopping and FAIL criteria. Do not use historical outcomes that were already examined for candidate selection; if no genuinely uninspected data exists, label analysis **retrospective/exploratory** and do not claim prospective validation.

## Phase C — real execution
Reuse versioned `src/`, `tools/`, `history/`, `results/` and available cloud snapshots; inspect raw provenance first. Write only necessary reusable scripts, tests and documented command entrypoints in repository. Run actual tests and actual numerical analysis. Handle access blockers explicitly, never fabricate metrics; if no qualified data exists, stop at evidence-based BLOCKED without invented substitute.

## Phase D — independent QA and decision
Run an algorithmically independent cross-check of critical metrics and guard against lookahead, duplicate fixture rows, outcome/threshold cherry-picking, and economics that ignore official executability/overround. Report observed effect, sample sizes, effective independence, limitations and negative findings. Document same-agent implementation/review limitation.

## Outputs and final gate
- `research/task0011/SELECTION.md`
- `research/task0011/PREREGISTRATION.md` (frozen commit before any candidate-specific run)
- versioned reusable code/tests where needed
- result summaries and reproducible command evidence
- `REPORTS/TASK-0011.md` and `REVIEWS/TASK-0011.md`
- final outcome: PROCEDURE ACCEPTED/REJECTED and separately HYPOTHESIS VALIDATED/NOT VALIDATED/INCONCLUSIVE/BLOCKED.
- Push all approved artifacts to origin/main with clean worktree; do not claim validation from a small exploratory sample.

## Stop criteria
If no test can satisfy time integrity and coverage with available data, record concrete blocker and close honestly. If mechanism fails frozen falsification gate, report negative result and DO NOT switch post-hoc to runner-up within TASK-0011. Next distinct hypothesis requires another formal task.
