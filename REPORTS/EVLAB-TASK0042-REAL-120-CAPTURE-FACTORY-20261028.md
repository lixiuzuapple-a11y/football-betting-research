# EV-Lab TASK-0042 — Real final cloud canary into the existing official factory

Date: 2026-10-28 (CST); independent offline, create-only run, on EV-Lab
evidence and EV-Lab repository only. **No new model predictions or bets.**

## Inputs / execution
- Immutable off-cloud source is the complete TASK-0041 final copy in
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0041-final-soak-20261028\task0041-official-20261027`.
  Source SQLite SHA256:
  `8dafc7075b6082d1bc87a7f4b1fc36d940e7b3df69e0993a4e277eb0b48a62cf`.
  Full direct and copied-source audits both classified 120 real observations:
  108 ok / 11 no_offer / 1 transport_error; 119/119 raw bytes verified.
- Reused existing `python -m tools.phase1_data_factory`, passed only this
  source `--root`, `--out-db` / `--out-summary` in entirely new folders.
  Default *fixed* `max_provider_age_hours=6`, `partial_scan=false`.
  Never changed that threshold after seeing results.
- Source and output databases are separate; raw bytes not pushed to Git.

## Real factory outcomes
- **120/120** source capture rows preserved in derived source ledger;
  **119** gzip source hashes verified, **2,484** fixture observations,
  **23** distinct fixture IDs, and **139** quote candidate events.
- Five market pools: HAD **29** (23 initial, 6 advance changes),
  HHAD **29** (23+6), TTG **26** (23+3), CRS **26** (23+3),
  HAFU **29** (23+6); total **139**.
- Stale, flagged and duplicate events were counted by existing gates,
  rather than retained as fresh candidate changes. The event store is
  *observed quote candidates*, not executable offers or expected returns.
- Independent SQL read-only verification on the derived SQLite:
  `PRAGMA quick_check=ok`; source status totals match raw audits;
  **0** candidate events at/after kickoff, **0** provider updates after
  capture, **0** missing source-capture joins, **0** source SHA mismatches.
  Only tables: `source_captures`, `fixtures`, `quote_candidates` —
  no settled results, BUY decisions, or betting transactions.
- First output folder:
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0042-official-factory-20261028`.
  SQLite SHA256:
  `10da1326ed04f637a6ea2fd29fad2661f5ce74b11e1ed0327ec7440a5c7930d3`;
  quality_summary.json SHA256:
  `aed1e20560354e6d4e31e81d20b943dd6c695e69118dadde5f95d18286790346`.
- Independently reran the **entire** 120-source ingestion into new
  `task0042-official-factory-replay-20261028` destination. Both output
  SQLite and summary SHA256 matched **byte-for-byte**.

## Regression qualification
- Added `tests/test_task0042_factory_canary_status.py`: (1) legitimate
  HTTP200 `no_offer`, a single transport error with no raw, and later
  successful quote capture import without source mutation; (2) tampered
  `no_offer` raw bytes fail closed with no published output.
- Targeted existing plus new data-factory tests: **9 passed** (0.80s).
- Full repository tests: **397 passed** (6.86s).

## Scope of successful progression
**Stage ACCEPT**: This proves the post-cloud real-source ingestion can feed
the already existing research quote-data factory with auditable safety filtering.
It does **not** demonstrate an autonomous cron/watchdog, qualified systemd
restart, valid future-team identity mapping across sources, automatic
multi-model forward predictions, verified new match results, any positive EV,
or a production bet. Next substantive research gate is automated
source-to-forecast *pre-kickoff* freeze with real model eligibility.
