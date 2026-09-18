# Data Policy

Rules for what data may enter this project, and under what conditions.

The shortest version: **if a dataset cannot say where it came from, when it was
true and when we got it, it does not enter the project - no matter how
interesting it looks.**

---

## 1. Provenance is mandatory

Every dataset used in a formal experiment is stamped with:

| Field | Meaning | Example |
|---|---|---|
| `source` | Where the rows came from | `https://example.com/api/fixtures` or a file hash |
| `collected_at` | When we pulled and finalised this version | `2026-09-18T09:00:00Z` |
| `data_time_start` / `data_time_end` | The instants the rows describe | `2026-09-18T00:00:00Z` .. `2026-09-18T09:00:00Z` |
| `version` | Our immutable label | `2026-09-18.1` |
| `schema` | The payload contract version | `core-0.0.1` |

Enforced in `data/provenance.py`:

- all three timestamps must be timezone-aware;
- `data_time_end >= data_time_start`;
- **`data_time_end <= collected_at`** - a dataset cannot describe a moment that
  had not happened when it was collected;
- every row's `data_time` must fall inside the window the snapshot claims to
  cover.

## 2. Two rules for time

Every row carries two clocks, and conflating them is the most common way a
backtest lies to you:

- **`data_time`** - when the fact was true.
- **`collected_at`** - when it reached us.

A quote counts as known at instant *t* only if **both** are at or before *t*. A
feed that delivers a five-minute-old price does not license the claim that we
knew it five minutes earlier.

Worked example, from the test suite:

| quote | data_time | collected_at | knowable at 12:00? |
|---|---|---|---|
| `odds-known` | 08:00 | 09:00 | yes |
| `odds-not-yet-arrived` | 08:00 | 12:30 | **no** - still in transit |

Same upstream moment, same price, different answer, because one of them had not
reached us.

## 3. Phase labels

Every row is labelled `pre-match`, `live` or `post-match` relative to the
fixture's kickoff.

| Phase | May enter a pre-match feature vector? |
|---|---|
| `pre-match` | Yes, if it passes the two-clocks test |
| `live` | No |
| `post-match` | **Never** |

The rule is enforced by type, not by convention: `MatchResult.phase` is always
`POST_MATCH`, and `features.validate_observations()` refuses any object whose
phase is `POST_MATCH` before anything else happens.

## 4. The bar a source must clear

Before a new source is wired into `data.loader`, it must have:

1. **A stable identifier.** A URL, an endpoint, a documented file, or a hash.
2. **A licence permitting research use.** Including redistribution limits if the
   rows are ever published.
3. **Documented semantics per field**, including units and time zone.
4. **A schema version**, so a later reader can parse an old snapshot.
5. **A stated freshness contract** - expected latency from event to availability.
   This determines what `collected_at` means in practice.
6. **A stated density.** How many fixtures are missing, and why. A source that
   silently omits lower-league fixtures creates survivorship bias.
7. **A tamper check.** A row count and a content hash, so a snapshot can be shown
   to be the one that was used.

A source missing any of 1-5 is not usable for a formal experiment.

## 5. Absence of a source is not a data set

There is currently no source. That is not an inconvenience to be papered over:

```
available_sources() -> ()
load_snapshot(...)  -> raises NotImplementedYetError
```

A pipeline that fabricates or samples its own inputs cannot be used to evaluate
anything, because there is no way to know whether a result reflects the world or
the generator.

**Never generate sample data and let it pass for real data.** If a shape is
needed for a test, it lives in `tests/` as a fixture, clearly synthetic, and
never reaches `data/`.

## 6. Storage in this repository

Raw and derived datasets are **not** versioned here. `.gitignore` excludes
`data/*` and `results/*` while keeping the directory placeholders and their
READMEs.

Rationale: datasets are large, frequently re-licensed, and best stored with a
content hash rather than in git history. What belongs in the repository is the
**recipe** - the snapshot's provenance record - plus the code that validates it.

Each snapshot should be recorded with enough information for a third party to
re-fetch or verify it:

```
source URL or hash | version | collected_at | data_time window | row count | schema
```

## 7. Odds data: specific cautions

Odds are the most leak-prone data in this project. Each of the following has
invalidated a real backtest somewhere:

1. **Closing line leakage.** The closing price contains information from after
   the point a bet had to be placed. It is a legitimate *evaluation* input (to
   measure closing-line value) and an illegitimate *decision* input.
2. **Timestamp drift.** A book's "last updated" field may be a cache timestamp,
   not the moment the price changed. Establish which one before using it.
3. **Silent revision.** Some feeds overwrite history. Capture an append-only
   series of snapshots rather than querying "current" prices retrospectively.
4. **Survivor books.** A book that no longer exists may have offered unbeatably
   generous prices that were never actually available in size.
5. **Margin changes.** The overround moves over time; a value strategy calibrated
   on one era's margin is not calibrated on another.

Store raw, unmodified captures. Any cleaning is a separate, versioned, documented
step that produces a new artefact - never an in-place edit of a capture.

## 8. What is never done

- Editing a capture in place. A correction is a new snapshot with a new version.
- Filling missing values silently. Missing is missing; imputation is a modelling
  decision that must be recorded, and it happens in `features`, not `data`.
- Mixing sources into one snapshot without per-row provenance. If two sources
  are combined, the combination is itself a snapshot with its own record and the
  row-level origins preserved.
- Backfilling. A snapshot's `collected_at` is when we actually collected it; a
  later pull is a new snapshot, not a correction to an old one's timestamp.

## 9. Retention

Nothing is deleted. Failed pulls, rejected sources and superseded snapshots are
retained with a status, because "we tried this source and it was unusable" is a
result worth keeping.
