# TASK-0013 — A07 information-coverage proxy feasibility gate
- Status: ACCEPTED
- Date: 2026-10-09
- Owner Li; Executor/Reviewer ChatGPT.
- New mechanism: A07 ex-ante information coverage. Distinct from TASK-0011/12 A04 rest.
- Explicit exploratory historical feasibility gate, **not** betting/alpha validation.
## Frozen plan before analysis
Use existing hist_v2.csv, preserve SHA. Candidate coverage proxy = archived `src` category (fd_std versus fd_extra); this is provider/ingestion pathway, not established real-world information availability and must not be called that without evidence.
Test predeclared **data-identification gate**: source label must have a provider-documented, date-effective meaning corresponding to information coverage; outcome and closing odds must not be used to construct it. Assess source-group size, historical opening `PSH/PSD/PSA` availability and closing `PSCH/PSCD/PSCA` availability. Only if external semantics are established can this be considered a meaningful A07 treatment proxy. To prevent fishing, no outcome-based calibration comparisons or ROI until proxy semantics pass; report gate FAIL/BLOCKED honestly.
Execution: independently recompute basic counts and cross-tab with separate implementations, confirm preservation of source/original row count, run tests; findings versioned under research/task0013 plus report/review. No downloading, no paid source, no service alteration.
- Do not claim `fd_extra` objectively means lower information coverage merely from its label.
