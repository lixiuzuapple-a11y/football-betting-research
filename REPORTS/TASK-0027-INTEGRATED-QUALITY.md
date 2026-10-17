# TASK-0027 — Integrated corpus-quality research work package

## Purpose / scope
One coherent research phase after TASK-0026, **not** separate micro-tasks: derive a reproducible 169-match fixture coverage and odds-state replay diagnosis, then identify what can legitimately proceed to verified results and forward EV research.

### Frozen source evidence
TASK0024 + TASK0025 immutable cloud archives previously audited: 9522 capture rows, 9519 saved gzip responses with 0 known corrupt, 82+87=169 disjoint matchIds, both SQLite integrity good. TASK0025 ended normally at 3120 rounds. These are **previously independently observed**, not newly recomputed in this phase.

### Reused assets
- `tools/task0020_replay_audit.py` old (different capture schema), evidences prior-payload reversion methodology.
- `tools/task0022_result_join.py` existing strict fixture identity matching; does **not** infer scores or claim real outcome completion.
- `tools/task0017_official_only.py` reader contract.

### New reusable read-only diagnostic
- `tools/task0027_corpus_quality.py` accepts repeated `--root` arguments for collector roots and `--out` to write a reproducible JSON report; checks SQLite integrity, each captured gzip SHA256, count/coverage per match ID, observation duration distributions, per-market raw state transitions and nonconsecutive returns to earlier seen state; explicitly marks 0 verified results.
- `tests/test_task0027_corpus_quality.py` covers synthetic 1.9 -> 2.0 -> 1.9 reversion and transport row without raw, and rejects mismatched SHA.
- Local full test suite `289 passed` (2026-10-17).
- Invocation once cloud SSH connectivity is restored:
```bash
python3 tools/task0027_corpus_quality.py \
 --root /home/ubuntu/evlab-data/task0024-official-20261010 \
 --root /home/ubuntu/evlab-data/task0025-official-20261015 \
 --out /home/ubuntu/evlab-data/task0027-corpus-quality.json
```
The command is read-only against original raw and DB. Output is outside both frozen roots.

### Material blocker
During this session WebCodex local workspace worked, but `evlab-cloud` SSH calls timed out even for `date -u`. Thus the tool has **not** run on the full 169-match corpus in this task, and no new full-corpus coverage, replay, or match outcomes are claimed. Do not promote earlier exploratory 6022 field transitions to validated effective odds changes.

### Scientific phase gate
- **Engineering diagnostic implementation ACCEPT** on local tests.
- **Empirical corpus coverage statistics PENDING** because live cloud SSH unavailable; no substitute invented.
- **Real price updates PENDING**: replay-reversion counts are a screening metric, not enough to identify monotonic bookmaker timestamps or executable sporttery quotes.
- **Score join PENDING**: strict official match ID/identity/time, verifiable result origin and independent review required; no claims of predictive edge or ROI.
- Prefer single next integrated activity after SSH restoration: execute frozen corpus audit, investigate provider timestamps and actual quote subfields, obtain legitimate outcome mapping, then write quantitative findings and STOP/GO decision. Do not begin collecting more before data quality gate.
