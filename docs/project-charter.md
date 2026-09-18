# Project Charter

This document is the constitution of the project. Where code and this document
disagree, one of them is a bug, and the disagreement must be resolved rather
than tolerated.

---

## 1. What the project is

A **Football Betting Recommendation & Research System**: a reproducible,
auditable, extensible pipeline for pre-match analysis, odds value assessment,
recommendation logging, post-match evaluation and historical backtesting.

The system's job is to be **wrong in measurable ways**. A research pipeline that
cannot be falsified is entertainment.

## 2. What the project is not

- Not an automatic betting system.
- Not a tipster service.
- Not a prediction product. Predictions are intermediate artefacts.
- Not a continuation of any earlier football project. Prior work may later be
  imported as an explicitly-labelled prior, but it is **not** an architectural
  premise here.

## 3. Roles

| Role | Responsibility |
|---|---|
| Project owner | Sets direction, defines research questions, accepts or rejects results |
| Executing engineer | Implements, tests, reports; does not redesign the project |
| Reviewer | Challenges methods and conclusions before they are accepted |

No result is accepted on the authority of the party that produced it.

---

## 4. Separation of the four concepts

These four things must never collapse into one module, one function or one word:

```
Prediction          a probability triple from a named model version
Recommendation      a recorded opinion, at a moment, about a specific price
Betting Decision    whether a human chooses to act on that opinion
Actual Execution    money moving
```

Current state, stated plainly:

- `Prediction` and `Recommendation` are implemented.
- `Betting Decision` is a human action and is deliberately absent from the code.
- `Actual Execution` **is not implemented, and stage 1 must not implement it.**

A `Recommendation` carrying `BUY` is a row. It is not a command, and no module in
this package consumes it as one. A test enforces this: no execution module, no
execution callable, no wagering endpoint.

---

## 5. Time discipline

### 5.1 Phase separation

Every piece of information exists in exactly one of three phases:

```
pre-match   knowable strictly before kickoff
live        knowable between kickoff and the final whistle
post-match  knowable only once the match has finished
```

**Post-match information may never enter a pre-match artefact.** The feature
layer rejects post-match objects by type; `MatchResult.phase` is always
`POST_MATCH`, and anything whose `phase` is `POST_MATCH` is refused as an input.

### 5.2 Two clocks, not one

Every observation carries two times, and confusing them is the most common way a
backtest lies to you:

- **`data_time`** - the instant the observation describes.
- **`collected_at`** - the instant we received it.

A feed that hands us a five-minute-old price does not license the claim that we
knew that price five minutes earlier. Both clocks must be at or before the
decision instant.

### 5.3 The `as_of` cutoff

Artefacts that embody a judgement (`Prediction`, `Recommendation`) carry an
`as_of`: the information cutoff used. Every dependency must satisfy
`as_of <= created_at`. This is what makes the question

> What did this prediction actually know?

answerable, rather than a matter of recollection.

### 5.4 Naive datetimes are never acceptable

Every timestamp is timezone-aware. A naive timestamp cannot be compared across
sources, and a silent comparison error is a look-ahead leak with no error
message.

---

## 6. Data provenance

Any data used in a formal experiment must be traceable on five axes:

| Field | Meaning |
|---|---|
| `source` | Where the rows came from: URL, endpoint, file hash |
| `collection_time` | When we pulled it |
| `data_time` | The instant(s) the rows describe |
| `version` | Our immutable label for that snapshot |
| `schema` | The contract version the payload conforms to |

A dataset that cannot answer all five is not usable for research, however
interesting it looks. See [`data-policy.md`](data-policy.md).

---

## 7. Experiments

Every formal experiment carries:

```
experiment_id
hypothesis
data_version
model_version
parameters
result
status
```

Rules:

1. **Pre-register.** The hypothesis and parameters are recorded before the run.
   A test invented after seeing the number is not a test.
2. **Failures are retained.** `FAILED` is a terminal state that stays in the
   registry forever. There is no delete path, by construction.
3. **Results are frozen.** Once an experiment has a result, it cannot be
   re-resolved. A correction is a new experiment.
4. **Report the sample.** Every metric travels with its sample size, its data
   version and its model version. An ROI without a sample size is a rumour.

See [`experiment-protocol.md`](experiment-protocol.md).

---

## 8. No leakage

The following failure modes are treated as project-threatening, because each one
produces results that look good and are meaningless:

| Failure mode | Example |
|---|---|
| Future information | Using a closing line to predict a match that already kicked off |
| Look-ahead bias | A rolling statistic computed with a centred window |
| Selection bias | Backtesting only the fixtures that were easy to source |
| Survivorship bias | Testing on leagues that still exist today |
| Leakage through labels | A feature derived from the scoreline |
| Leakage through odds | Using a price that was only available after kickoff |
| Post-match leakage | Team news, injuries or line-ups filed after the whistle |

Mitigations in code:

- post-match objects rejected by type at the feature boundary;
- two-clock time checks on every observation;
- `as_of <= created_at` on every judgement artefact;
- `RecordStore.state_as_of()` reconstructs the world from what had actually been
  recorded, not from what we know now;
- `walk_forward_windows()` cannot produce a window that trains on its own test
  period, and supports an explicit embargo gap.

---

## 9. Honesty rules

1. **Never fabricate data.** No sample rows, no synthetic fixtures presented as
   real, no interpolated values passed off as observations.
2. **Never fabricate completion.** Unimplemented behaviour raises
   `NotImplementedYetError`. A stub must never return a plausible value.
3. **Never let a plausible default stand in for a decision.** An empty feature
   vector, a uniform forecast or an empty backtest result is worse than an
   exception, because it looks like work.
4. **Report what failed.** A missing result is reported as missing.
5. **Distinguish fact, inference and unknown** in every written conclusion.

---

## 10. Security and credentials

Nothing from this list may ever enter version control:

```
.env  *.pem  *.key  credentials.*  token.*  cookies.*  secrets.*
```

plus any GitHub token, API key, session cookie, password or personal
authentication data. `.gitignore` blocks the common shapes. If a secret is ever
found in the working tree, **stop and report before committing** - history is
very hard to un-write.

---

## 11. Change control

- Architectural change is a decision, not a side effect of a bug fix.
- Every substantive change lands as a commit with a message that explains the
  why, not just the what.
- This charter is amended deliberately and visibly, never by drift.
