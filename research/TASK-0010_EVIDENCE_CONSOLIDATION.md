# TASK-0010 — Evidence consolidation, as of 2026-10-09

## Audit scope and evidence grade
Based on versioned TASKS/REPORTS/REVIEWS and established research memos in this repository, not a fresh execution of the source datasets. Archived legacy bundles under ignored `history/_review/` and cloud-only TASK-0006 data are not magically Git-tracked. A document saying ACCEPTED is evidence of a formal prior verdict, not renewed independent scientific verification.

## Nine-task reconciliation

| Task | Formal latest decision | What was actually established | What was **not** established |
|---|---|---|---|
| 0001 | ACCEPTED | GitHub/WorkBuddy/Reviewer handoff smoke | Scientific validity or profit |
| 0002 | ACCEPTED | Legacy inventory and five documentation files migrated | All historical research claims verified |
| 0003 | ACCEPTED **via SUPERSEDED_BY_OWNER_HISTORY_BUNDLE** | Owner archive accessible, 19 ZIP manifests checked | Original WorkBuddy staging workflow executed; archive completeness outside declared scope |
| 0004 | ACCEPTED | synchronized free-source engineering smoke; Sporttery per-pool clocks/availability | Sharp provider change time, economic lead-lag |
| 0005 | ACCEPTED | Cloud collector qualified, source variant recorded, capture/confirmation controls | Variant = named bookmaker, source-quality fit for signal |
| 0006 | **REJECTED strictly sealed** | Five-day prospective capture intact: 14,656 captures, 7,100 rounds, 640/640 raw checks | Strict sealed compliance (S1 log and S2 completion aggregates leaked) |
| 0007 | ACCEPTED **procedure** | D01-B preregistered analysis + separate-code audit; 580 matched changes, 504 analyzable, 438 stale/executable observations | Clean lead-lag: **all 580 in >20 simultaneous-event batches**, no evidence in batch<=5; D01-B NOT VALIDATED |
| 0008 | ACCEPTED **procedure** | B01 preregistered synchronized analysis, 6,978 rounds and 33,453 selection observations, separate audit | Stable reference: **12/14 ever-positive pairs variant-dependent**; B01 NOT VALIDATED |
| 0009 | ACCEPTED **desk reconnaissance only** | Source alternatives categorized/permission-time semantics recorded | Alternative source passing all gates or actual new feed capture; SOURCE_QUALIFICATION_BLOCKED |

Sources: `REVIEWS/TASK-0001..0009.md`, `REPORTS/TASK-0006..0008.md`.

## Edge matrix corrections (do not overwrite 2026-09-23 snapshot)
`research/EDGE_EXHAUSTION_MATRIX_20260923_v1.md` predated TASK-0007/8. Its B01 and D01 prospective testing priorities are now **attempted and negative with current BetExplorer reference_proxy**. Do not call their generalized market mechanisms universally refuted: the source does not identify a stable independent sharp provider or its own quote update time. Equally, do not restart the identical pipeline or cherry-pick variants.

### Mechanism inventory
| Family | Today’s decision boundary | Evidence / reopen condition |
|---|---|---|
| B01 same-time pricing residual | CURRENT PROXY DOWNGRADED | Require independently qualified new reference and preregistration; no ROI rescue |
| D01-B reference move → executable Sporttery lag | CURRENT PROXY DOWNGRADED | Require defensible named market and observed/event timing; correct strict-seal implementation if replication becomes justified |
| C01 deterministic cross-play arbitrage | DOMINATED in tested historical HAD/CRS, TTG/CRS, HAD/HAFU constructions | Historical audited scans had zero full-cover arbitrage; probabilistic relative mispricing remains distinct/unproven |
| A01 generic public-model competition | DOMINATED under legacy tested setups | Only genuinely new point-in-time information or plausible economic upper bound may reopen |
| B03/B06/D03/D04 generic FLB/open-close/early-late timing | Mostly DOMINATED in documented legacy market/scope | New contract/ruleset/mechanism, not fresh threshold tuning |
| A03 player/lineups; A04 rest/travel; A05 weather/referee; A06 timestamped news; D02 news/lineup latency | UNTESTED / insufficient aligned evidence | Need predeclared availability times and incremental market-baseline hypothesis |
| A07 genuine information-coverage asymmetry | REVALIDATE; standalone league slicing negative | Define ex-ante coverage metric, frozen splits and OOS |
| B04/B05 demand shading | UNKNOWN/REVALIDATE | Independent demand proxy, no odds-bucket posthoc mining |
| C01 probabilistic cross-play residual; C03/C04 component/dependence pricing | UNKNOWN/REVALIDATE | Contract legality, exact current play rules and official pool availability; independence assumptions checked |
| E01 official subsidy/promotion | UNKNOWN | Effective-dated official subsidy contract with net payout arithmetic |

Status here is an **evidence inventory**, not TASK-0011's value ranking or an assertion that a hypothesis is profitable.

## Reuse catalogue — tracked and known external
- `src/football_betting/prospective/{ledger,collector,manifest}.py`, `deploy/` — capture/evidence, not automatically strict-sealed.
- `src/football_betting/data/{sporttery_webapi,betexplorer,provenance}.py` — provider/identity/time semantics, with reference variant caveat.
- `src/football_betting/matching/teams.py` and `assets/team_name_map.json` — conservative versioned crosswalk.
- `src/football_betting/odds/implied.py` — de-vig arithmetic, not truth-probability oracle.
- `src/football_betting/analysis/{d01b,b01}.py`, `tools/task0007*;task0008*`, `tests/test_task0007_d01b.py`, `tests/test_task0008_b01.py` — reproducible analysis tools and separate-code audits.
- `results/task0007/` — versioned results/diagnostics; TASK-0008 evidence is chiefly its REPORT and independent REVIEW, not an assurance all run intermediates are tracked.
- `research/LEGACY_EVIDENCE_INGESTION_20260923.md`, `research/P0_EVIDENCE_RECONSTRUCTION_20260923.md`, `research/DATA_SOURCE_ALTERNATIVES_RECONSTRUCTION_20260923.md`, `research/EDGE_EXHAUSTION_MATRIX_20260923_v1.md` — historical constraints/asset locations.
- `history/MANIFEST.md` inventories 19 ZIP volumes, but original ZIP/extracted artifacts are ignored local assets; cloud prospective dataset is also outside this Git tree. Reproduction requires custody/hash/access checks, not a Git clone alone.

## Concrete QA and research hazards
1. The data-source issue is *fit for a causal market hypothesis*, not blanket source unavailability. TASK-0004 already proved collection; TASK-0009 desk survey did not newly certify feeds.
2. TASK-0006 prospective evidence may be reused with its strict-seal defect plainly declared, never promoted to strictly sealed.
3. TASK-0007/8 independent computational paths are by same lead/reviewer, not independent human/agent replications.
4. Legacy evidence has known buggy result lineages; inventory verified export hashes, not every model's validity.
5. **Stale documentation defect**: `results/README.md` still says “Currently empty” and “No experiment has been run,” despite tracked `results/task0007/` and TASK-0007/8 completion. Correct as separate documentation hygiene when necessary; do not delete evidence.
6. The next study should explicitly define experimental unit/fixture clustering; high row counts per round must not be treated as independent matches.
7. Current 2026 Sporttery play rules, coverage and commercial API terms need effective-date confirmation before any economically meaningful experiment.
8. Don't manufacture a scientific ranking from this inventory; TASK-0011 is a separate mechanism/evidence/cost assessment.

## Boundary for TASK-0011
Select **one** candidate mechanism only after measuring novelty relative to historical tests, point-in-time input availability, actual Sporttery execution/settlement mapping, coverage and a falsification test that can be done with existing data first. Do not select by apparent historical ROI or convenience of an existing favorable subset. All task gates remain separate from research result gates.
