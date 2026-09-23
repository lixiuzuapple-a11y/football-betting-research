# Legacy Evidence Ingestion Record — 2026-09-23

## Status

- Reviewer: ChatGPT
- Owner: Li
- Source location: `history/`
- Purpose: convert the owner-provided legacy export from a package archive into auditable evidence for the new project.
- This is **review/ingestion**, not a new backtest and not a WorkBuddy execution task.

## 1. Source package integrity

The owner placed the legacy export directly under:

`E:\OneDrive\OneDrive - Swire Properties Limited\webcodex\history\`

The package contains 19 primary ZIP volumes plus provenance files and historical backup archives.

On 2026-09-23 the reviewer recomputed SHA256 for all 19 primary ZIP volumes and compared them with `history/MANIFEST.md`.

Result:

- ZIP count checked: **19**
- SHA256 matched: **19**
- SHA256 mismatch: **0**

Therefore the 19-volume export is accepted as an intact copy of the manifest-described export.

This does **not** prove that the original research workspace itself was complete or correct; it proves only that the local ZIP files match the supplied export manifest.

## 2. Review extraction

The following packages were extracted into the local-only directory `history/_review/`:

1. `01_交付物_REPORTS.zip`
2. `02_顶层研究报告_md.zip`
3. `06_结果_results.zip`
4. `17_data_实验中间产物含e54.zip`
5. `18_data_其他派生素材.zip`

Review extraction:

- files: **239**
- bytes: **24,989,705**

`history/_review/` is ignored by Git.

The ZIP bundles themselves are also ignored by Git. Only lightweight provenance/index files may be versioned.

## 3. Why TASK-0003 is not being falsely marked complete

`TASKS/TASK-0003-legacy-asset-triage.md` specified a different external staging layout and a WorkBuddy collection/report lifecycle.

The owner-provided `history/` export:

- is directly readable by WebCodex;
- has its own manifest and README;
- is not the exact TASK-0003 staging structure;
- was not submitted through the TASK-0003 WorkBuddy lifecycle.

Therefore:

> **TASK-0003 is not retroactively marked ACCEPTED.**

For current research purposes the owner-provided export removes the immediate blocker that TASK-0003 was intended to solve: ChatGPT can now inspect the real legacy evidence directly.

No new WorkBuddy task is needed at this stage.

WorkBuddy will be used later only if the reviewer produces explicit file operations or reruns that require executor work.

## 4. Evidence inspected in first pass

### 4.1 Closeout / methodology

- `结案报告_竞彩足球长期正收益_v1.md`
- `研究方法论_可迁移框架_v2.md`
- `信息差路线_框架_v1.md`
- REV-3 inventory / revision notes

### 4.2 Market / timing / external-market experiments

- `results/e44_ttg_movement.md`
- `results/e52_clv_full.md`
- `results/e54_e55_pinnacle.md`
- `results/e56_had_crossmarket.md`
- `results/e57_league_calib.md`
- `results/e58_全玩法普查.md`

### 4.3 Intermediate/result artifacts

- `data/e28_stale_arb.json`
- `data/e30_crossplay.json`
- `data/e30b_control.json`
- `data/e30b_robust.json`
- `data/e54_join.csv`
- `data/e56_had_join.csv`
- related inventory dependency records

## 5. First-pass evidence findings

### 5.1 The legacy work is materially richer than a summary suggested

The archive contains actual historical experiments for:

- generic forecasting/model comparison;
- de-vig / pricing structure;
- FLB / odds buckets;
- open/close timing;
- CLV;
- cross-play mapping;
- Pinnacle vs Sporttery;
- league segmentation;
- single-bet availability;
- all-five-play census;
- Oracle / upper-bound checks;
- forward ledgers.

Therefore the new project must **crosswalk before rebuilding**.

### 5.2 Generic external-market prediction was tested, but the scope matters

E54/E55:

- final strict join: 4,596 matched games; analysis sample about 3,729;
- initial apparent +15.12% gross ROI was a row-order bug;
- corrected result: about −16.17% / −17.90% depending on analysis path;
- Pinnacle-derived total-goal information was statistically indistinguishable from Sporttery ttg after the relevant comparison;
- permutation result reported p = 0.806.

This is strong negative evidence against:

`Pinnacle-derived latent-goal model -> Sporttery ttg selection`

It is **not** a proof that every possible same-time quote residual or lead-lag event is impossible.

### 5.3 HAD cross-market evidence is negative but informative

E56 reports that Pinnacle 1X2 contained genuine information relative to random controls, but did not clear the Sporttery executable price hurdle in that matched sample.

This supports:

- information can exist without economic edge;
- cross-market residual needs an **actual executable same-time quote test**, not merely a better forecast.

### 5.4 Sporttery timing itself was heavily tested

E44 shows:

- Sporttery ttg prices genuinely change;
- >=2 official versions in 75.6% of its 82-match sample;
- price movement is observable and sometimes large.

E52, over 71,682 matches / 160,838 historical points, reports:

- 45.7% of matches had only one observed snapshot;
- median observed holding span about 9.8h;
- middle ttg buckets had statistically detectable open-to-close improvement, generally below 1%;
- legacy estimated break-even improvement for those buckets was roughly 21–28%;
- even an ex-post best-move historical upper bound in examined windows stayed below that legacy hurdle.

Therefore:

`Sporttery open-vs-close timing alone`

is strongly dominated for ttg in the legacy data.

But this does **not** equal:

`external sharp move occurs first AND Sporttery quote is still stale AND ticket remains executable`

The latter remains a separate D01 question.

### 5.5 Segmentation evidence supports removing Segmentation as a root

E57:

- league-level descriptive bias differences looked large;
- strict expanding-window league-specific correction had no incremental log-score value;
- paired M2−M1 ΔlogL = −0.00010, t = −0.33;
- league-specific linear version also failed.

This is direct project-specific evidence for the new framework decision:

> segmentation is a modifier / search axis, not an independent edge source.

### 5.6 Full-play census provides the main legacy execution baseline

E58 reports 10,947 matches / 591,138 odds rows and explicitly records single-bet availability.

Legacy sample observations:

| Play | legacy mean overround | historical single availability |
|---|---:|---:|
| had | 13.49% | 10.3% |
| hhad | 13.55% | 0.2% |
| ttg | 26.23% | 98.5% |
| crs | 43.68% | 100% |
| hafu | 26.21% | 98.5% |

These are **legacy observations, not permanent constants**. They must not be substituted for current executable quotes.

E58 also found:

- FLB-like structure across all five plays;
- all tested executable simple strategies remained negative;
- a very large CRS Oracle conditional structure existed, but was locked behind unachievable information requirements in the tested design.

### 5.7 Cross-play inconsistency needs careful reclassification

E30 initially found a had-vs-ttg latent-goal difference.

Later legacy notes explicitly revised its interpretation:

- much of the difference was attributable to the ttg pricing bias itself;
- the internal cross-play gap was not shown to be an independently exploitable edge;
- the result should not be interpreted as automatic arbitrage.

In addition, inventory lineage for the E30 result artifacts is only MEDIUM for some output-path relationships.

Therefore:

`C01 same-event cross-play consistency`

remains worth a **cheap deterministic re-audit**, but old E30 is not positive evidence of profitability.

## 6. Bug exposure imported from REV-3 inventory

Nine legacy bugs are recorded. Critical reviewer treatment:

- BUG-001: ROI denominator error; false +4844% -> about −18.24%.
- BUG-002: missing hit mask; false +549% -> about −18.24%.
- BUG-003: cKDTree index shape error; numerical degradation, not directly result inflation.
- BUG-004: E54 row-order mismatch; false +15.12% -> −16.17%.
- BUG-005: E58 merge without pool; cross-play Cartesian contamination.
- BUG-006: E54 v2 permissive join; about 27% mismatches; v3 strict join replaced it.
- BUG-007: E58 backfill metadata missing.
- BUG-008: E58 sample omission related to payout/poolStatus filtering.
- BUG-009: prospective ledgers stopped updating; only partially fixed at inventory time.

Rule:

> Any legacy conclusion touched by a bug is used only from the corrected artifact/version, or is marked REVALIDATE.

## 7. Current reviewer decision

The archive is now sufficient to start the formal:

`EDGE_EXHAUSTION_MATRIX`

No bulk migration into the new repository is justified.

The new repository should retain:

- lightweight provenance/index files;
- reviewer synthesis;
- explicit evidence crosswalks;
- later, only selected small reproducibility artifacts.

Raw/large legacy ZIP/data remain local.

## 8. Next action

Create and iteratively tighten:

`research/EDGE_EXHAUSTION_MATRIX_20260923_v1.md`

The matrix maps every frozen strategy family to:

- legacy experiment(s);
- evidence path;
- bug exposure;
- executable hurdle / availability;
- evidence strength;
- current status;
- kill reason;
- reopen condition.

Only after this reviewer step may an executor task be created for selected reruns, cleanup, or migration.

