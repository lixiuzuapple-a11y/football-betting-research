# EV-Lab — actual 169-fixture corpus audit (2026-10-18)

## Source and reproducibility
- Two immutable official capture roots backed up off-server and verified SHA256 against cloud originals; this audit ran on the Windows backup, not on the resource-limited cloud host.
- Inputs TASK0024 6,398 successful payloads/82 fixture IDs; TASK0025 3,117 successful payloads/87 fixture IDs; overlap **0**.
- Read all successful raw gzip JSON and verify each uncompressed payload against the corresponding SQLite raw SHA; this is an exploratory streaming pass after full backup verification.
- Local evidence file alongside backup: `MAINLINE-169-STREAMING-AUDIT.json`.
- **169** distinct fixtures and **234,340** fixture-response observations. Min/median/max observations per fixture = **[8, 1418, 3204]**.

## Field-level findings
For each fixture/pool, compare observed pool price vectors excluding provider `updateDate`, `updateTime`, and flags ending in `f`. Report raw vector transitions across responses, revisits to previously seen vectors, provider timestamp decreases, and fixtures with vector changes.

| Pool | Raw vector transitions | Returns to earlier vector | Timestamp reversals | Fixtures with changes |
|---|---:|---:|---:|---:|
| HAD | 952 | 458 | 217 | 118 |
| HHAD | 954 | 440 | 211 | 126 |
| TTG | 675 | 317 | 158 | 116 |
| CRS | 500 | 219 | 110 | 113 |
| HAFU | 666 | 296 | 146 | 116 |

**Interpretation**: Many observed changes are reversions and provider timestamps also travel backward. No legitimate conversion of these transitions to independent changes, actionable quoted prices, or EV edge is warranted. Need fixture-local provider-time ordering, stable identity, full quote availability flags, and replay deduplication. Do not treat the counts as tradeable opportunities.

## Stage gate
- Source integrity/off-host backup: **ACCEPT** (separate verified backup report).
- Real full-corpus fixture coverage and structural price vector exploration: **OBSERVED**, independent algorithm review still required before claiming executable quote history.
- Genuine timestamp-consistent quote updates: **PENDING**.
- Verifiable match outcomes linked to IDs and scores: **0**, **PENDING**.
- Betting edge / strategy / ROI: **NOT EVALUABLE**.
- Next single mainline research phase: normalize quotes with status/flags and timestamp validation, establish lawful match-outcome identity bridge, then run leakage-safe prospective decision tests only if labels/quotes pass. Avoid more collectors or framework proliferation.
