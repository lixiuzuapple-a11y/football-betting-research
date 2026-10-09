# TASK-0011 Phase A selection (2026-10-09, before candidate-specific outcome analysis)

Input inventory: `history/_review/09_data_历史与赛程/data/hist_v2.csv` contains dated match rows, league/division, teams, full-time outcomes, and opening `PSH/PSD/PSA`, plus closing price columns. Actual header and first row inspected, but no feature/outcome association computed before this note. This historical archive was previously used in generic analyses; **no assertion that any result is unseen/out-of-sample**.

| Family | Current fit | Verdict for TASK-0011 |
|---|---|---|
| A04 rest/congestion differential | Historical dated fixtures and Pinnacle opening 1X2 present; prior matrix says not family-wide tested; mechanism measurable without new API | **SELECT** fixed retrospective falsification |
| A03 lineup/player | No verified point-in-time lineup completeness in inspected canonical fields | defer |
| A05 weather/pitch | No timestamped weather join shown for this file | defer |
| D02 news → repricing lag | No provider event clock for reference, negative TASK-0007 source-quality warning | defer |
| C01 probabilistic cross-play | Requires cross-play mapping/settlement and probability model; narrower deterministic audit already negative | defer |
| B04/B05 demand shading | No defensible ex-ante independent demand proxy verified | defer |
| A07 coverage asymmetry | No source coverage score assigned before results; league-only segmentation previously failed | defer |
| C03/C04 parlay dependence | Many settlement/contract complexities, current dataset insufficient | defer |

Fixed choice rule: prioritize genuinely measurable non-price information using existing point-in-time historical dates and market baseline, low incremental cost, with a negative/falsifying result possible. Do not select using ex-post profits or favorable groups. Selection is an exploratory retrospective test, **not** a new Sporttery betting strategy. It can establish whether the hypothesis deserves further study; it cannot establish real-money value.

Reusable assets: prior market de-vig and repository test infrastructure; use existing historical CSV (no re-download), avoid reinventing market arithmetic. Scope fixed: test only A04 rest differential as descriptive incremental information over opening market baseline. Do not pivot to other families if result is negative.
