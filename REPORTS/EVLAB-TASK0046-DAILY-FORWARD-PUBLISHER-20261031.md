# EV-Lab TASK0046 — Guarded daily genuine prospective publisher

Date/time: 2026-10-31, Beijing. EV-Lab football only.
Stage result: **ENGINEERING ACCEPT (no-new-fixtures path)**,
**actual new-fixture Git publication remains PENDING**.

## Direct reusable implementation

- `tools/task0046_forward_publication.py` reuses original TASK0044
  one-shot collection/eligibility and TASK0043 unchanged four-model freeze.
  It refuses to publish a prediction from unverified/late source data,
  duplicate MatchIDs, invalid source/training/identity hashes, bad
  historical chronology, incomplete models, unexpected Git remote,
  dirty/misaligned main, publication within 60 min of kickoff, or
  unverified remote Git commit.
- A create-only Git commitment format records the original frozen source
  SHA and full probabilities, historical source SHA/training last date/
  publication time, identity bridge SHA, source code commit, UTC capture/
  frozen timestamps, market prices/time **NULL UNVERIFIED**, results
  **PENDING**, and no-EV/no-wager markers. Before any Git publication
  `verified_freeze()` checks exact file SHA/vector equality.
- Every attempted live run gets unique off-Git source evidence and
  create-only run journal. No-offer and no-new-match are accepted as
  legitimate **no-forecast** outcomes, not a selection failure.
- The cloud official TASK0045 collector remains **independent and active**.
  We do not copy its live SQLite WAL; this daily pipeline uses the exact
  same approved official source endpoint via a fresh genuine 1-round
  TASK0044 request. **Do not claim it consumes the cloud WAL.**
- A daily Windows task `EVLab-TASK0046-DailyForward` was registered with
  logged-in Administrator Interactive principal; **11:15 Beijing daily**,
  StartWhenAvailable/WakeToRun, 20-min execution limit, IgnoreNew instances.
  Batch script is Git-versioned
  `deploy/Run-Task0046-DailyForward.ps1`, SHA256
  `b373d1c6acb46d7dea26fa80858570bb5d7dab025513b178d461f63e5ffb2fc3`.
  If PC is off / account logged out / network inaccessible, next job
  is **not guaranteed**; no cloud-independent forward scheduler is claimed.

## Real official capture and registered scheduler execution

1. Manual `--mode probe` at 2026-10-31 10:08 Beijing:
   - HTTP200, **43 real official fixtures**;
   - source SHA256
     `31f7938ff0d7dcac6964e5427af580cd95c8918c3d709f1eecd8273a25e6450b`;
   - status `NO_NEW_ELIGIBLE_PREMATCH_FIXTURES`; no new freeze, no new
     Git commitment; eligible team crosswalk remains strict.
   - evidence run `run-20261031T020852158536Z-41c9c452`.
2. Real **Task Scheduler** invocation `Start-ScheduledTask`, not just
   direct Python:
   - LastRunTime **2026-10-31 10:11:11 Beijing**;
     LastTaskResult `0`; next regular start
     **2026-10-31 11:15:15 Beijing**.
   - At 10:11:38 Beijing captured **43 real fixtures**, HTTP200;
     same valid SHA as prior official capture (identical source body);
     event status `NO_NEW_ELIGIBLE_PREMATCH_FIXTURES`.
   - exact source commit
     `bfd30f6ad5396a862f6dcc37e7848cdb8ab0933b`;
     1/1 raw gzip SHA matches, SQLite quick_check=ok and
     current fixed parser classification=ok; original row preserved.
   - evidence run `run-20261031T021136112509Z-bd263952`;
     append-only invocation log
     `E:\WebCodex-Workspace\EVLab-Data-Backups\task0046-forward-20261031\scheduler\INVOCATIONS.jsonl`.
3. Original independent TASK0044 score remains `Ready`:
   planned **2026-10-31 12:30:30 Beijing**, no prior task run
   when checked. It was not changed by this rollout.

## Tests and acceptance

- 18 TASK0046 tests passed (mocked target-source publication paths,
  real on-disk freeze data, duplicate prior IDs, source-hash/date
  mutations, invalid opponent/model source, dirty/diverged/wrong
  repo, remote commit mismatch, failed run provenance, no-offer
  and no-new-match journal behavior).
- Whole EV-Lab regression: **452 passed**.
- PowerShell scheduler script syntax: PASS. Python compile: PASS.
  Git diff whitespace check: PASS.
- Live official source probe and actual registered Windows invocation
  independently read, source audit 1/1, no false new forecast: PASS.

**ACCEPT** bounded on-demand and daily scheduled research capture/no-new
forecast and guarded publication software. **PENDING** live eligible
new-fixture forecast successfully published before kickoff + subsequent
official blind score, market-time pricing, CLV, positive EV and continuous
Windows availability. This stage cannot manufacture a new eligible real game.

See `REVIEWS/EVLAB-TASK0046-INDEPENDENT-QA-20261031.md`.
