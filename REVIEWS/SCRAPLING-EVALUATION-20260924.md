# REVIEW — Scrapling reconnaissance and access-boundary ruling

- Review date: 2026-09-24
- Reviewer: ChatGPT
- Owner: Li
- Source report: `research/literature/SCRAPLING_EVALUATION_20260924_v1.md`
- Source commit: `22219ccccdeef28d896aa19162a993a52e0cd4db`
- Scope: independent of TASK-0004, except where the report supplied new data-quality evidence
- Decision: **DO NOT ADOPT SCRAPLING NOW / KEEP ACCESS REDLINES**

## 1. Executive decision

The Executor's central recommendation is accepted with one terminology correction:

> **Do not install or adopt Scrapling in the current project scope. Reuse the useful design ideas without taking the dependency. Keep the existing access-control and proxy/VPN redlines unchanged.**

This is a **current-scope adoption decision**, not a global technical rejection of Scrapling.

The report's evidence level is still `SCOUTED`. It explicitly did not perform a source-level audit of Scrapling. Under this project's own evidence taxonomy, that is insufficient for a final library-wide `REJECT` verdict.

The correct registry state is therefore:

`SCOUTED / NOT ADOPTED (CURRENT SCOPE)`

If a future task identifies a concrete need that Scrapling uniquely solves, the project may reopen it starting with a bounded PARTIAL AUDIT of the exact component needed.

## 2. Q1–Q6 rulings

| Question | Ruling | Reason |
|---|---|---|
| **Q1** — adopt §8 recommendation? | **YES, with wording correction** | Do not install/adopt Scrapling now. Absorb only dependency-free ideas: declarative parsing, polite adaptive backoff, fetch/parse separation. Existing `lxml` already reproduced the needed 500.com parsing behavior; anti-detection features do not solve the current timestamp-quality bottleneck. |
| **Q2** — append the two §5 defects as TASK-0004 errata? | **YES** | Both defects are material data-integrity facts. TASK-0004's current narrow correction already requires WorkBuddy to append them; do not create a competing edit while that task is in REJECTED/correction state. |
| **Q3** — make encoding integrity a hard data-policy rule? | **YES** | A page-declared charset is not evidence that the whole payload obeys one codec. Raw bytes, strict decoding, and validation of key fields must be mandatory. This review updates `docs/data-policy.md`. |
| **Q4** — is the 500.com explicit-decoding conclusion correct? | **YES — independently reproduced** | Reviewer reproduced the mixed-encoding failure and silent identifier corruption from the saved raw page; details below. |
| **Q5** — relax WAF / proxy-VPN redlines? | **NO** | The current blocker is missing provider-side timing on the reference source, not inability to reach a page. Anti-detection cannot create a timestamp the upstream never exposes. The paid proxy / enterprise bypass routes are also excluded by the Owner's “if it only works by paying, skip it” constraint. |
| **Q6** — add Scrapling to the GitHub scout? | **YES, but not as `SCOUTED / REJECT`** | Register as **SCOUTED / NOT ADOPTED (CURRENT SCOPE)**. `REJECT` would overstate the evidence because no source-level audit was performed. |

## 3. Independent verification of the two 500.com defects

Reviewer independently tested the saved raw file:

`data/raw/p0_dual_market_smoke/v3r4_mirror_500_today_091842.html`

Size: **114,505 bytes**.

### 3.1 Mixed encoding is real

Strict whole-document decode results:

- UTF-8: **FAIL at byte 61**
- GBK: **FAIL at byte 77,510**
- GB18030: **FAIL at byte 77,510**
- GB2312: **FAIL at byte 77,495**
- Latin-1: decodes mechanically, but does not provide meaningful Chinese text semantics

Reviewer also reproduced the silent-corruption case:

- `utf-8, errors='ignore'` -> first `data-matchnum` becomes **`003`**
- `gbk, errors='ignore'` -> the same bytes yield **`周三003`**

Therefore the Executor's warning is correct:

> **Using permissive decoding can silently destroy identity fields without raising an exception.**

The policy consequence is broader than 500.com: transport bytes must be preserved, decoding assumptions must be explicit, and permissive error suppression is not acceptable for identifiers, odds, timestamps, availability, or other research-critical fields.

### 3.2 Truncated match number is not unique

Reviewer independently extracted the current page's full match numbers:

`周三003, 周四001, 周四002, 周四003, ...`

The three-digit suffix `003` collides between:

- `周三003`
- `周四003`

Therefore the suffix alone is not a valid match key.

Reviewer also reproduced **1 hidden ended row** carrying `bet-tb-end`.

Consequences:

- preserve the full provider identifier;
- do not infer executability merely from presence in page HTML;
- hidden/ended rows must be distinguished from currently sellable rows.

## 4. Access-boundary ruling

### 4.1 Existing redlines remain in force

The following remain **not authorized** as ordinary project behavior:

- solving WAF / Cloudflare challenges to defeat access controls;
- browser/TLS fingerprint impersonation for the purpose of evading detection;
- proxy or IP rotation;
- VPN changes to obtain otherwise blocked content;
- paid residential/datacenter proxy pools;
- enterprise anti-bot bypass APIs;
- credential/account creation not explicitly authorized by Owner.

This ruling applies to Scrapling and to equivalent tools under other names.

### 4.2 What remains allowed

The following are ordinary, bounded collection techniques and are not treated as redline relaxation:

- normal HTTP headers required by a public endpoint, including the same-site Sporttery `Referer` already ruled acceptable;
- ordinary requests to publicly reachable unauthenticated endpoints/pages;
- inspection of public HTML / JavaScript / XHR to understand the page's own data flow;
- bounded browser rendering where a page genuinely requires rendering, provided it is not being used to solve/bypass an access-control challenge;
- polite rate limiting, exponential/adaptive backoff, caching, and retry;
- local parsing libraries such as `lxml`.

### 4.3 Why the redlines are not relaxed now

The report's core reasoning is correct:

- TASK-0004 already obtained the official Sporttery leg.
- BetExplorer is reachable.
- The unresolved D01-B issue is that the reference proxy does **not expose provider update time**.
- Anti-detection cannot manufacture an upstream timestamp without violating the project's no-invented-timestamp rule.

Therefore broader bypass capability has no demonstrated research value for the current P0 question.

The Owner constraint also excludes the main cases where such tooling usually adds meaningful access capacity:

> if the useful route requires paid proxy / bypass infrastructure, do not pursue it.

### 4.4 Future exception standard

No blanket relaxation is granted.

If a future research route depends on one uniquely valuable public source that cannot be obtained through compliant access methods, a **source-specific exception proposal** may be reviewed separately. It must state:

- exact source and research question;
- why existing alternatives are insufficient;
- what access mechanism is proposed;
- whether it costs money;
- ToS / legal / reproducibility implications;
- the minimum requested exception.

Until such a review is accepted, the current redlines remain binding.

## 5. Scrapling component decision

| Component / idea | Current decision |
|---|---|
| `Selector`-style declarative parsing | **ADOPT THE PATTERN, not the dependency**; use existing `lxml` where sufficient |
| AutoThrottle / adaptive politeness | **ADOPT THE PATTERN** |
| fetch / parse separation | **ADOPT THE PATTERN**; already aligned with project architecture |
| XHR inspection | **ALLOWED as a technique** within normal public access |
| ordinary browser rendering | **Allowed only when genuinely required**, not for challenge solving |
| `Fetcher(impersonate=...)` | **NOT AUTHORIZED** |
| `StealthyFetcher(solve_cloudflare=True)` | **NOT AUTHORIZED** |
| `ProxyRotator` | **NOT AUTHORIZED** |
| installing Scrapling now | **NO** |
| source-level Scrapling audit now | **NO NEED**; reopen only on a concrete future use case |

## 6. Data-policy consequence

The 500.com evidence establishes a new hard ingestion rule:

> **Raw transport bytes are authoritative. Charset declarations are hypotheses to validate, not facts to trust.**

For research-critical fields:

- never use permissive decode behavior such as `errors='ignore'` or `errors='replace'` as the canonical parse path;
- if a document is mixed-encoding, segment/parse deterministically or extract the required byte regions with explicit encoding rules;
- retain the raw-byte hash;
- test representative raw fixtures;
- fail closed when identifiers/odds/timestamps cannot be decoded unambiguously.

Provider identifiers must also be preserved in full unless uniqueness of a transformed key is formally demonstrated.

This review updates `docs/data-policy.md` accordingly.

## 7. Registry consequence

Scrapling will be added to:

`research/literature/GITHUB_OPEN_SOURCE_SCOUT_20260922_v3_0.md`

with:

- evidence level: **SCOUTED**
- project decision: **NOT ADOPTED (CURRENT SCOPE)**
- useful ideas: declarative selector, adaptive backoff, fetch/parse separation
- reason: unnecessary dependency for current parsing; anti-detection features conflict with existing boundaries and do not solve the current information-quality bottleneck
- reopen condition: a concrete source that materially benefits from a specific Scrapling component, followed by component-level PARTIAL AUDIT

## 8. Final gate

- Q1: **YES**
- Q2: **YES**
- Q3: **YES**
- Q4: **YES / independently reproduced**
- Q5: **NO — redlines stay**
- Q6: **YES, as SCOUTED / NOT ADOPTED (CURRENT SCOPE)**

`SCRAPLING = SCOUTED / NOT ADOPTED NOW / REDLINES UNCHANGED`
