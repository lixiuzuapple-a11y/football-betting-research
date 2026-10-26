# EV-Lab Phase 2: bounded cloud forward capture + executable prediction freeze

Date: 2026-10-26 (+08:00). The two tracks have **different** acceptance levels.

## Track A: real cloud bounded qualification

The cloud runner is `evlab-cloud`, source script `/home/ubuntu/task0024_collector.py`. Its sha256 is
`a3ae6db246ba2cd52cdfc3798efe66462fc27d13fb11a8d5345572c4144b162a`, matched locally against the fixed Git source `eb1099a799d86d16d9ca625501641a264d1c2f91:tools/task0017_official_only.py`.

New data root only (all prior roots left untouched):
`/home/ubuntu/evlab-data/phase2-official-20261026`

The Linux systemd transient service (started 2026-10-26 14:08 CST):
- `evlab-phase2-official-20261026.service` running as unprivileged `ubuntu`.
- Official fixed Sporttery URL only, 60-second cadence, 20-second HTTP timeout.
- `--max-rounds 2880 --max-hours 49 --max-bad 3`.
- `RuntimeMaxSec=176400` (49 hours), `MemoryMax=350M`, `Restart=no`.
- Persists append-only SQLite `official.sqlite3` and compressed immutable raw payloads by SHA256; remains **research-only**, not official machine trading.
- `evlab-phase2-health-20261026.timer`: independent 2-minute polling of status, SQLite quick_check, capture age and disk space; appends `health.jsonl`.
- `evlab-phase2-health-stop-20261026.timer`: one-shot stop for health timer after 50 hours.
- Transient units are *not boot-persistent*. A VM reboot or fault may interrupt the task: a deliberate controlled qualification limit, **not** a qualified always-on production service.

Observed initial conditions: first capture 2026-10-26 06:08:42 UTC, HTTP200, 4 fixtures, source hash `59a70aff5050426b94d69270907f2b9253268f6b9c54ec04e7a0dfac538380ae`. First manual monitor returned OK. By 06:18 UTC, 10 captures were present; monitored 2-minute events consistently OK, SQLite quick_check=ok, roughly 40GB free disk.

No automated chat alert, guaranteed service recovery, or completed 48h stability claim. Those require observation after the full bounded window.

Read-only verification:
```bash
ssh evlab-cloud 'systemctl show evlab-phase2-official-20261026.service -p ActiveState -p Result -p ExecMainStatus'
ssh evlab-cloud 'systemctl list-timers --all --no-pager | grep evlab-phase2'
ssh evlab-cloud 'tail -n 5 /home/ubuntu/evlab-data/phase2-official-20261026/health.jsonl'
```

## Track B: actual future 1X2 probability freeze

An explicit *weak independent baseline* is in `src/football_betting/models/observed_frequency.py`. It reads historical verified score categories **only**, Dirichlet(1,1,1) smoothing. No bookmaker price is available to the predictor. All market odds are handled downstream and are not passed into the training or prediction interface.

Generic `available_predictors()` application registry and feature builder are still NOT wired to an ongoing model-production process. The baseline is an explicit research CLI:

```powershell
python -m tools.phase2_forecast_lab freeze --historical-labels "E:\WebCodex-Workspace\EVLab-Data-Backups\official-20261018\TASK0030-RESULT-EVIDENCE\VERIFIED_SCORE_CANDIDATES.json" --quote-manifest "E:\WebCodex-Workspace\EVLab-Data-Backups\task0040-new-official-window-20261026\sporttery-20261026T034944Z.json.manifest.json" --out "E:\WebCodex-Workspace\EVLab-Data-Backups\phase2-forward-lab-20261026\PHASE2-FIRST-FORWARD-FREEZE.json"
```

This command was run with real source files on 2026-10-26 14:16:58 CST, before all four listed kickoffs on October 27. The file is **create-only** (cannot overwrite). Official training labels totaled 135 (home 64/draw 31/away 40), latest training date October 18. All 4 fixtures got the independent [0.47101449, 0.23188406, 0.29710145] base-rate forecast; 2/4 also qualified for strict HAD market **reference**, not executable prices. Forecasts are deliberately not team-specific, not calibrated for future performance and not a BUY.

Frozen full file SHA256:
`53abdeb13121974512ead40340fbd68df96a5082ab8fde210b84bf3588b40f86`.
Training labels SHA256:
`6da5c08d4b1a77f531506c67052fdd46cc002e8562283b02ca7d85a1b64c1a40`.
Source raw SHA256:
`4079741dcbd9f9dd7ef65bd241da9f0592988b2bdb33e62aee0cb04857331457`.
Manifest SHA256:
`839d29b970d216b26125e56d91fa8e45cfa06ba138a4d2904a55ac22c7343d2d`.

Important limitation: the market reference was received 2026-10-26 11:49 CST, earlier than the frozen 14:16 forecast. This is **not** a synchronized actionable quote, nor a fair proof of instantaneous market arbitrage. The official raw data shows a 50-hour-old provider update for one HAD fixture.

Future scoring will use `python -m tools.phase2_forecast_lab score --frozen <immutable-file> --official-results <new-official-result-evidence.json> --out <new-result-file>`, only when verified final outcomes become available and after kickoff, with strict fixture/score status checks. It is an **on-demand scoring CLI**, not yet a deployed automatic result-fetching/evaluation scheduler.

## Safety and acceptance line

- Cloud: startup+repeated-health observation **ACCEPT**; 48h qualification **PENDING**.
- Forecast: four actual new future fixtures **FROZEN BEFORE KICKOFF**, source/label/commit provenance pinned; independent predictor **only a weak benchmark**.
- Automatic multi-model prediction and bookmaker-aligned CLV: **NOT IMPLEMENTED**.
- Model edge, profitable EV, staking, BUY and execution: **NO-GO**.
