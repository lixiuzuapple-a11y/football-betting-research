# ChatGPT ↔ WorkBuddy Collaboration Protocol v2.1

This file is the operating contract for AI-to-AI work in this repository.

## 1. Roles and authority

- **Project Owner (Li):** sets goals, scope, budget and final product decisions.
- **ChatGPT / Reviewer:** decomposes work, creates formal tasks, reviews repository evidence, accepts/rejects work and writes review records.
- **WorkBuddy / Executor:** executes assigned tasks, validates its work and writes execution reports.

WorkBuddy must not self-approve. ChatGPT must not accept work solely from WorkBuddy's chat summary.

## 2. GitHub is the authoritative handoff ledger

Formal project state lives in the repository:

- `TASKS/` — instructions from ChatGPT to WorkBuddy.
- `REPORTS/` — WorkBuddy execution reports/evidence.
- `REVIEWS/` — ChatGPT review decisions.
- source/docs/research files — actual deliverables.

Chat messages are notifications only. If chat and the current remote repository disagree, the current remote repository wins.

## 3. Mandatory synchronization before reading

**This rule is compulsory.**

Before WorkBuddy reads a task, review, protocol, or project state, it must synchronize with remote `main`.

Minimum sequence:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git status -sb
```

Then WorkBuddy must read the current `COLLABORATION.md` and relevant task/review from the synchronized working tree.

Do not claim that a task, report, review or instruction is missing until this synchronization has been attempted and the remote state checked.

If synchronization fails, stop and report the exact error. Do not guess from a stale local clone.

## 4. Task lifecycle

`TODO → IN_PROGRESS → REVIEW → ACCEPTED`

Failed review:

`REVIEW → REJECTED → IN_PROGRESS → REVIEW`

Rules:

1. ChatGPT creates a task with a stable task ID.
2. WorkBuddy may change `TODO` to `IN_PROGRESS` only when it actually starts.
3. WorkBuddy creates `REPORTS/<task-id>.md` and changes status to `REVIEW` only after required work and validation are complete.
4. Only ChatGPT/Reviewer may change `REVIEW` to `ACCEPTED` or `REJECTED`.
5. ChatGPT records the decision in `REVIEWS/<task-id>.md`.

## 5. WorkBuddy execution discipline

For every task WorkBuddy must:

1. Synchronize remote `main` as defined in section 3.
2. Read the latest protocol and the entire assigned task.
3. Check allowed changes, forbidden changes and acceptance criteria before editing.
4. Stay strictly inside scope.
5. Never redesign architecture unless explicitly authorized.
6. Never fabricate completion, data, sources, commands, tests or results.
7. Preserve failures and blockers exactly.
8. Never expose or commit passwords, tokens, cookies, credentials or personal authentication data.
9. Do not install dependencies, alter system configuration, change Git remotes/configuration, rewrite Git history, force-push, deploy, or contact external services unless the task explicitly authorizes it.
10. Inspect changed files/diff before submission and run the validations required by the task.
11. Write the required report with commands, evidence, changed files, results, blockers and commit information.
12. Push the authorized deliverable to the specified branch/remote when the task requires GitHub handoff.
13. After submission, **STOP**. Do not start adjacent work, investigate a new topic, design the next feature, change permissions, or "helpfully" continue beyond scope unless a new formal task or explicit Owner/Reviewer instruction authorizes it.

## 6. WorkBuddy completion message

After a task is pushed for review, WorkBuddy's chat message to the Owner should be short and factual:

- task ID;
- status = REVIEW;
- pushed commit hash;
- report path;
- any blocker requiring Owner action.

Do not call the task `ACCEPTED`, `closed`, or finally completed. Acceptance belongs to ChatGPT/Reviewer.

## 7. WorkBuddy handling of reviews

When told that ChatGPT has reviewed a task, WorkBuddy must first synchronize remote `main` using section 3, then read:

`REVIEWS/<task-id>.md`

and the current task status.

- If `ACCEPTED`: acknowledge the review and stop. Do not perform more work.
- If `REJECTED`: read the concrete findings and wait for/execute only the authorized correction scope.

WorkBuddy must not say "I cannot see the review" based only on an unsynchronized local clone.

## 8. Reviewer discipline

ChatGPT/Reviewer must:

1. Fetch/read current remote state before review.
2. Inspect actual diff/commits and relevant files independently.
3. Treat WorkBuddy's report as evidence, not proof.
4. Check task scope and forbidden-path violations.
5. Record findings in `REVIEWS/<task-id>.md`.
6. Set task status to `ACCEPTED` or `REJECTED`.
7. Commit and push the review so WorkBuddy can retrieve it from GitHub.

## 9. Minimal task schema

Every formal task contains:

- Task ID and Status
- Owner / Reviewer
- Objective and context
- Allowed changes
- Forbidden changes
- Required steps
- Required validation/evidence
- Acceptance criteria
- Required report path
- Git/branch/push instructions when relevant

## 10. Concurrency and conflict rule

One task must not overwrite another task's unreviewed work.

Before starting, inspect `git status` and remote history. If unexpected tracked changes, divergence, merge conflicts or another active task touch the same files, stop and report instead of guessing.

Never use force-push to solve collaboration conflicts unless the Project Owner explicitly authorizes it.

## 11. Research integrity

Existing project research rules remain authoritative, including:

- no future-information/look-ahead leakage;
- no fabricated real-world data;
- explicit data provenance and time discipline;
- failed experiments/results are retained;
- prediction, recommendation, human betting decision and execution remain distinct;
- an unimplemented capability must not return plausible fake output.

## 12. Reusable asset and automation discipline

**Reuse-first is mandatory.** Before writing a new script, downloader, parser, validator, analysis helper, report generator, deployment helper, configuration template, schema utility, or other repeatable artifact, first search the current WebCodex-managed repository for an existing implementation that can be reused or extended.

Rules:

1. Reusable automation and project tooling must live inside the corresponding WebCodex project repository (for example under `src/`, `scripts/`, `tools/`, `research/`, `deploy/`, or another clearly documented project path), not only in chat, a temporary shell command, Downloads, Desktop, or an untracked personal folder.
2. Prefer extending or parameterising an existing tool over creating a near-duplicate.
3. If a one-off diagnostic proves generally useful, promote it into a reusable tracked artifact before repeating the same work later.
4. Data acquisition, cleaning, mapping, validation, hashing, reporting, deployment and monitoring helpers follow the same rule.
5. Reusable templates, field mappings, schemas, dictionaries, endpoint knowledge and operational procedures should also be versioned in the repository when they materially reduce future rework.
6. Every new reusable artifact should have enough naming/documentation/tests that a later ChatGPT, WorkBuddy, or other executor can discover and use it without reconstructing the original chat.
7. Before starting new implementation work, record or report whether an existing asset was reused, extended, or why a new one was necessary.
8. Do not repeatedly download, scrape, transform, or recompute the same asset when a verified cached/versioned copy already exists and remains valid. Preserve provenance and freshness metadata so reuse is auditable.
9. Project-specific artifacts stay in that project's independent Git repository under the WebCodex workspace; do not create hidden cross-project coupling merely to share code. If an artifact genuinely becomes cross-project infrastructure, promote it deliberately into a separately versioned shared component.

The intent is to turn completed work into cumulative project capability: **build once, verify once, reuse many times**.
## 13. Protocol acknowledgement

Whenever WorkBuddy is explicitly sent this protocol URL or told that the protocol changed, it must:

1. synchronize remote `main`;
2. read this file;
3. reply to the Owner with exactly the following acknowledgement format:

```
ACK COLLABORATION v2.1
已同步 origin/main，并阅读 COLLABORATION.md。
我知道：开始任务前先同步；先查已有可复用资产；只按 TASKS 范围执行；可复用脚本/工具/数据流程要沉淀进 WebCodex 项目仓库；完成后写 REPORTS 并提交 REVIEW；提交后停止；收到审核通知后先同步再读 REVIEWS；只有 ChatGPT/Reviewer 可以 ACCEPTED/REJECTED。
```

This acknowledgement confirms receipt only; it does not start a task.

## 14. Versioning

Protocol changes must be deliberate, committed and pushed. New tasks use the current protocol. An already-running task keeps the protocol version under which it started unless explicitly migrated by the Owner/Reviewer.
