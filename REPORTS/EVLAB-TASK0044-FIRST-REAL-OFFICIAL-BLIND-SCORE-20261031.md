# EV-Lab — First REAL pre-kickoff → official blind score (TASK0044)

Date of actual official score: **2026-10-31 12:30:02 CST**.
Independent QA: 2026-10-31 14:18–14:22 CST. Scope: two previously
pre-kickoff frozen matches only, four unchanged models, no betting.

## Scheduled execution really happened

- Windows Task Scheduler `EVLab-TASK0044-OfficialScore-20261031`:
  `LastRunTime=2026-10-31 12:30:30`, `LastTaskResult=0`,
  `NumberOfMissedRuns=0`, one-shot task without a future trigger.
- Immutable scheduler script:
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0044-scheduled-20261031\Run-OfficialScore.ps1`.
  Append-only output `SCORE_RUN_LOG.txt`:
  `START=2026-10-31T12:30:01.4739278+08:00`,
  `SUCCESS=2026-10-31T12:30:02.8069594+08:00`.
  The Windows scheduler's displayed LastRunTime is approximately **29s later**
  than the script's own start time; **clock/source discrepancy retained**,
  not explained away. Regardless, both are >8h after final fixture kickoff.
- Actual result root, not under Git:
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0044-official-score-20261031`.
  `BLIND_SCORE.json` SHA256
  `c33ae8cf8f67da7453102a840a18bb8c4414b428afb1d36a48178a3b268c8be0`;
  `SOURCE_MANIFEST.json` and original `official-2026-10-31-page-1.json`
  retained without mutation.
- Official HTTP200 source receipt
  **2026-10-31T04:30:02.758349Z**, URL fixed Sporttery
  `getUniformMatchResultV1.qry`, 14,927 source bytes,
  SHA256 `73d2f04bbdcb355a2bf18c2ca30bb0d0933d7cf149236a2f895bd593a7c1aba6`,
  official final status `2` for both exact target MatchIDs and original
  home/away IDs. Target official date `2026-10-31` matches UTC kickoff
  converted to Beijing date.

## Original pre-kickoff source and Git-anchored forecasts

- **Original official fixture capture** at 2026-10-29T07:31:11.376632Z;
  actual gzip raw SHA256
  `4fecde60266a7f99fcf10b6aeed3ab1883ad17d8394e0f2f56bc3f93f1b42767`.
  Independent read-only TASK0041 audit of
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0043-live-single-20261029`:
  **1/1 verified**, HTTP200, SQLite quick_check=ok.
- Original full forecast frozen **2026-10-29T07:36:26.021565Z**,
  source file SHA256
  `3bb96003e370f45bc60c9656d76542bf3444cd5b19a3d2575c303e66e4d670b3`.
  Original Git commitment submitted at commit `a0395a0`,
  Git committer timestamp **2026-10-29T07:42:36Z**:
  earliest kickoff 2026-10-30T18:00:00Z — **34h17m after Git commitment**.
  Original model results are compared against frozen probability triples,
  not re-trained or re-selected after scores.
- Historical training input 53,705 original completed fixtures,
  last training match date **2026-07-04**, historical source published
  **2026-07-05T01:23:18Z** (stale by roughly four months).
- **Important Git newline caveat:** the published Git ledger blob contains
  **LF**, SHA256
  `e8001e6eb3ee8c8974b7710dfa23661d1f16e98f7f319b50637b12e47f48c857`.
  Windows checked-out ledger contains **CRLF**, SHA256
  `339fc55ebb50ec687934f67fa68b365b5ff64612c314b0fc5de822e097233dcf`;
  the scored manifest records the local checked-out ledger SHA. Our
  independent auditor confirmed **the sole byte difference is CRLF→LF**.
  It is legitimate to claim **identical Git-anchored forecast substance**
  and a separately identical frozen file SHA; **not** legitimate to claim
  the checked-out ledger and Git blob are byte-for-byte equal.
- Local OS/Git commit timestamps are not independently authenticated time
  authorities; this is a reproducible prospective commitment with Git
  chronology, **not** trusted-third-party timestamp proof.

## Exact independently confirmed official results

| MatchID | Beijing kickoff | Official home/away IDs | Final (home:away) | 1X2 |
| --- | --- | --- | --- | --- |
| 2042359 | 2026-10-31 02:00 | 618 / 613 | **3:2** | HOME |
| 2042364 | 2026-10-31 04:05 | 180 / 179 | **1:0** | HOME |

Both rows found **exactly once** in genuine raw official result pages; complete
status and date/identity matched; none were silently omitted.

## Fixed same-game four-model comparisons (N=2)

| Model | top-class hit | mean log loss ↓ | mean multiclass Brier ↓ |
| --- | ---: | ---: | ---: |
| Global frequency | 2/2 | 0.8221034122122116 | 0.4728903205169874 |
| League frequency | 2/2 | 0.7159679598176149 | 0.39416753598685256 |
| League Poisson | 1/2 | 0.736939915342606 | 0.41382858706745196 |
| Pooled Elo/Davidson | 1/2 | 0.949376210663625 | 0.5676340298895921 |

Replay tool `tools/task0047_independent_blind_score_qa.py`
computed the results independently from original frozen vectors and saved
raw result bytes, not by reusing `task0044.score_evidence()`. Exact
comparison against original `BLIND_SCORE.json` passed at <= 1e-12.
Independent create-only JSON evidence (out of Git):
`E:\WebCodex-Workspace\EVLab-Data-Backups\task0047-independent-qa-20261031\INDEPENDENT_AUDIT.json`.

No simultaneous PIT bookmaker price, fair-probability baseline, Pinnacle CLV,
ROI, staking or market alpha is claimed. **N=2 is far too small for meaningful
model selection or calibration inference.** Frequency 2/2 is a realized
sample outcome, not evidence that it is a superior predictor.

## Test and acceptance

- Eleven additional synthetic independent-audit tests: pass. Corrupted original
  or final raw SHA, Git-anchor substantive alteration, missing/duplicate
  official result, nonfinal status, incorrect identity, original freeze
  change, score/result disagreement and incorrect model arithmetic are rejected.
- Full EV-Lab test suite **463 passed**. Existing TASK0044 mocked-clock
  negative-control was repaired because its hardcoded scoring date preceded
  the actual current time; this was a **test-only fix**, no production scorer,
  frozen vector or raw source modification.
- **TASK0044 REAL OFFICIAL PROSPECTIVE BLIND SCORE: ACCEPT (N=2)**.
  This closes one authentic prospective prediction/score chain. It does not
  validate market superiority or future scheduled reliability.
- Next research gate remains accumulating **new authentic prospectively frozen
  and scored eligible matches** under TASK0046 with independent source/identity
  verification; no new model exploration or basketball extension.
