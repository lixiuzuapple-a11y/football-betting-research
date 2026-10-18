# EV-Lab canonical quote candidate replay — stage 2026-10-18

## Stage decision
**ACCEPT** the reproducible conservative replay diagnostic on historical frozen corpus. **NO-GO** for trading/ROI outcome inference until authoritative market status semantics and verified score identity are provided.

## Input and method
Read-only verified Windows backup of TASK0024 and TASK0025. `tools/task0029_quote_candidates.py` confirms SHA256 of each raw decompressed payload against SQLite, yielding **9,519** raw responses and **169** fixtures. Incremental fixture × market replay is bounded in memory and runs locally. First accepted market snapshot requires parseable valid odds, an observed timestamp not materially preceding provider timestamp (120s tolerance), matchStatus=Selling, sellStatus=1, poolStatus=Selling and no nonzero f-flags. A subsequent valid later provider timestamp creates an update event only if the full price vector or handicap changes; same state is duplicate, rollback rejected, same-timestamp contradictory vector rejected. Date semantics assume provider local UTC+08. This conservative filter may exclude legitimately tradable events; fields are not an official contractual trade API.

| Market | Initial accepted | Accepted later price moves | Identical snapshots | Provider rollbacks rejected | Flagged snapshots excluded | Match not selling excluded |
|---|---:|---:|---:|---:|---:|---:|
| HAD | 159 | 274 | 104292 | 0 | 23153 | 98504 |
| HHAD | 167 | 275 | 108608 | 1 | 23634 | 101650 |
| TTG | 166 | 206 | 116015 | 0 | 16302 | 101650 |
| CRS | 166 | 171 | 119036 | 0 | 13317 | 101650 |
| HAFU | 167 | 207 | 115228 | 0 | 17088 | 101650 |

Distinct accepted fixture × market keys: **825**. The filtered events are candidate quote observations, **not executable bets**. The classification priority is ordered (flagged, timestamp, match-level state, pool-level state, then replay comparisons) so exclusion counts are mutually exclusive by first encountered reason, and should not be interpreted as population-wide raw prevalence.

## Known blockers and interpretation
- Prior response-order audit counted 3,747 vector transitions across pools. This stricter replay identifies a much smaller accepted subset because rejected/duplicate snapshots and non-selling status are excluded. The two totals use different denominators and cannot be compared as market volume without qualification.
- Provider timestamp backtracking, unknown f-field semantics, unclear bet authorization and absence of verified settlement still prevent a historical executable-odds book.
- No verified final score file with matchId, score and authoritative provenance was present in project inputs; existing strict join helper `tools/task0022_result_join.py` cannot fabricate provenance. **0 verified joined outcomes**; zero estimated return on investment.
- Status codes may change without quote update; actual sale eligibility needs independent source verification. We intentionally do not label any quote as tradeable.

## Reproduction
`python -m tools.task0029_quote_candidates --root <TASK0024_local_backup> --root <TASK0025_local_backup> --out <local_report.json>`
Synthetic transition regression: `tests/test_task0029_quote_candidates.py`. Entire existing suite **296 passed** (2026-10-18).
Raw numerical JSON evidence: `E:\WebCodex-Workspace\EVLab-Data-Backups\official-20261018\TASK0029-QUOTE-CANDIDATES.json`.

## Research gate
STOP any retrospective profit claims. GO narrowly to verified score acquisition by provenance and independent quote-state business semantics confirmation; only once those gates are satisfied consider a frozen, leakage-safe decision validation. No need for a new data collector or another framework.
