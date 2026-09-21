# TASK-0003 — Legacy asset triage and conversation handoff

- Task ID: TASK-0003
- Status: TODO
- Owner: Li
- Reviewer: ChatGPT
- Executor: WorkBuddy
- Risk: Low
- Type: documentation / classification only

## Objective

Classify the frozen legacy football-betting research assets into a controlled reuse plan for the new GitHub project.

This task answers one question only:

> Which legacy assets may be inherited as infrastructure/reference, which should remain archive-only, which require independent revalidation before any reuse, and which cannot yet be classified because evidence is insufficient?

This task does **not** restart football research, rerun experiments, retrain models, repair collectors, backfill data, or decide whether any historical betting conclusion was correct.

## Authoritative baseline

The authoritative legacy inventory is the ACCEPTED baseline under:

`legacy/2026-09-21-inventory/`

Start from the synchronized remote repository and read at minimum:

- `COLLABORATION.md`
- `TASKS/TASK-0002-legacy-inventory-import.md`
- `REVIEWS/TASK-0002.md`
- all five files in `legacy/2026-09-21-inventory/`

Do not treat older chat summaries as stronger evidence than the frozen GitHub baseline.

## Special rule: WorkBuddy currently has two conversations

WorkBuddy may receive this notification in either or both of these conversations:

1. the old **竞彩足球研究** conversation;
2. the current **GitHub / WebCodex 尝试** conversation.

The two conversations have different roles:

### Old 竞彩足球研究 conversation

Use it only as a **historical retrieval aid** for locating legacy files, old experiment names, prior notes, or context that may help identify an asset.

It is **not** an authoritative project ledger.

If an important claim exists only in old chat context and cannot be tied to a file, commit, report, script, dataset, or other inspectable evidence, label it:

`CHAT-ONLY / NOT VERIFIED`

Do not classify an asset as reusable solely because the old chat said it worked.

### Current GitHub / WebCodex conversation

Use it only for notification and operational coordination.

Formal task state, evidence, deliverables, and review live in GitHub.

### Conflict rule

If either chat conflicts with synchronized `origin/main`, **GitHub wins**.

Do not maintain two parallel versions of task state.

After the legacy migration/audit work is eventually completed, the old 竞彩足球研究 conversation is to be treated as **historical archive only**. New project work should then originate exclusively from GitHub tasks/current project conversation.

## Mandatory synchronization

Before doing any work:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git status -sb
```

Then read `COLLABORATION.md` and this entire task.

If sync fails, stop and report the exact error.

## Classification system

Every material legacy asset or coherent asset group must receive exactly one primary class:

### A — KEEP / INHERIT

Use only when the asset can be carried into the new project **without treating a historical research conclusion as trusted evidence**.

Typical candidates may include:

- generic research methodology/process documents;
- data dictionaries or source catalogs;
- reusable engineering utilities whose purpose can be verified from code;
- schemas, naming conventions, manifests, provenance records;
- raw/near-raw source data with sufficiently clear provenance and integrity evidence.

A does **not** mean “scientifically validated” or “profitable”. It means “safe to retain as reusable infrastructure/reference under stated limitations”.

### B — ARCHIVE ONLY

Historical material worth preserving for traceability but not intended to feed the new research pipeline directly.

Typical candidates may include:

- superseded reports;
- old experiment narratives;
- obsolete scripts;
- duplicate copies;
- prior conclusions;
- abandoned branches/approaches;
- presentation/HTML copies of results already represented elsewhere.

B assets remain available for audit/history but should not become new-project evidence by default.

### C — REVALIDATE BEFORE USE

Potentially valuable assets that must not enter new analysis until independently checked.

Typical triggers include:

- derived datasets;
- joins/alignment tables;
- cleaned/normalized data where transformations matter;
- historical backtest outputs;
- model outputs/parameters;
- scripts connected to known bugs;
- assets with unclear time discipline, leakage risk, join risk, provenance gaps, or previously favorable-result bugs;
- data/results whose current reproducibility is only `INFERENCE` or `UNKNOWN`.

For every C item, state the **minimum revalidation required** before reuse. Do not perform that revalidation in this task.

### D — UNKNOWN / NEEDS EVIDENCE

Use when available evidence is insufficient to choose A/B/C honestly.

State exactly what evidence is missing.

Do not force uncertain assets into another class.

## Required deliverable

Create:

`legacy/2026-09-21-inventory/ASSET_TRIAGE.md`

The document must contain:

### 1. Executive summary

- counts of A / B / C / D;
- the main reasons assets fall into each class;
- a short statement that old research conclusions are not automatically inherited.

### 2. Classification table

At minimum columns:

| Asset / group | Type | Primary class | Evidence basis | Why | Reuse condition | Priority | Notes |

Rules:

- classify coherent groups where individual-file classification would create meaningless hundreds of rows;
- split a group when members have materially different provenance/risk;
- use exact paths/names;
- distinguish observed fact from `INFERENCE`;
- keep `UNKNOWN` explicit;
- do not invent missing metadata.

### 3. Mandatory high-attention items

Explicitly address at least:

- `e58_census_odds.csv` / E58 census chain;
- `fb_match_ht.csv`;
- `fb_match_index.csv`;
- `fb_ttg_series.csv`;
- `e54_join.csv` and other join/alignment assets;
- `hafu_hist.csv` / `hafu_hist_fitted.csv`;
- forward/prospective ledgers;
- Pinnacle / 竞彩 alignment and de-vig code/results;
- Oracle / upper-bound experiments;
- known bug-affected E53/E54/E58 assets;
- research methodology documents;
- raw source snapshots / normalized captures;
- duplicate football-data collections;
- collectors / orchestration / backfill scripts;
- reports that contain old profitability conclusions.

If an item named above does not exist under the exact path/name in the frozen inventory, say so; do not fabricate it.

### 4. Revalidation queue

For C items, create a queue grouped by minimum check type, for example:

- provenance/hash/source verification;
- schema/time-range sanity;
- raw→derived lineage reproduction;
- join/alignment audit;
- future-information / leakage audit;
- ROI/metric recomputation;
- bug-regression check;
- prospective-only confirmation.

This is a **queue definition**, not execution.

### 5. Archive-retirement note

Define what remains to be completed before the old 竞彩足球研究 conversation can be retired from active use.

Target end state:

> Old 竞彩足球研究 chat = historical archive only.  
> GitHub repository + current project conversation = sole active workflow.

Do not declare the old conversation retired yet unless all legacy assets needed for current work have inspectable GitHub/file evidence or are explicitly marked `CHAT-ONLY / NOT VERIFIED` / `D — UNKNOWN`.

## Evidence hierarchy

Use this order when evidence conflicts:

1. synchronized GitHub files / actual local legacy files;
2. scripts and datasets that can be inspected;
3. formal reports and frozen inventory;
4. old conversation context;
5. memory/assumption — never sufficient by itself.

## Allowed changes

Only:

1. `TASKS/TASK-0003-legacy-asset-triage.md` — status changes only after task start;
2. create/update `legacy/2026-09-21-inventory/ASSET_TRIAGE.md`;
3. create `REPORTS/TASK-0003.md`.

## Forbidden changes

Do not:

- edit the five frozen TASK-0002 legacy inventory files;
- edit `REVIEWS/TASK-0002.md`;
- modify legacy raw/derived data;
- move, rename, deduplicate, or delete legacy assets;
- rerun experiments or backtests;
- retrain any model;
- fix historical scripts;
- restart/stop collectors or services;
- backfill data;
- install packages;
- change Git remotes/configuration;
- rewrite history or force-push;
- use external web research;
- start the next research phase.

This task is classification only.

## Validation before submission

Before submitting:

1. verify the five frozen inventory files are unchanged;
2. verify only the three allowed TASK-0003 paths changed;
3. check every C item has a minimum revalidation requirement;
4. check every D item names missing evidence;
5. search `ASSET_TRIAGE.md` for unsupported words such as “已验证盈利”, “可直接用于盈利模型”, or equivalent overclaims;
6. ensure old-chat-only claims are marked `CHAT-ONLY / NOT VERIFIED`.

## Report requirements

Create `REPORTS/TASK-0003.md` containing:

- synchronized starting HEAD;
- source files inspected;
- whether the old research conversation was consulted;
- if consulted, which facts were chat-only and how they were marked;
- A/B/C/D counts;
- exact files changed;
- validation commands/results;
- unresolved blockers;
- submission commit hash and push result.

## Completion

When finished:

1. set task status to `REVIEW`;
2. commit and push to `origin/main`;
3. STOP;
4. report to Owner only:
   - Task ID;
   - status = REVIEW;
   - commit hash;
   - report path;
   - blockers, if any.

Do not call the task ACCEPTED. Only ChatGPT/Reviewer may accept it.

## Acceptance criteria

- `ASSET_TRIAGE.md` exists and is evidence-based;
- A/B/C/D classification is applied without forcing uncertainty;
- important legacy datasets/code/results are explicitly covered;
- C assets have concrete minimum revalidation requirements;
- D assets state missing evidence;
- old-chat-only information is visibly separated from inspectable evidence;
- frozen TASK-0002 inventory files remain unchanged;
- no research/backtest/model/data mutation occurred;
- task is submitted in REVIEW state with report and commit evidence.
