# EV-Lab TASK0048 — actual run and failure recovery, 2026-11-02

**Stage conclusion:** engineering **ACCEPT** for Windows Task Scheduler trigger,
no-due-scoring behavior, bounded retestable Git-synchronized pre-kickoff
collector, and synthetic fail-closed score/independent-review logic.
**PENDING** actual new real pre-kickoff forecast and its later independent score.
This report does not validate betting market profitability.

## Current source observations (Asia/Shanghai +08)

- 2026-11-01 **11:15** forward daily task completed, exit **0**,
  captured **34 official games** and had zero additional approved
  four-model prospects.
- 2026-11-02 **11:15** forward daily task failed, exit **2**:
  `git fetch origin main` returned **128** before any official capture.
  Original untouched evidence:
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0046-forward-20261031\journal\run-20261102T031503689762Z-725c25cd.json`.
  The old journal did not capture Git stderr. **Exact root cause not known**.
- **12:33** authenticated manual Git fetch worked, HEAD == origin/main.
  TASK0046 preflight now makes **up to three bounded fetch attempts**
  (5/10-second pauses) but **never skips remote Git verification or
  preregistered time/identity guards**. No attempted fetch of a new official
  page occurs if preflight fails.
- Real **registered Windows scheduler** TASK0046 was manually triggered
  after the code was pushed, at about **12:40**:
  exit **0**, actual source response **9 games**,
  status `NO_NEW_ELIGIBLE_PREMATCH_FIXTURES`. Evidence:
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0046-forward-20261031\journal\run-20261102T044039402158Z-1070d016.json`.
  The original 11:15 failed journal remains. This demonstrates
  **actual scheduler recovery** but does not guarantee immunity from
  future Git/Internet outages.

## New automatic delayed post-match scoring path

- `tools/task0048_scheduled_score.py` is an orchestration layer over the
  existing official-only TASK0044 `fetch_and_score` and independently
  reconstructed TASK0047 `independent_audit`, without retraining any model.
- It reads **only** prior successfully pushed TASK0046 Git commitments,
  rechecks exact remote-confirmed Git HEAD and ancestor of origin/main,
  historical forecast source bytes/SHA and the approved Git ledger path.
  It refuses any match frozen/published at or after kickoff.
- Scores a cohort only **3+ hours after the latest kickoff**; every official
  response is saved in a fresh, create-only evidence root.
  Missing, duplicate, invalid identity/date/status or incomplete source
  **fails closed** and retains that attempt; subsequent runs use new roots.
  No result is silently omitted. No success until independent QA has
  replayed original source SHA, Git ledger and all four probability vectors.
  Previously successful scores are only skipped if original score and
  independent-audit SHA bytes still match.
- Candidate batch bound: 10; larger queues fail for manual QA rather than
  claiming complete scoring. No sportsbook price, model selection,
  CLV/ROI or money transactions are in scope.
- Daily Windows Task Scheduler task:
  `EVLab-TASK0048-DailyOfficialScore`, **18:30 Beijing**,
  registered using `deploy/Run-Task0048-DailyScore.ps1`,
  script SHA256
  `e66736134b7284fe4cfa855ef69e0ef0798e4e310cc8914e7b31ab206062ebc9`.
  Actual manually triggered registered task returned **exit 0**,
  LastRunTime **2026-11-02 12:40:40** (scheduler clock),
  one invocation in off-Git
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0048-official-score\scheduler\INVOCATIONS.jsonl`.
  Next automatic scheduled trigger: **2026-11-02 18:30:30 Beijing**.
- A direct actual local run at **12:37:40 Beijing** returned
  `NO_COMMITTED_NEW_PROSPECTS`. There were zero new qualifying and Git
  published prospective model cohorts in the current queue, so this
  run **never fetched any new result pages** or fabricated scores.
- The original TASK0044 Oct31 two-game blind score remains ACCEPT,
  unchanged and outside the new automation's outstanding queue.
- Both scheduled workflows depend on Windows PC powered on, logged-in
  Administrator and valid Git/Internet connectivity. Cloud TASK0045
  continuous official source collector runs separately and was not
  modified or interrupted.

## Tests and boundaries

- Focused new scorer + Git fetch retry+ existing independent QA **passed**.
- Full EV-Lab repository test suite **475 passed**. PowerShell task script
  parsed, Python compiled and Git diff whitespace check passed.
- Synthetic negative tests exercise post-kickoff delay, no eligible
  commitments, duplicate accepted score, changed Git/forecast,
  missed official results, evidence retention on repeated failure,
  invalid historical timestamp, and altered accepted-score SHA.
- **Engineering ACCEPT** for TASK0048 orchestration and deployed
  schedule. **NOT ACCEPTED** until a new qualifying prospect is
  actually Git committed before kickoff and later automatically
  receives a fully independently audited official final score.
- External real-time alerts, automatic off-site restore-tested backups
  and market-odds PIT comparisons remain distinct unclosed items.
