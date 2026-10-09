# TASK-0009 — Reference source qualification (desk evidence, 2026-10-09)

## Input evidence and separation
TASK-0007 = procedure ACCEPTED / D01-B NOT VALIDATED; TASK-0008 = procedure ACCEPTED / B01 NOT VALIDATED. Source-quality defects are not erased. No live candidate-source credentials were used; no authenticated quotes, Sporttery overlap test or novel prospective samples were obtained. The following is **documentation-level qualification only**, not runtime/data-source certification.

## Source matrix vs precommitted Q0–Q7
| Candidate | Identity & timing evidence | Access / pricing | D01-B eligibility | B01 eligibility | Decision |
|---|---|---|---|---|---|
| football-data.co.uk fixtures.csv BFE columns | Betfair exchange columns; collected periodic static fixture sheet (typically Fri/Tue), not timestamped each quote move | openly downloadable; coverage/rights must be assessed | FAIL Q2 event lead timing | POTENTIAL historical coarse baseline only; Q4 untested | Keep as free baseline; reuse legacy fetcher |
| Betfair Delayed Exchange API | Named exchange market/runner IDs; delayed observations variable 1–180s; delayed Stream batches changes every 3min | Betfair verified account + app/session key, delayed development key without activation fee; geography/terms unverified | FAIL real-time causal seconds-scale timing | CANDIDATE for coarse market reference only; Q0/Q4/Q5 untested | No account operations authorized |
| Pinnacle bespoke API | Named bookmaker; API specs & time quality must be tested under actual access | approval and variable fee, research applicants possible; no public free API | CONDITIONAL only after approved access and timing verification | CONDITIONAL | Blocked pending permission/budget |
| The Odds API V4 | Named bookmakers; market-level last_update is time vendor last saw bookmaker odds, not necessarily bookmaker origin update; historical snapshots 5-min since Sept 2022 | API key; historical endpoint paid | FAIL source-origin update timing / minute-scale history for D01-B | CANDIDATE coarse matched residual; Q0/Q4/Q5 untested | No purchase |
| BetExplorer current reference_proxy | TASK-0007: all 580 matched changes in >20 mass batches; TASK-0008: 12/14 ever-positive selection pairs not positive in every variant | Existing collector | REJECT current D01-B source | REJECT current B01 source | Negative control only |
| 500.com Sporttery mirror | Third-party mirror, not provider-declared official HAD executability | prior access reported; current not qualified | NOT substitute for execution truth | NOT substitute for official execution truth | Research cross-check only |

## Official references verified on 2026-10-09
- https://support.developer.betfair.com/hc/en-us/articles/360009638032-When-should-I-use-the-Delayed-or-Live-Application-Key
- https://support.developer.betfair.com/hc/en-us/articles/115003887871-How-do-I-get-access-to-the-Stream-API
- https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access
- https://support.developer.betfair.com/hc/en-us/articles/360002464152-Which-API-Licence-Do-I-Require
- https://www.pinnacle.com/en/api
- https://github.com/pinnacleapi/pinnacleapi-documentation
- https://football-data.co.uk/matches/resources/fixtures.csv
- https://the-odds-api.com/liveapi/guides/v4/
- https://the-odds-api.com/historical-odds-data/

## Findings and limitations
- A named source alone is insufficient: the provider-origin price change time must not be inferred from when our collector received a periodically refreshed page.
- Betfair Delayed is legitimate for authorized development, but cannot resolve quote sequencing under short latency; live Betfair key is not an approved pure research/read-only shortcut and requires fee and betting-related eligibility.
- football-data's periodic weekly fixture file is valuable for price-calibration baseline, not an independent lead-lag clock.
- The Odds API last_update means its own observation time and does not establish the upstream bookmaker's true price event time.
- The Sporttery 19/24 fixture coverage from TASK-0007 cannot automatically be ascribed to any substitute. Every new source must report a fresh prospective join denominator.
- No source presently passes all Q0–Q6. This is an **access/evidence gap**, not proof all possible sources are economically useless.

## Gate and follow-up design
**Disposition: SOURCE_QUALIFICATION_BLOCKED** for D01-B and B01 operational progression. Do not start another five-day collector, paid integration, ROI study or BUY/PASS signal.
A future TASK-0010 may run a single short paper-only smoke AFTER one source has legal access and credible stable bookmaker/market IDs, with: frozen fixture universe; raw hashes; strict capture clocks; no outcome lookup; official Sporttery simultaneous HAD; variant and batch stability audit; no upstream update-time claim if absent. Stop if official Sporttery overlap or licensing fails.
Use existing provider/ledger/matching/de-vig code and legacy fetch scripts; do not introduce a third data pipeline.
