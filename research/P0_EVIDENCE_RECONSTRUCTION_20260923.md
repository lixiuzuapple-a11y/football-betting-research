# P0 Evidence Reconstruction — C01 / D01 / B01

**Date:** 2026-09-23  
**Reviewer:** ChatGPT  
**Inputs:** owner-provided legacy export under `history/`, local-only extracts under `history/_review/`, Applied Edge Taxonomy v1.0  
**Purpose:** use the actual legacy assets to tighten the two P0 routes before commissioning new execution work.

---

## 1. Scope

This pass answers three narrow questions:

1. **C01** — does the archived all-play Sporttery data already show a deterministic same-event cross-play no-risk arbitrage?
2. **D01** — does the archived timing evidence support a generic “sharp moves first, Sporttery remains stale long enough” thesis?
3. **B01** — do the archived cross-market joins contain the exact same-time quote timestamps needed to close the Sporttery-vs-sharp residual question?

No new predictive model is fit. No historical result is promoted merely because it looks profitable.

---

## 2. C01 — same-event cross-play consistency

### 2.1 Exact same official update timestamp, single-eligible only

Local audit:

`history/_review/c01_crossplay_arb_audit.json`

Source:
- `e58_census_odds.csv`
- 605,565 rows
- 21,116 match/update keys
- exact same official update timestamp
- only states marked single-eligible

Results:

### HAD + CRS full-state cover

- n = 15 comparable states
- minimum total no-risk cover cost = **1.1220**
- median = **1.1294**
- maximum = **1.1439**
- arbitrage cost < 1: **0**
- near-arbitrage cost < 1.01: **0**
- near-arbitrage cost < 1.02: **0**

### TTG + CRS conservative synthetic cover

- n = 2,225 comparable states
- minimum total no-risk cover cost = **1.2008**
- median = **1.3119**
- maximum = **1.3149**
- arbitrage cost < 1: **0**
- near-arbitrage cost < 1.01: **0**
- near-arbitrage cost < 1.02: **0**

Interpretation:

> In the exact-same-update, single-eligible constructions tested, the archive contains **no deterministic no-risk arbitrage**.

This does not prove every possible multi-play probabilistic inconsistency is absent, but it materially narrows C01.

### 2.2 Carry-forward quote reconstruction

Local audit:

`history/_review/c01_crossplay_carryforward_audit.json`

Reconstruction:
- each pool quote carried forward from its official update timestamp until the next observed update
- 33,483 reconstructed snapshots
- 11,169 matches
- single-eligible only

Results:

#### HAD + CRS
- n = 1,460
- minimum cover cost = **1.1103**
- median = **1.1297**
- arbitrage count = **0**

#### TTG + CRS
- n = 16,835
- minimum cover cost = **1.2008**
- median = **1.2543**
- arbitrage count = **0**

A synthetic route can occasionally be cheaper than the directly quoted equivalent component, but the complete no-risk cover still remains above 1. This is a **relative pricing inconsistency**, not an arbitrage proof.

Caveat:
- actual sales cutoff is not present in this archive
- this is not a complete linear program over every possible product combination

### 2.3 HAD + HAFU carry-forward

Local audit:

`history/_review/c01_had_hafu_carryforward_audit.json`

- n = 1,179
- minimum full cover cost = **1.1103**
- median = **1.1296**
- arbitrage count = **0**
- best synthetic/direct component ratio = **0.9340**

Again, a synthetic representation may sometimes be cheaper than the direct component, but the full contract set does not produce a no-risk positive payoff in the tested construction.

### C01 decision

Split the old broad C01 into two claims:

1. **C01-A pure deterministic cross-play arbitrage**  
   Status: **DOMINATED / NEGATIVE IN TESTED CONSTRUCTIONS**.

2. **C01-B probabilistic cross-play residual after correct settlement, timestamp and availability mapping**  
   Status: **REVALIDATE**, but priority is lower than before.  
   A future test is justified only if it asks whether the relative inconsistency predicts realised state probabilities, not whether an already-observed pure arbitrage exists.

---

## 3. D01 — generic stale-quote / lead-lag thesis

### 3.1 Archived feasibility analysis

Local evidence:

`history/_review/18_data_其他派生素材/data/latency_arb_feasibility.json`

The old analysis used a historical HAD executable hurdle of roughly **12.88% relative move** (`jc_k = 0.8859`). This is a legacy quote-derived hurdle, not the current system-wide payout ratio.

Sporttery update sample in that file:

- 29 matches
- 121 observations
- stale span median = **2.35h**
- stale span p90 = **9.34h**
- maximum = **26.34h**
- update-gap median = **3.15h**
- observed max single-outcome move at update:
  - median = **3.73%**
  - p90 = **7.53%**
  - max = **11.84%**

The same file explicitly concludes:

> the literal “Sporttery is stale for hours, therefore a sufficiently large sharp-market move can usually be harvested” thesis is not supported under its assumptions.

Its own blocking unknowns are more important than its point estimate:
- the **same-time Sporttery-vs-Pinnacle residual tail was never measured adequately**;
- which Pinnacle timestamp Sporttery effectively references is unknown;
- whether Sporttery fully or partially corrects at updates is unknown;
- executable old-price lock behavior needs to be proven.

### 3.2 E28 retrospective CLV proxy

`e28_stale_arb.json`

- 5,900 matches
- seasons: 2017/18, 2024/25, 2025/26
- multiple assumptions about how much closing-market movement was knowable at decision time
- partial correlation between the proxy and outcome quality only about **0.035–0.041**
- every reported CLV bucket in the displayed analyses remained negative ROI

This is additional negative evidence against a generic “movement itself is alpha” interpretation.

### D01 decision

The route must be split:

1. **D01-A generic Sporttery stale timing / open-to-close harvesting**  
   Status: **DOMINATED in legacy scope**.

2. **D01-B exact external sharp move → still-executable stale Sporttery quote**  
   Status: **REVALIDATE / DATA GAP**.  
   The archive does not contain the exact simultaneous external-market snapshots required to close this route.

So D01 is no longer treated as one undifferentiated “highest priority” thesis.

---

## 4. B01 — exact same-time Sporttery vs sharp residual

### 4.1 What the archive has

`e54_join.csv`:
- 4,596 matched rows
- includes Pinnacle opening/closing fields such as `PSH/PSD/PSA`, `PSCH/PSCD/PSCA`
- includes Sporttery match identity
- **does not contain an external-market observation timestamp**

`e56_had_join.csv`:
- 3,430 rows
- includes Sporttery HAD prices and Pinnacle opening fields
- **does not contain synchronized external quote timestamps**

`e58_census_odds.csv`:
- 605,565 Sporttery rows
- has official update timestamp `upd`
- has single eligibility
- is rich enough to reconstruct Sporttery-side quote history
- **does not supply a same-time sharp-side quote history**

`fb_ttg_series.csv`:
- 160,855 Sporttery TTG rows
- contains `updateDate/updateTime`

`jc_ttg_ts.csv`:
- 43,568 captured Sporttery rows
- contains both collector `snapshot_time` and `official_update_time`

These are useful for the Sporttery side, but not sufficient to manufacture an exact same-time sharp residual.

### 4.2 What the old scripts actually used

The archived Pinnacle work predominantly uses football-data.co.uk:
- Pinnacle opening odds
- Pinnacle closing odds

Those are suitable market baselines and ex-post references, but they are **not an exact timestamped sharp quote stream**.

Therefore:

> **B01 cannot be honestly closed from the current archive alone.**

Using closing odds as if they were the quote observable at each Sporttery update would recreate the exact timing error the new framework is designed to prevent.

### B01 decision

Status remains:

**SURVIVES / REVALIDATE — missing synchronized dual-market data**

The next engineering requirement is now precise:

> obtain or prove unavailable a timestamped sharp/reference quote source that can be sampled concurrently with Sporttery, preserving the same event / market / selection / line / settlement contract.

This is a data-acquisition problem, not a modelling problem.

---

## 5. Consequence for research priority

After direct evidence reconstruction:

### Closed or materially downgraded

- generic ttg open-vs-close timing
- generic stale-price harvesting
- pure deterministic HAD/CRS, TTG/CRS, HAD/HAFU no-risk cross-play arbitrage in the tested constructions

### Still open

1. **B01 exact same-time Sporttery-vs-sharp residual**
2. **D01-B true event-driven stale window**, but only as a subset of the same synchronized data collection
3. **C01-B probabilistic cross-play relative mispricing**, lower priority and only after deterministic consistency/availability controls

### Do not do next

- another prediction model
- more threshold sweeps
- another league slice
- another open-vs-close proxy using closing prices as decision-time data

---

## 6. Executor boundary

The reviewer can finish the evidence interpretation from the local archive.

A new executor task is justified only for the remaining engineering gap:

**TASK-0004 — synchronized Sporttery + sharp quote capture feasibility / smoke test.**

The task must not substitute:
- closing odds,
- daily opening odds,
- a soft-book average,
- or a synthetic probability model

for a timestamped sharp/reference quote stream.

If no suitable source is accessible without new credentials/cost, the correct deliverable is a blocker report, not fabricated data.

---

## 7. Gate

Current gate:

`LEGACY P0 RECONSTRUCTION = COMPLETE ENOUGH TO COMMISSION DATA-FEASIBILITY TASK`

Next:

`TASK-0004 -> source/collector feasibility -> tiny synchronized smoke dataset -> Reviewer validation`

Only after that can B01/D01-B receive a real falsification experiment.
