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

Empty. No hypothesis has been raised yet, because stage 1 builds the machinery
that will test them. Prior football research from earlier projects is **not**
imported here as a premise - it may later be added as an explicitly-labelled
prior, in its own file, with its provenance.
