# TASK-0042 — Real bounded cloud capture → verified official data factory

Date: 2026-10-28. Scope: EV-Lab only.

## Goal
Use the actually completed TASK-0041 120-round official-only canary as the
first *new* post-cloud, immutable input to the already accepted Phase1 data
factory. Validate a full nonpartial scan, immutable source, status handling,
actual observed timestamps, provenance links and reproducible derived output.
Do not duplicate the ingestion framework or overwrite earlier roots.

## Requirements
1. Independently close TASK-0041 after terminal systemd status and full raw
   byte/SQLite audit (including any real transport failures).
2. Copy the final source root to an EV-Lab-only machine-local backup. Preserve
   source SQLite SHA; do not publish third-party raw data to Git.
3. Run `tools.phase1_data_factory` with default previously frozen 6-hour
   provider quote freshness gate into a fresh, create-only destination.
4. Independently query source-count parity, joined raw-hash references,
   event-before-kickoff timestamps, allowed provider-update order, and SQLite
   integrity; verify no results or bets were materialized.
5. Rebuild into a separate new destination with unchanged inputs and compare
   both derived SQLite and summary exact SHA256.
6. Add regression coverage for mixed `ok`, `no_offer`, transport errors,
   and tampered non-OK source bytes.

## Acceptance
ACCEPT only the *bounded 120-row cloud → research quote candidates* link if
all checks and whole-repository tests pass. No production scheduler, reboot
recovery, full odds execution verification, ongoing future-model forecasts,
Pinnacle CLV, or profitable EV is proven in this task.

Status: REVIEW → reviewer QA upon completion.
