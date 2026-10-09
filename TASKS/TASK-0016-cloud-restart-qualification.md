# TASK-0016 — Cloud collection restart qualification

- Status: ACCEPTED
- Date: 2026-10-09
- Owner Li; Executor/Reviewer ChatGPT
- Goal: Determine whether cloud collection can resume safely after TASK-0015 revealed persistent successful-but-empty official responses.
- Existing TASK-0006 is sealed/historical; MUST stay inactive, disabled, and unchanged.
- Before any restart: inspect cloud service, storage, current official endpoint using same documented request headers, and existing CLI bounds.
- Pilot authorization: up to **two rounds** using a brand-new data directory, phase QUALIFICATION, 60-second interval; check official source match counts/failures and ledger. This is NOT a new sealed, deployable, indefinitely running production acquisition and does not establish reference-market quality.
- If official empties, repeated failures, or other nonzero result: stop and document failure. Don't bypass upstream restrictions.
- No service enable or indefinite background run under this task.
- Record commands, exact proof and costs, test, REVIEW, commit and push.
