# EV-Lab integrated mainline research phase — 169-fixture quality and outcome gate

**Date:** 2026-10-18. **Decision: CONDITIONAL GO for further quote reconstruction; NO-GO for outcomes-based backtest, ROI or betting claims.**

## Actual data and method
Full reproducible scan of two off-host immutable copies of TASK0024/TASK0025, independently verified in `REPORTS/DATA-BACKUP-20261018.md`. Analyzed **9,519** gzip payloads with each uncompressed raw SHA256 checked against read-only SQLite; **169** distinct fixtures; **234,340** fixture observations. Counts by capture result: {'ok': 9515, 'empty': 4, 'transport_error': 3}.

Code: `tools/task0028_timeline_gate.py`. Run with repeated `--root <backup-run>` and `--out <absolute-path>`; machine-readable evidence: `E:\WebCodex-Workspace\EVLab-Data-Backups\official-20261018\TASK0028-TIMELINE-GATE.json`. Simple helper regression tests: `tests/test_task0028_timeline_gate.py`. Stage-specific validation: seven passing tests (including existing corpus and join tests).

## Per-pool diagnostic
| Pool | Observations | Price-vector transitions | Provider-time advance | Provider-time rewind with price move | Nonzero price flags (observations) | Quote age >6h (observations) |
|---|---:|---:|---:|---:|---:|---:|
| HAD | 226,386 | 952 | 736 | 216 | 24,570 | 135,194 |
| HHAD | 234,340 | 954 | 746 | 208 | 25,243 | 138,700 |
| TTG | 234,340 | 675 | 517 | 158 | 17,411 | 156,422 |
| CRS | 234,340 | 500 | 390 | 110 | 14,197 | 160,767 |
| HAFU | 234,340 | 666 | 520 | 146 | 17,937 | 154,411 |

Pool transition totals: **3,747**, of which **2,909** accompany provider-time increases and **838** accompany provider-time decreases. Different pools/observations are not independent betting events. The quote-age counts show *supplier update timestamp age*, not necessarily bet staleness; odds may properly remain unchanged for hours. Identical consecutive snapshots dominate. All raw vectors passing numeric checks does **not** imply executable availability. Status flags and match sell status remain unjoined.

The inspection reveals some price fields' timestamp and real observed arrival can disagree. No causal price time order can be asserted from capture order alone without stale-state handling. Replaying every response as a fresh independent quote would double-count history.

## Honest scientific limitations
- This audit deliberately analyzes response order and full vector snapshots, not a complete canonical quote event store. It does **not** reconstruct an independently verified historical trading book or observe actual accepted orders.
- Flags ending in `f` are classified but their business semantics are not proven; match-level sellStatus / bettingSingle and market eligibility need an explicit state machine grounded in an official field specification.
- HAD is absent in a subset of records, consistent with product eligibility variations; no assumption every fixture has every market.
- Score labels: **0 externally verified results** in analyzed captures. Existing `tools/task0022_result_join.py` has only an identity-protected strict join; no supplied provenance-verified score source was found in the repository. Official result access previously reported HTTP403; this phase did not establish a lawful reliable bulk result feed. Identity alone is not proof of score.
- Therefore claims of model edge, calibration, PnL, ROI, Sporttery BUY/PASS performance, 100-match trading record are **NOT EVALUABLE** with this corpus alone. No invented outcomes or implicit retrofitting.

## Evidence-based recommendation
**STOP** speculative profitability/backtests. **CONTINUE** bounded, scientifically useful work: (1) derive match/status/market flags canonical quote event history with explicit observed-time and provider-time gates, suppress replays; (2) acquire authorized real final-score provenance and strict fixture identity match; (3) only then run leakage-safe rolling decisions with pre-registered metrics. No new framework, broad new data campaign, automatic bets, or excessive backup project is justified at this gate.

## QA / reproducibility
Run: `python tools/task0028_timeline_gate.py --root <TASK0024-backup> --root <TASK0025-backup> --out <report.json>`. Tests `python -m pytest -q tests/test_task0028_timeline_gate.py tests/test_task0027_corpus_quality.py tests/test_task0022_result_join.py`: **7 passed**. Input manifests and SHA comparison are in the local independent backup root. Github stores script, tests, and this grounded report; not protected raw responses.

**Stage closure:** The actual quote-quality/feasibility phase is complete and receives **RESEARCH STAGE ACCEPT** for accurate diagnosis only; real outcome model/ROI phase remains **NO-GO**, not silently approved.
