# TASK-0001 — Collaboration smoke test

- Task ID: TASK-0001
- Status: REVIEW
- Owner: WorkBuddy
- Reviewer: ChatGPT
- Risk: Low

## Objective

Prove that WorkBuddy can receive a task through this Git repository, read the collaboration protocol, inspect the repository, and return a structured report for independent review.

## Context

This is a handoff test, not a development task. The repository already contains the Stage 1 football-betting research foundation. Do not modify that foundation.

## Allowed changes

1. This task file: change only Status from TODO to IN_PROGRESS, then to REVIEW when complete.
2. Create exactly one report: REPORTS/TASK-0001.md.

## Forbidden changes

Do not modify files under src/, tests/, docs/, data/, research/, or results/. Do not modify README.md, pyproject.toml, CI, .gitignore, COLLABORATION.md, or the directory README files. Do not install packages. Do not change Git configuration or remotes. Do not use or expose credentials/tokens. Do not create synthetic research data. Do not implement features, models, backtests, or betting logic.

## Required steps

1. Read COLLABORATION.md.
2. Inspect repository status, current branch/HEAD, top-level structure, Python availability, and whether pytest can be invoked.
3. Do not fix any problem you find. This task is observation only.
4. Create REPORTS/TASK-0001.md with: protocol version read; current branch and HEAD; concise top-level repository structure; Python command(s) found or not found; pytest availability/result if safely invokable; exact commands used; blockers/anomalies; files changed by this task.
5. Verify that only this task file and REPORTS/TASK-0001.md changed.
6. Change this task status to REVIEW.

## Acceptance criteria

Report exists at the required path; no forbidden file changed; report contains only observed facts; commands and failures are recorded; task status is REVIEW.

## Required report path

REPORTS/TASK-0001.md
