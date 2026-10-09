# TASK-0009 — Reference-source qualification
- Status: IN_PROGRESS
- Date: 2026-10-09
- Owner: Li
- Lead / Executor / Reviewer: ChatGPT
- Prerequisites: TASK-0007, TASK-0008 completed; both mechanism hypotheses NOT VALIDATED.
- Scope: source reconnaissance and qualification only. No paid account activation, five-day capture, live betting or BUY/PASS.
## Aim
Identify a defensible alternative to BetExplorer reference_proxy for Sporttery HAD B01/D01-B comparisons. Reuse existing research/DATA_SOURCE_ALTERNATIVES_RECONSTRUCTION_20260923.md, TASK-0007/8 lessons, historical Betfair/football-data tooling, canonical matching and odds utilities. Do not rebuild existing functionality.
## Frozen qualification gates (before new test results)
Q0: authorized access, licence, cost and geography documented; unknown = not qualified.
Q1: stable named market/provider/fixture/1X2 selection identity, no unannounced rendering variant changes.
Q2: UTC response-receipt and separately documented provider-update semantics; no event-time assertion based only on collection time.
Q3: conservative identity join independent of odds; kickoff tolerance fixed at 15 minutes as in TASK-0007.
Q4: overlap with official executable Sporttery HAD quantified with coverage denominator.
Q5: snapshot stability, batch/reversion rate reported without cherry-picked variants.
Q6: raw bytes, hashes, parser/schema revision, retrieval provenance and deterministic replay.
Q7: Owner approval before payments, account actions or recurring collection.
## Candidate order
1. football-data.co.uk fixtures.csv with Betfair Exchange (BFE) columns: free static/periodic baseline; cannot imply intraday move times.
2. Betfair Delayed API: named exchange but personal account/app key required; 1–180-second delayed snapshots and 3-minute Stream conflation disallow second-level D01-B attribution.
3. Pinnacle bespoke API: request/approval/cost required; no free access assumption.
4. Named bookmaker via a licensed odds data vendor: examine timestamp, identity, cost and licence.
5. BetExplorer: negative control after TASK-0007/8; no reinstatement by posthoc variant picking.
6. Sporttery official is execution-side truth, 500.com only third-party mirror.
## Deliverables and disposition
Record a source-by-source matrix with official evidence URLs, source time semantics, research-fit gate and uncertainties in research/TASK-0009_REFERENCE_SOURCE_QUALIFICATION.md. Report execution in REPORTS/TASK-0009.md; independently audit in REVIEWS/TASK-0009.md. Any generally reusable script/test must be tracked under tools/src/tests. If no Q0–Q6-qualified source is available, close as research reconnaissance completed / source qualification BLOCKED, with explicit reopen criteria. No interpretation of proxy differences as true EV, profit or a deployable signal.
