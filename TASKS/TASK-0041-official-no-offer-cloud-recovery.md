# TASK-0041 — Official no-offer cloud collector recovery

Date: 2026-10-27. Project: EV-Lab / football-betting-research.

## Scope
Resume the interrupted bounded official Sporttery collector experiment. Verify the failed historical service, preserve its raw evidence, classify legitimate HTTP200 no-sale responses as `no_offer`, independently validate a new bounded cloud service, and record the limits. No other repository, trading order, or original data root may be changed.

## Acceptance gates
1. **A — Historic forensics:** original journal/exit reason; SQLite quick_check; verify every raw gzip SHA and byte length; reclassify without changing stored history.
2. **B — Regression:** true `no_offer` does not exhaust bad-response threshold; invalid or transport/source responses remain failure; SHA tampering rejected.
3. **C — New bounded canary:** isolated directory, frozen source identity, prescribed rounds/duration; demonstrate legitimate no-offer followed by continued real HTTP200 samples and byte-level provenance.
4. **D — Final soak:** after canary terminates, verify all observations, ending service state, and reason. **Do not call D complete before it ends.**

Raw bookmaker/provider files stay in EV-Lab-controlled evidence locations, outside Git. No inference about actual positive EV, CLV, or live profitability.

Status on 2026-10-27: **A/B/C startup ACCEPTED; D PENDING**.
