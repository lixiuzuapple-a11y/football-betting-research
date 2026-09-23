# EDGE EXHAUSTION MATRIX v1

**Date:** 2026-09-23
**Framework:** Applied Edge Taxonomy v1.0
**Scope:** China Sports Lottery football betting research under the current project charter
**Purpose:** map the frozen 32 strategy families to real legacy evidence before any new experiment is authorized.

---

## 0. Status language

- **KILLED** — the route, as precisely defined, is blocked by contract/rule/math or a credible upper bound.
- **DOMINATED** — evidence is strongly negative; do not spend on it unless a reopen condition occurs.
- **REVALIDATE** — relevant legacy evidence exists, but scope, bugs, ruleset, timing, or execution mapping prevents final closure.
- **SURVIVES** — enough mechanism remains to justify a controlled next test.
- **UNKNOWN** — theory exists but current evidence is insufficient.
- **UNTESTED** — no material legacy test located in the first-pass evidence review.

Evidence ladder:

- L0 mechanism only
- L1 retrospective association / deterministic audit
- L2 point-in-time or strict historical out-of-sample evidence
- L3 prospective sealed
- L4 executed
- L5 replicated

No route in this v1 matrix is promoted to stable live use.

---

## 1. Global execution facts inherited from legacy evidence

These are **historical observations** from E58 and related files, not timeless constants:

- legacy mean market overround: had ~13.49%, hhad ~13.55%, ttg ~26.23%, crs ~43.68%, hafu ~26.21%;
- legacy historical single availability: had 10.3%, hhad 0.2%, ttg 98.5%, crs 100%, hafu 98.5%;
- the old official payout-accounting ratio must never be substituted for actual quote overround;
- current research must calculate hurdle from the quote actually executable at the decision timestamp;
- same-event different Sporttery games cannot be mixed in one parlay under the current rule interpretation; separate-single analysis still depends on actual single availability.

Legacy clustering evidence also means nominal n must not automatically be treated as independent N_eff.

---

## 2. R1 — Information / Inference

| ID | Strategy family | Legacy evidence | Evidence | Bug exposure | v1 status | Why | Reopen condition |
|---|---|---|---|---|---|---|---|
| A01 | Poisson/DC/Elo/xG/Bayes/ML outcome model | exp02/Pitcan-style replication; E58 simple model tests; closeout synthesis | L2 | general legacy QA required | **DOMINATED** | Large historical/OOS body says generic public-data model improvements did not create economic edge; changing algorithm is not a new mechanism | genuinely new information set, new market structure, or upper-bound evidence showing room above actual hurdle |
| A02 | Market + feature residual model | E53/E54/E56 family; market-relative experiments | L2 partial | BUG-001/002/003 affect E53 lineage; BUG-004/006 affect E54 lineage but corrected versions exist | **REVALIDATE** | Corrected evidence is negative, but “market + genuinely new feature” is broader than tested lambda transforms | pre-registered new feature with point-in-time availability and incremental value over market baseline |
| A03 | Player / lineup / roster / tactical structured model | no decisive family-wide legacy experiment located | L0/L1 | unknown | **UNTESTED** | Legacy project did not establish an upper bound for high-quality player/lineup information as a class | acquire point-in-time lineup/player data and first test public-info upper bound before modelling |
| A04 | Rest / travel / congestion / motivation | scattered old hypotheses; no decisive family-wide audit found | L0/L1 | unknown | **UNTESTED** | plausible public features but no evidence they clear market baseline + Sporttery hurdle | pre-register one mechanism and test incremental residual over market |
| A05 | Weather / pitch / referee / venue | no decisive family-wide audit found | L0 | unknown | **UNTESTED** | not exhausted by generic model failure | new point-in-time data + public-info incremental test |
| A06 | Public news / coach / social / text extraction | no decisive family-wide audit found | L0 | unknown | **UNTESTED** | LLM/text processing is only an implementation; edge depends on timing/information not yet measured | measurable pre-price information lead with timestamped source |
| A07 | Low-coverage leagues / newly listed competitions | E57 segmentation negative for league calibration; E58 broad leagues | L2 partial | corrected legacy artifacts still need full lineage QA | **REVALIDATE** | “league segmentation” alone failed, but genuinely lower information coverage is a different mechanism | identify ex-ante coverage metric, not league label; show incremental OOS information |
| A08 | Private / non-public early information | none required | L0 | n/a | **KILLED (scope)** | non-scalable / compliance-sensitive and outside core research scope | owner explicitly changes project scope and legal/compliance review permits it |

---

## 3. R2 — Pricing / Market Microstructure

| ID | Strategy family | Legacy evidence | Evidence | Bug exposure | v1 status | Why | Reopen condition |
|---|---|---|---|---|---|---|---|
| B01 | Same-time Sporttery vs sharp consensus residual | E54/E55 ttg; E56 had; e54_join | L2 proxy | BUG-004/006 corrected in E54 v3; exact timestamp alignment still not established | **SURVIVES / REVALIDATE** | Legacy proves simple Pinnacle-derived predictors did not beat Sporttery; it does **not** fully test same-time executable residual distribution | build exact timestamp/contract alignment; measure residual vs later reference and realised outcome |
| B02 | 1X2 vs AH / O-U / exchange probability mapping | E53, E54/E56, e17/e18 pairs | L2 partial | BUG-001/002/003 around E53 lineage; join QA required | **REVALIDATE** | several mappings were negative but not every contract-equivalent mapping was exhausted | same-contract line-equivalence audit with strict IDs/timestamps |
| B03 | Favourite-longshot / draw bias | exp03; E51/E52; E58 all-play census | L2 | E58 BUG-005 corrected; BUG-007/008 require current canonical dataset check | **DOMINATED** | FLB-like bias is real but tested economic magnitude stayed below executable friction | regime/ruleset change or new OOS evidence of economically larger bias |
| B04 | Home / national / brand / popularity bias | no clean legacy family-wide test located | L0/L1 | unknown | **UNKNOWN** | cannot infer from generic FLB | pre-register exact demand mechanism and acquire demand/proxy data |
| B05 | Demand-driven shading / odds-bucket bias | E58 bucket results; E52 drift patterns | L2 partial | E58 corrected dataset required | **REVALIDATE** | price-bucket structure exists; causality/demand channel and prospective persistence not established | independent OOS period with family-wise correction |
| B06 | Opening-price systematic mapping bias | exp04; E44; E52 | L2 | E52 documents its own repaired defects | **DOMINATED for ttg / REVALIDATE globally** | ttg opening advantage was far below break-even requirement; other plays not equivalently exhausted | current-rule, other-play opening data with executable snapshots |
| B07 | Venue/bookmaker dispersion / direct cross-market arb scan | E54/E56 comparisons, but no complete all-venue arbitrage census located | L1/L2 partial | join/timestamp quality critical | **UNKNOWN / OUT-OF-CORE EXECUTION** | price dispersion may exist but overseas execution is outside core; still useful as diagnostic reference | keep as diagnostic unless project execution scope changes |

---

## 4. R3 — Product / Contract

| ID | Strategy family | Legacy evidence | Evidence | Bug exposure | v1 status | Why | Reopen condition |
|---|---|---|---|---|---|---|---|
| C01 | Same-event cross-play probability consistency | E30/E30b; E53; E58; later E30 interpretation in 信息差路线_框架_v1 | L1/L2 partial | E30 output lineage MEDIUM; E53 BUG-001/002/003; E58 BUG-005 | **SURVIVES / REVALIDATE** | old cross-play “裂缝” was later largely explained as pricing-style difference, not proven edge; cheap deterministic consistency audit remains valuable | rerun on canonical corrected all-play rows, same timestamp/ruleset, enforce single availability |
| C02 | Basic M串1 pricing consistency | E58 availability + parlay arithmetic discussions | L1 | rule/version mapping needed | **DOMINATED as edge source** | ordinary parlay packaging does not create edge; forced parlay usually increases friction | only reopen for a documented payout inconsistency, not because of parlay shape alone |
| C03 | M串N component-set pricing | no decisive canonical legacy audit located | L0/L1 | unknown | **UNKNOWN** | may be mechanically auditable at low cost; must expand into component contracts | obtain current M串N rules/quotes and verify component payout exactly |
| C04 | Cross-match dependence / correlated legs | no decisive legacy family-wide test located | L0 | unknown | **UNTESTED** | dependence exists in principle but economic residual was not established | pre-specify causal dependence and show joint mispricing survives compound friction |
| C05 | Same-match dependence | rule analysis | L0/L1 | ruleset version critical | **KILLED for mixed-parlay form** | current rules prohibit same-match different games mixed in one parlay | separate-single form can reopen only when every required leg is individually offered |
| C06 | Rounding | rule/settlement discussions | L1 deterministic | current rule version required | **DOMINATED** | scale is mechanically small relative to normal friction | documented directional rounding large enough to change EV |
| C07 | Prize cap | E58/rule analysis | L1 deterministic | ruleset version required | **KILLED as positive edge** | cap truncates upside; it is a friction/constraint, not an edge generator | only changes if a new rule introduces an asymmetric subsidy |
| C08 | Void / cancellation / refund | rule analysis; no statistically useful legacy case base found | L0/L1 | ruleset version critical | **UNKNOWN / LOW VALUE** | rare and likely neutral, but full historical case audit not done | evidence of predictable asymmetric contract transformation |
| C09 | Settlement / line-equivalence / ruleset-version mapping | many legacy joins; current framework requirement | L1 infrastructure | several legacy bugs arose exactly here | **SURVIVES as CORE VALIDATION** | not itself a profit edge, but every product/pricing test fails without it | never “closed”; keep as mandatory execution adapter control |

---

## 5. R4 — Timing / Access / Execution

| ID | Strategy family | Legacy evidence | Evidence | Bug exposure | v1 status | Why | Reopen condition |
|---|---|---|---|---|---|---|---|
| D01 | Sharp lead-lag / stale quote | E28 proxy; E44 Sporttery movement; E54/E56 market comparisons | L1/L2 proxy | timestamp equivalence not proven | **SURVIVES / HIGHEST PRIORITY** | old timing studies mainly test Sporttery open→close or derived CLV; they do not fully observe “sharp moved first, Sporttery stayed stale, ticket executable” | exact dual-market timestamp data; preregister move threshold and executable window |
| D02 | Lineup/news/event reaction lag | no decisive timestamped legacy test located | L0 | n/a | **UNTESTED** | mechanism distinct from generic news modelling because value is latency | timestamped source event + Sporttery repricing/cutoff log |
| D03 | Early quote / price-lock timing | E52 open→close ttg | L2 | repaired E52 defects documented | **DOMINATED for ttg** | historical open-price improvement was far too small | other play/ruleset with materially different movement distribution |
| D04 | Pre-close / cutoff drift | E44/E52 | L2 | historical truncation in 2016–2019 explicitly documented | **DOMINATED for generic ttg timing / REVALIDATE execution** | generic drift insufficient; actual last executable quote vs final observed quote still needs execution mapping | verified cutoff + purchase-lock timestamp dataset |
| D05 | Terminal / execution latency anomaly | no credible legacy evidence | L0 | n/a | **DOMINATED / OUT OF CORE** | operational glitch hunting is fragile, low capacity, and not required for scientific objective | only if normal execution logs reveal a stable benign latency effect |

---

## 6. R5 — External / Mechanical

| ID | Strategy family | Legacy evidence | Evidence | Bug exposure | v1 status | Why | Reopen condition |
|---|---|---|---|---|---|---|---|
| E01 | Official prize promotion / temporary subsidy | no complete legacy archive located in first pass | L0 | ruleset/effective date critical | **UNKNOWN** | deterministic if an official promotion materially changes payout | official current notice + exact contract-level EV calculation |
| E02 | System misquote / settlement anomaly | scattered rule discussions only | L0 | n/a | **OUT OF CORE / UNKNOWN** | rare, potentially voidable, not a scalable research program | only record observed incidents; do not build exploit program |
| E03 | Rebate / commission / outside bonus | outside official Sporttery core | L0 | n/a | **KILLED (scope)** | depends on external/off-book transfer and compliance risk | explicit project-scope change + verified legal/contractual source |

---

## 7. Cross-cutting modifier: Segmentation

Segmentation is not a root and does not receive a separate family count.

Legacy E57 is especially relevant:

- large descriptive league differences existed;
- expanding-window league correction added no value;
- M2−M1 ΔlogL ≈ −0.00010, t ≈ −0.33;
- threshold sensitivity stayed zero/negative.

Therefore any future:

- league;
- odds bucket;
- team class;
- weekday;
- favourite/longshot;
- market phase;

filter must attach to a named underlying mechanism and must be evaluated with:

- frozen family definition;
- multiplicity control;
- point-in-time OOS;
- prospective sealed confirmation where economically material.

---

## 8. Priority after legacy ingestion

### P0 — do next

1. **B01 + D01 combined audit**
   - exact Sporttery quote timestamp;
   - exact sharp/reference quote timestamp;
   - same event / market / selection / line / settlement;
   - later reference move;
   - actual Sporttery availability/cutoff;
   - residual distribution and lead-lag event study.

2. **C01 deterministic cross-play re-audit**
   - corrected E58 dataset;
   - same timestamp;
   - current ruleset;
   - single availability;
   - synthetic state-payoff consistency;
   - no post-hoc model fitting required.

### P1 — only after P0

- D02 lineup/news lag;
- B04/B05 demand-shading mechanisms;
- C03/C04 M串N/dependence;
- A07 true coverage asymmetry;
- A02 one pre-registered public-information residual family.

### P2 — do not spend now

- more generic model architectures;
- more league slicing;
- generic “early vs late” timing;
- Kelly/portfolio/sizing;
- LLM multi-agent prediction;
- rounding/cap as main alpha thesis.

---

## 9. What is now actually exhausted?

### Strongly exhausted / dominated in the legacy scope

- generic public-data model competition against market baseline;
- league segmentation as a standalone improvement;
- generic ttg open-vs-close timing;
- simple Pinnacle-derived ttg probability model;
- simple Pinnacle 1X2 → Sporttery HAD selection in the matched legacy sample;
- FLB/odds-bucket effects as sufficient standalone edge;
- plain parlay as an edge source.

### Not exhausted

- exact **same-time** Sporttery-vs-sharp executable residual;
- exact **lead-lag** stale window after sharp moves;
- lineup/news event-to-reprice latency;
- corrected all-play deterministic cross-play consistency under actual availability;
- M串N component and dependence pricing;
- currently effective official promotion/subsidy edge.

That distinction is the main output of v1.

---

## 10. Gate

The next research step must not be “build a better predictor”.

It is:

`P0 evidence reconstruction -> exact contract/timestamp alignment -> falsification`

If P0 is closed negatively with adequate data and a credible upper bound, the project should substantially reduce or stop further positive-EV search rather than proliferate models.
