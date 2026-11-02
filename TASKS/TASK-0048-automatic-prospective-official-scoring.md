# TASK0048 — Guarded automatic prospective official blind scoring

Date: 2026-11-02. EV-Lab football mainline only. No basketball/stock.

## Goal

Make new prospectively Git-published TASK0046 four-model cohorts **eligible for
automatic delayed official result retrieval and independent scoring**. Keep
existing TASK0044 Oct31 two-game scored artifacts immutable. This is a small
orchestration layer over the previously real-validated official-only scorer
and independent QA calculator, **not** a new prediction/model/market system.

## Verified starting point

- 2026-11-01 11:15 scheduled TASK0046 ran exit 0, captured 34 official
  fixtures and correctly recorded NO_NEW_ELIGIBLE_PREMATCH_FIXTURES.
- 2026-11-02 11:15 TASK0046 ran exit 2, **failed before official capture**
  because remote Git fetch returned status 128. Incident:
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0046-forward-20261031\journal\run-20261102T031503689762Z-725c25cd.json`.
  The failed run is NOT recast as a normal no-new-fixture observation.
  Manual read-only fetch at 12:33 succeeded, so the original transient cause
  cannot be conclusively inferred from the truncated old log.
- Cloud TASK0045 source remained active and healthy at 12:33; 70 records in
  current epoch, raw SHA verified, SQLite OK, about 40 GiB free.
- No new TASK0046 pre-kickoff Git forecast commitments exist as of this review.
  First Oct31 TASK0044 two-game official blind score is already ACCEPT.

## What is done in this stage

1. TASK0046 Git *preflight fetch only* now retries a bounded three times with
   5/10-second delays; it does **not** weaken clean branch, exact origin,
   remote HEAD agreement or pre-kickoff publication rules. After 3 failures
   it remains FAILED_RETAIN_ALL_EVIDENCE and is not counted as prediction.
   Sensitive credential-bearing stderr must not be persisted.
2. New `tools/task0048_scheduled_score.py` scans only prior **successfully
   remote-Git-acknowledged** TASK0046 forward run journals and freezes with
   source Git blob matching the exact research ledger (allow recorded LF/CRLF
   difference only), first confirmed commit before kickoff, untouched original
   full freeze SHA and identical vectors.
3. Only once the latest fixture kickoff + >=3 hours has elapsed may it call
   the already verified original TASK0044 `fetch_and_score`. Original raw
   official result pages are immutable, SHA-protected, and exact MatchID,
   home/away/date/status verified; complete frozen cohort or fail.
4. On successful scoring, it runs the **independent** source+Git+probability
   audit from TASK0047. A create-only independent audit result plus source
   scores must exist before recording INDEPENDENT_SCORE_ACCEPTED.
   A prior accepted cohort is deduplicated; proof files and SHA are rechecked.
5. For official results missing/delayed, unverified Git, dirty evidence,
   corrupted previous score, or API failure, write a *separate fresh attempt*
   with source material and FAILED_RETAIN_ALL_EVIDENCE; next run may retry.
   Never silently discard individual games, fabricate missing results,
   choose a winning model, or override a prior artifact.
6. Bound per-invocation cohorts to 10. Operator QA required beyond the bound.
   The Windows task is interactive, **requires the PC logged in and network**;
   this is not a cloud 24h service guarantee.
7. Daily result tasks do **not** alter the cloud collector, prior TASK0044
   schedule or TASK0046 prospective model pipeline. The new workflow includes
   no market pricing, ROI or bet execution.

## Acceptance

Required: full repository regression; negative tests around unanchored/
retroactive predictions, not-yet-due matches, missing official results, failed
independent QA and corrupt previous evidence; actual real-job registration
and bounded no-due run; accurate evidence if no newly committed cohorts exist.
**Cannot claim a newly published match was scored live** until such a real
pre-kickoff frozen cohort actually appears.
