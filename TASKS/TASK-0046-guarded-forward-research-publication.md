# TASK-0046 — Guarded daily genuine pre-kickoff Git forecast commitment

Date: 2026-10-31. EV-Lab football mainline only.

## Objective and reuse

Move beyond manual single-shot prospective freezing without altering the running
cloud TASK0045 collector, training new models, broadening unverified teams or
inventing a market baseline.

Reuse TASK0044 one-round official capture/duplicate suppression, TASK0043
frozen training history and team mapping and all four models, plus TASK0044
exact forecast hash/probability verifier. The new job makes a **separate one-shot
official source capture**; cloud official continuous collection remains an
independent data stream, not silently substituted from a live SQLite WAL.

## Guarded execution

1. Windows daily job runs only in clean `main` and verifies the exact
   approved GitHub `origin`; fetches latest remote and refuses divergence.
2. Keep each one-shot source SQLite, raw official gzip/SHA and status in a
   **create-only off-Git evidence root**, plus a create-only per-run journal.
   No official offer or no new crosswalk-eligible match generates no Git
   commitment and does not fabricate predictions.
3. Read previous TASK0043/TASK0046 commitment MatchIDs and refuse repeats.
   New fixture must pass 40-hex source code pin; 64-hex training, source and
   team identity hashes; legal training cutoff and chronology; exact all-four
   model vectors; minimum **60-minute publication safety margin** to kickoff.
4. Preserve original full prediction file off-Git. Create-only Git manifest
   binds frozen SHA, original official source SHA/time, code Git commit,
   training cutoff/source publication/hashes, team bridge, full four-model
   predictions, absent quote time/prices explicitly `UNVERIFIED` and
   official result `PENDING`. Re-run TASK0044 verifier against the commitment.
5. Stage **only** the new manifest, commit, push, verify actual remote HEAD and
   require remote verification before earliest kickoff. Failures remain in
   create-only run journal, and no output is claimed as a published qualified
   forecast without verified remote HEAD.
6. Local OS clock and Git commit timestamps are not authenticated independent
   time authorities; no false claim of independently timestamped publication.
   No betting, BUY, model retraining, score access or CLV in this pipeline.
7. The TASK0044 single 12:30:30 2026-10-31 score task stays untouched.
   The new daily scheduler requires the Windows PC on, signed-in user and
   online working GitHub access; it is not a cloud 24/7 job.

## Constraints

The same **two leagues and 35 strictly approved identity-matched historical
fixtures** remain the only eligible mapping. A new real prospect may be rare.
The historical training corpus is stale (last match 2026-07-04), which is
recorded, not represented as modernized. Any unable-to-publish or
no-eligible outcome is retained and is not automatically imputed as success.
Only research instruments are accepted, not claims of market outperformance.

Deployment: `deploy/Run-Task0046-DailyForward.ps1`
and `tools/task0046_forward_publication.py`.
Stage QA requires a live official source probe, negative controls, registered
Windows schedule and a real guarded invocation. Future executions are not
proven until observed.
