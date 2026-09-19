# ChatGPT ↔ WorkBuddy Collaboration Protocol v1.0

## 1. Roles

- Project Owner (Li): decides goals, scope, budget, and final product decisions.
- ChatGPT / Reviewer: decomposes work, writes task files, reviews evidence and diffs, accepts or rejects work.
- WorkBuddy / Executor: reads assigned task files, executes only the stated scope, validates its work, and writes a report.

No executor may self-approve its own work.

## 2. Repository as the handoff ledger

The Git repository is the authoritative handoff record.

- TASKS/: instructions from ChatGPT to WorkBuddy.
- REPORTS/: WorkBuddy completion reports and evidence.
- REVIEWS/: ChatGPT acceptance/rejection reviews.
- Code/data recipes/docs: actual deliverables.

Chat messages are not a substitute for repository records when a task changes project state.

## 3. Task lifecycle

TODO → IN_PROGRESS → REVIEW → ACCEPTED

If review fails: REVIEW → REJECTED → TODO/IN_PROGRESS through a new or revised task.

Each task has one stable task ID. Reports and reviews use the same ID.

## 4. Executor rules

WorkBuddy must:

1. Read this protocol and the whole assigned task before changing anything.
2. Stay inside scope. Do not redesign architecture unless the task explicitly asks.
3. Never fabricate completion, data, test results, sources, or commands.
4. Preserve failures and report blockers exactly.
5. Do not expose or commit secrets, credentials, cookies, tokens, or personal authentication data.
6. Do not install dependencies, alter system configuration, push destructive Git history, or contact external services unless the task explicitly authorizes it.
7. Before finishing, inspect git diff / changed files and run the validation required by the task.
8. Write REPORTS/<task-id>.md containing: summary, files changed, commands/tests run, results, unresolved issues, and commit hash if committed.
9. Set the task status to REVIEW only after the report exists.

## 5. Reviewer rules

ChatGPT must independently inspect the report and relevant repository changes. A report is evidence, not proof.

Review outcomes:

- ACCEPTED: requirements met and evidence is sufficient.
- REJECTED: concrete defects or missing evidence exist. The review states exactly what must be corrected.

Review is written to REVIEWS/<task-id>.md.

## 6. Minimal task schema

Every task file must contain: Task ID, Status, Owner, Objective, Context, Allowed changes, Forbidden changes, Required steps, Acceptance criteria, Required report path.

## 7. Safety / research discipline

Existing project research rules remain authoritative. In particular: no future-information leakage, no fabricated real-world data, explicit provenance, append-only experiment history, and recommendation must remain separate from execution.

## 8. Versioning

Changes to this protocol must be deliberate and committed. A protocol change does not silently alter already-running tasks unless the task is explicitly migrated.
