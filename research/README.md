# research/

Research material that is not code: what we intend to test, how a test is set
up, and what is already known.

```
research/
├── hypotheses/    falsifiable statements, written before the test
├── experiments/   experiment records and their parameter files
└── literature/    sourced material, with provenance and a stated relevance
```

## `hypotheses/`

One file per hypothesis, named `<slug>.md`:

```markdown
# <hypothesis in one sentence>

- Status: proposed | under test | supported | refuted | abandoned
- Raised: <date>
- Refuted by: <what result would kill this>

## Statement
A falsifiable claim. If it cannot lose, it does not belong here.

## Mechanism
Why should this effect exist? Written before the test, not after.

## Test design
Data version, model version, decision rule, metric, minimum sample size.
```

The mechanism section is the one most often skipped and the one that matters
most: a pattern in historical odds is easy to find retrospectively, and usually
means the data was assembled with hindsight.

## `experiments/`

Parameter files and records for pre-registered experiments, keyed by
`experiment_id`. The authoritative registry is
`records.ExperimentRegistry`; these files are the human-readable counterpart.

An experiment file is created **before** the run. See
[`../docs/experiment-protocol.md`](../docs/experiment-protocol.md).

## `literature/`

Sourced material - papers, articles, datasets - each with:

- where it came from and when it was retrieved;
- what claim it is being cited for;
- what it does **not** support.

A citation without a stated relevance is a bookmark, not research.

## Rules

1. **Pre-register.** Write the hypothesis and the design down before running.
2. **Keep refuted hypotheses.** A refuted hypothesis is a result; deleting it
   invites someone to raise it again next month.
3. **Separate exploration from confirmation.** If the design changed after seeing
   results, relabel it as exploration.
4. **No fabricated references.** If it cannot be found, it is not cited.

## Status

The hypothesis/experiment registries remain empty: no new confirmatory
hypothesis has been raised yet.

Legacy football work is now available as **evidence to audit**, not as a
premise to inherit. The reviewer records are:

- [External-AI Edge Space synthesis](literature/EDGE_SPACE_PANEL_SYNTHESIS_20260922_v1.md)
- [Open-source and theory reconnaissance v3.0](literature/GITHUB_OPEN_SOURCE_SCOUT_20260922_v3_0.md)
- [Legacy evidence ingestion record](LEGACY_EVIDENCE_INGESTION_20260923.md)
- [Edge Exhaustion Matrix v1](EDGE_EXHAUSTION_MATRIX_20260923_v1.md)
- [P0 evidence reconstruction](P0_EVIDENCE_RECONSTRUCTION_20260923.md)
- [Legacy data-source alternatives reconstruction](DATA_SOURCE_ALTERNATIVES_RECONSTRUCTION_20260923.md)

The source legacy bundles live under `../history/`. Bulk archives and local
review extracts are intentionally ignored by Git; only provenance/index files
and reviewer conclusions belong in repository history.
