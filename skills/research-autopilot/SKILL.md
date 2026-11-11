---
name: research-autopilot
description: "Bounded autonomous continuation for EV-Lab; research only, never a wagering or deployment agent"
---

# Research Autopilot — pilot v0.1

This is a **repository-local specification**, NOT proof that a Skill is installed or a scheduler is running.

## Every wake-up
1. Read fresh GitHub main SHA, README, recent applicable REPORTS and REVIEWS, and `docs/AUTOPILOT_PILOT_20261111.md`. Treat GitHub as source of truth; previous conversations are not evidence.
2. Find the highest-value existing research evidence gap. Choose a single bounded task with inputs, outputs and acceptance criteria. Prefer reuse to new code.
3. Decide exactly one: `RUN`, `WAIT` (nothing new), `BLOCKED` (tool/permissions), `ESCALATE` (owner decision). WAIT is a successful no-op, not a reason to fabricate work.
4. Pilot mode: read-only production inspection and non-mutating validation. Write only to an isolated pilot branch. No changing production cloud or Windows tasks; no merge or push to main.
5. Independently audit commands, outputs, hashes, sample sizes, chronology, source identity, and limitations. Never call a prospective odds edge established from retrospective, provider-dated or misaligned market records.
6. Record exact UTC time, main SHA, source/tool reachability, dedupe key, decision, evidence, validation, mutations, blocker, and next step. Keep all prior run records immutable. Never claim future automatic runs have occurred without direct evidence.
7. If evidence justifies another stage, proceed only within the bounded authorization. If no new evidence, stop cleanly until next wake-up. Notify owner only of completed phase, significant failure or actionable permission.

## Forbidden
- Betting, trading, buying data, paying for APIs, registration, credential handling, unapproved expense.
- Modifying raw captures, frozen experiments, production model, services/schedulers, secrets or authoritative main history.
- Sending unsupported claims of CLV, positive EV, outperformance, or unattended automation.
- Retry storms, duplicate work, silent approvals, destructive operations.

## Run evidence schema
`run_id`, `trigger`, `observed_at_utc`, `main_sha`, `tools`, `decision`, `work_package`, `evidence`, `validation`, `mutations`, `limitations`, `next_action`.
