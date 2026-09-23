# Data-source alternatives reconstruction — legacy evidence correction

**Date:** 2026-09-23  
**Reviewer:** ChatGPT  
**Trigger:** Owner recalled that earlier research had already documented substitutes when paid or blocked data sources were encountered.  
**Purpose:** re-open the legacy evidence before accepting TASK-0004's conclusion that synchronized comparison was blocked by lack of free sources.

---

## 1. Executive correction

The Owner's recollection is supported by the legacy files.

TASK-0004 correctly observed that:

- current Sporttery official web/API access from this owner-machine client returns HTTP 567;
- Pinnacle direct endpoints are not freely accessible here;
- The Odds API / Betfair official API require credentials.

However, the conclusion:

> no acceptable free reference path exists without new credentials/payment

is **too strong** and is not consistent with the legacy research record.

The old project had already built and documented multiple substitute paths:

1. **football-data.co.uk `fixtures.csv` + Betfair Exchange (BFE) columns**
   - free / unauthenticated;
   - old production code records our own `snapshot_time`;
   - historical production policy explicitly used BFE as the sharpest pre-match reference available from that feed;
   - archive `market_odds.csv` contains actual BFE snapshots.

2. **BetExplorer current/fixture odds**
   - free / unauthenticated server-rendered 1X2 pages;
   - old collector records our own `snapshot_time`;
   - exp09 cross-validation against Pinnacle closing probabilities supported BetExplorer as a **market proxy** for the tested European leagues;
   - old production priority was:
     `BFE > BetExplorer > soft-book consensus`.

3. **500.com Sporttery mirror**
   - free / unauthenticated;
   - used for current / rolling historical Sporttery data;
   - old TTG data were cross-validated against official Sporttery with median difference 0.0000 on 74 matched cases;
   - can serve as a clearly labelled **third-party Sporttery mirror** when the official endpoint is temporarily unreachable, subject to source-quality flags.

4. **Cloudflare Workers + Cron**
   - explicitly designed as a zero-cost foreign-node option for international-market collection;
   - recommended in legacy research before paid The Odds API;
   - no worker implementation was found in the archived scripts, so this remains **designed but not proven**.

Therefore TASK-0004 needs revision: it must evaluate these already-known substitute paths before a final BLOCKED verdict.

---

## 2. Legacy evidence — free international reference paths

### 2.1 football-data.co.uk / Betfair Exchange

Source code:

`history/_review/05_脚本_scripts/scripts/fetch_market_odds.py`

Key recorded design:

- `fixtures.csv` is fetched free without a key;
- every collected row receives `snapshot_time`;
- provider field definitions were corrected against football-data.co.uk `notes.txt`;
- `BFEH/BFED/BFEA` are Betfair Exchange prices;
- commission-adjusted BFE probabilities are computed;
- BFE is explicitly designated the strongest pre-match reference available in that feed;
- if BFE is absent, the code falls back to soft-book consensus.

Old production file:

`history/_review/18_data_其他派生素材/data/market_odds.csv`

Reviewer re-count on 2026-09-23:

- total rows: **120**
- rows with complete BFE 1X2: **100**
- `mkt_source=betfair_exchange_comm5`: **100**

Examples include BFE overround around ~0.5%–1.1% before commission adjustment, demonstrating that this was not merely an unused code path.

Old operating manual:

`history/_review/02_顶层研究报告_md/模拟盘运行手册.md`

Daily pipeline explicitly included:

> 3a/5 抓外部市场·football-data（欧洲主流，含 Betfair 交易所）

### 2.2 Current status of football-data feed

Reviewer live check on 2026-09-23:

- `https://www.football-data.co.uk/fixtures.csv` -> HTTP **200**
- columns still include:
  - `BFEH/BFED/BFEA`
  - `BFE>2.5/BFE<2.5`
  - `BFEAHH/BFEAHA`
  - closing variants.

But the file was currently stale:

- min date: 2026-09-18
- max date: 2026-09-20
- future rows relative to 2026-09-23: 0

Conclusion:

> the path exists and historically worked, but is not currently sufficient by itself for a 2026-09-23 synchronized smoke capture.

It should be marked **temporarily stale**, not “nonexistent / paid”.

---

## 3. Legacy evidence — BetExplorer as market proxy

Source:

`history/_review/02_顶层研究报告_md/侦察_外部数据源实测_20260902.md`

Exp09 cross-validation result:

- six European leagues;
- median absolute probability difference versus Pinnacle closing: **0.467pp**;
- correlation: **0.994–0.998**;
- RPS difference: **−0.0012 to +0.0008**;
- pre-specified H0 accepted.

Legacy conclusion:

> **BetExplorer 可作市场代理。**

Known bias:

- roughly home −0.2pp / away +0.2pp versus Pinnacle in the tested leagues.

Collector:

`history/_review/05_脚本_scripts/scripts/fetch_betexplorer.py`

Important facts:

- service-rendered league fixture/results pages;
- 1X2 odds are present directly in HTML `data-odd`;
- records `snapshot_time` at collection;
- explicitly designed as the source for J1 / K1 / Saudi / cup competitions not covered by football-data.

Production integration:

`pair_markets.py` and the operating manual used priority:

> **BFE > BetExplorer > soft-book consensus**

### Current status

Reviewer live check on 2026-09-23:

`https://www.betexplorer.com/football/england/premier-league/fixtures/`

returned:

- HTTP **200**
- ~289 KB HTML
- **60** `data-odd` occurrences
- fixture rows present (e.g. Arsenal–Leeds, Aston Villa–Brentford, Chelsea–Bournemouth).

This directly contradicts treating BetExplorer only as an historical opening/closing label source.

Timestamp semantics:

- BetExplorer does not expose a trusted provider quote-update timestamp in this path;
- but the project can record **our own observed_at / snapshot_time**, exactly as the old collector did.

The original TASK-0004 schema says provider `source_updated_at` is required **if the provider exposes it**. Therefore lack of provider update time does not by itself invalidate BetExplorer as a point-in-time observed reference.

Caveat:

> BetExplorer is a validated **reference proxy**, not Pinnacle itself and not proven equivalent to Pinnacle on every league or at every moment.

It is sufficient for a smoke/feasibility path if labelled honestly.

---

## 4. Legacy evidence — Sporttery-side fallback

### 4.1 Official endpoints

Legacy authoritative route:

- `getMatchCalculatorV1.qry` current/on-sale
- `getUniformMatchResultV1.qry` historical index
- `getFixedBonusV1.qry?clientCode=3001&matchId=...` historical full oddsHistory.

The old project eventually discovered that `getFixedBonusV1` provides all five pools and full update timestamps back to 2016.

Current 2026-09-23 owner-machine check:

- official current calculator -> **HTTP 567**
- historical fixed bonus -> **HTTP 567**

Therefore official access is genuinely blocked in this client today.

### 4.2 500.com mirror

Legacy evidence:

`history/_review/02_顶层研究报告_md/资产登记册_v1.md`

Known routes:

- `https://trade.500.com/jczq/?date=<YYYY-MM-DD>`
- TTG: `?playid=270&g=2&date=<YYYY-MM-DD>`
- other playids recorded for score / half-full / handicap.

Legacy verified properties:

- current and rolling 1–30 day data accessible;
- beyond 30 days silently falls back to current listings;
- TTG cross-validation against official data:
  - 458 archived rows
  - **74 matched official cases**
  - median odds difference **0.0000**
  - `Σ(1/O)` consistent with official.

Current Reviewer live check on 2026-09-23:

`https://trade.500.com/jczq/`

returned:

- HTTP **200**
- ~116 KB HTML
- **11** `data-matchnum` rows
- **60** `data-sp` attributes
- current play switch includes `playid=270`.

Conclusion:

> official Sporttery remains preferred, but **the project does have a currently reachable free mirror path** that can be used for a labelled feasibility smoke test and repeated observed-at snapshots.

Limitation:

- the mirror does not give the official provider update clock used by the official API;
- therefore it cannot, by itself, give exact official repricing timestamps;
- repeated polling can still observe quote states and bound change intervals.

---

## 5. Cloudflare Workers and paid fallback

Legacy route-C feasibility document:

`history/_review/02_顶层研究报告_md/信息差路线_框架_v1.md`

Recorded options:

| Route | Legacy judgment |
|---|---|
| domestic machine / domestic cloud | free/cheap but Pinnacle unreachable |
| foreign HK/SG/JP VPS | workable, paid |
| **Cloudflare Workers + Cron** | **~0 cost; foreign nodes; recommended lowest-cost route** |
| The Odds API | paid but easy; aggregates Pinnacle |

Cloudflare Worker was a **design recommendation**, not a verified implementation. Search of archived scripts found no Worker / Wrangler deployment code.

This route should therefore be classified:

`UNTESTED ZERO-COST ALTERNATIVE`

not:

`KNOWN WORKING`.

Also note that older route-C research later deprioritized deployment because the then-current economic thesis was judged weak. The new Edge Space review has narrowed/reopened B01/D01-B, so that old “do not deploy” decision does not automatically settle today's narrower data question.

---

## 6. Why TASK-0004's previous blocker verdict is incomplete

The submitted report stated that reachable free sources were only unsuitable soft/aggregate opening/closing sources.

That misses three material legacy facts:

1. football-data's BFE path had already been used as a sharp/exchange reference;
2. BetExplorer had already been cross-validated and accepted as a market proxy and supports observed-at fixture snapshots;
3. 500.com is a free currently reachable Sporttery mirror with prior official cross-validation.

Therefore “no acceptable source without new credentials/payment” was not established.

The direct-Pinnacle blocker is real.

The official-Sporttery-API blocker is real.

But:

> **direct endpoint failure != research data-source exhaustion.**

That is precisely a lesson already recorded in the legacy project.

---

## 7. Corrected feasibility hierarchy

### Tier A — test now, free

1. **Sporttery side:** 500.com mirror, explicit source flag and observed_at.
2. **Reference side:** BetExplorer current fixture odds, observed_at.
3. For European fixtures, also attempt football-data BFE whenever the feed contains current/future rows.

Goal:

- tiny dual-source smoke sample;
- no profitability claim;
- prove concurrent observation and mapping;
- quantify how much timestamp precision is lost relative to official/sharp direct feeds.

### Tier B — free but unproven

4. Cloudflare Worker foreign-node collector.

Only test if Tier A cannot answer the feasibility question and after a separate access/compliance decision.

### Tier C — paid / credentialled

5. The Odds API / licensed reference feed.
6. Betfair/Pinnacle credentialled APIs where legally and contractually available.

Paid sources are last, not first.

---

## 8. Research-control lesson

The failure mode is not merely “WorkBuddy missed a file”.

The Reviewer also accepted the report before reconstructing the prior data-source decision tree.

New control:

> Before declaring a data-source route BLOCKED or requiring payment, search the legacy asset register, existing collectors, prior source reconnaissance, and production fallback order for already-validated substitutes.

In this project specifically, consult at minimum:

- `资产登记册_v1.md`
- `侦察_外部数据源实测_20260902.md`
- `信息差路线_框架_v1.md`
- `模拟盘运行手册.md`
- legacy source collectors under `history/_review/05_脚本_scripts/scripts/`.

---

## 9. Corrected TASK-0004 disposition

Previous:

`ACCEPTED / BLOCKER VERIFIED`

Corrected:

`REJECTED — SOURCE EXHAUSTION NOT DEMONSTRATED`

Required revision:

- test the already-recorded free fallback hierarchy;
- attempt a tiny, honestly-labelled synchronized observation using reachable substitutes;
- only return BLOCKED after those paths are explicitly tested or shown inadequate for the exact B01/D01-B question.

