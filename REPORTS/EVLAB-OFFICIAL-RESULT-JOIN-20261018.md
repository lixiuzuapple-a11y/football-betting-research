# EV-Lab mainline stage — official result evidence and identity join (2026-10-18)

## Outcome
**STAGE ACCEPT for source discovery, provenance capture, and strict identity join.** **135 score-labelled fixture candidates** from the official published result data. **NO-GO for claiming ROI/predictive edge** until leakage-safe timestamp cutoffs and settlement eligibility reviewed.

## Actual source, not inferred
- Public official results page: https://www.sporttery.cn/jc/zqsgkj/
- Site published JS `jc_sgkj_gz.js` invokes `https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry` with date/page query; GET returned HTTP 200 and `errorCode=0` (string or integer).
- Retrieved **11** date-scoped official JSON responses across **11** scheduled dates, **159** rows. All response byte-for-byte snapshots are held in the separate local evidence folder with SHA256 in `JOIN_EVIDENCE.json`. Not pushed into ordinary Git.
- Source files retained under `E:\WebCodex-Workspace\EVLab-Data-Backups\official-20261018\TASK0030-RESULT-EVIDENCE`; reproducible program `tools/task0030_official_result_evidence.py`.
- Source fixtures: frozen TASK0024 / TASK0025, 9,515 success raw responses, 169 fixture IDs. All raw payloads SHA256 verified against frozen SQLite before identity extraction.

## Strict matching and final score gate
- Source official `matchId` must equal frozen capture `matchId` exactly.
- Both `homeTeamId`, `awayTeamId` and `matchDate` must agree; duplicate conflicting official records are excluded.
- `sectionsNo999` must be strictly nonnegative numeric `home:away`; cancelled `无效场次`, blank and malformed score fail.
- Data sample reveals historical scored rows have `matchResultStatus=2`; condition requires exact 2. This is *empirically observed*, not a published contract proving every outcome's finality; human-readable public release still should be independently spot-checked prior to trading claims.

**Results:** matched ID records = **136**; joined valid-scored candidate fixtures = **135**; identity conflicts = **0**; matched but unscored = **1**; no official response row matched = **33**.

## Meaning for the research direction
This resolves most of the missing-outcome gap using a named official publisher rather than guessing. It does not prove that a historical observed odds quote could actually be placed at its recorded timestamp. In particular:
1. Previous replay produced 825 accepted fixture-market initial candidate states and 1,133 subsequent candidate changes, based on conservatively interpreted market/status flags; these are not legally verified executable order quotes.
2. Published result scores are retrospective labels and must be joined only **after** computing prior-to-kickoff decisions; absolutely no use in predictive features.
3. The remaining 34 unmatched/unscored fixtures stay **UNLABELLED**, not counted as losses, draws, or suspended draws. Some fixtures can have future kickoff dates relative to the 2026-10-18 research date.
4. Any ROI, holdout, strategy or calibration claim remains **NOT TESTED** here. Next coherent stage should freeze pre-kickoff evaluation criteria, verify quote availability and labelled settlement, and then run leakage-safe retrospective *diagnostic* evaluation, not optimistic trading claim.

## QA
- Local full suite **299 passed**; synthetic tests cover strict numeric score, pending status, cancelled records, identity conflict and duplicate conflicting scores.
- Same source date+page may change after this snapshot: persisted bytes and SHA256 are necessary for reproducible audit.
