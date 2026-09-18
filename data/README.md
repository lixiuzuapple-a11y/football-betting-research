# data/

Working directory for datasets. **Currently empty.**

Nothing here is versioned. `.gitignore` excludes everything except this file and
`.gitkeep`, because datasets are large, frequently re-licensed, and better stored
with a content hash than in git history. Read
[`../docs/data-policy.md`](../docs/data-policy.md) before putting anything here.

## What belongs here

Only captures that satisfy the provenance bar in the data policy:

| Field | Meaning |
|---|---|
| `source` | URL, endpoint, or file hash |
| `collected_at` | When we pulled it |
| `data_time_start` / `data_time_end` | The instants the rows describe |
| `version` | Immutable snapshot label |
| `schema` | Payload contract version |

A file dropped here without that record is not usable for a formal experiment,
however good it looks.

## Layout convention

```
data/
├── raw/          immutable captures, never edited in place
├── interim/      intermediate transformations, reproducible from raw
└── processed/    research-ready datasets, each with a provenance record
```

Subdirectories are created when the first real capture lands, not in advance.

## Rules

1. **Never edit a capture in place.** A correction is a new version.
2. **Never fill missing values here.** Missing is missing; imputation is a
   modelling decision and belongs in `features/`, recorded as such.
3. **Never fabricate.** No sample rows, no synthetic fixtures, no interpolated
   stands-ins. If a shape is needed for a test, it lives in `tests/`.
4. **Never commit a credential.** Not in a filename, not in a header column, not
   in a comment.

## Status

`data.loader.available_sources()` returns an empty tuple. No source is
configured, and `load_snapshot()` raises `NotImplementedYetError`. That is the
honest state of the project, not a gap to be plugged with generated rows.
