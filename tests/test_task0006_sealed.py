"""TASK-0006 regression tests: sealed-run pre-flight requirements (§17).

Covers the twelve behaviours TASK-0006 §17 requires, plus the §5.2 manifest
contract. Everything is offline: the collector's HTTP legs are replaced by
scripted responses, so these tests never touch the network.

The sealed phase is the point. A sealed run is only worth anything if the
*operations* cannot quietly become research: the phase must be stamped
everywhere, the deadline must not slide on restart, the baseline must survive a
restart, and the logs must not leak a result. Those are the things asserted here.

Indices below refer to the numbered list in TASK-0006 §17.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import asdict
from pathlib import Path

import pytest

from football_betting.data.betexplorer import variant_key_from_label
from football_betting.prospective.__main__ import _resolve_sealed_deadline, build_parser
from football_betting.prospective.collector import (
    CollectorConfig,
    LegOutcome,
    ProspectiveCollector,
)
from football_betting.prospective.ledger import (
    CAPTURE_KIND_CHANGE_CONFIRMATION,
    CAPTURE_KIND_REGULAR,
    DATASET_PHASE,
    PHASE_PROSPECTIVE_SEALED,
    SCHEMA_VERSION,
    SOURCE_OFFICIAL_SPORTTERY,
    SOURCE_REFERENCE_BETEXPLORER,
    CaptureRecord,
    LedgerStore,
    schema_hash,
)
from football_betting.prospective.manifest import (
    SEALED_DURATION_HOURS,
    ManifestError,
    build_manifest,
    read_manifest,
    write_manifest,
)

UTC = dt.timezone.utc
SEALED = PHASE_PROSPECTIVE_SEALED
VARIANT_LABEL = "geo=cn|serial=2609081259"

# --------------------------------------------------------------------------
# Fixtures: real-shaped payloads, scripted transport
# --------------------------------------------------------------------------


def _be_row(
    event_id: str,
    *,
    dt_raw: str,
    ts: str,
    odds: tuple[str, ...],
    home: str = "Home FC",
    away: str = "Away FC",
    cls_suffix: str = "tournamentLiContentMobile",
) -> str:
    odd_parts = "".join(
        f'<div class="table-main__odds"><p data-odd="{value}"></p></div>' for value in odds
    )
    return (
        f'<li class="showHide table-main__tournamentLiContent {cls_suffix}" '
        f'data-tid="371" data-ts="{ts}" data-event-id="{event_id}">\n'
        f'<ul class="table-main__matchInfo" data-live="{event_id}" data-dt="{dt_raw}">\n'
        f'<li class="table-main__participants">'
        f'<a href="/football/eng/england/{event_id}/">'
        f'<div class="table-main__participantHome"><p class="x">{home}</p></div>'
        f'<div class="table-main__participantAway"><p class="x">{away}</p></div>'
        f"</a></li>\n"
        f'<li class="table-main__oddsLi"><div class="table-main__oddsLi oddsColumn">'
        f"{odd_parts}</div></li>\n"
        f"</ul></li>\n"
    )


def _be_page(rows: list[str], *, geo: str | None = None, serial: str | None = None) -> str:
    head = ""
    if geo is not None:
        head += f"<script>const currentGeoLocation = '{geo}';</script>"
    if serial is not None:
        head += f'<link rel="stylesheet" href="/res/betexplorer.svg?serial={serial}">'
    return "<html><head>" + head + "</head><body><ul>" + "".join(rows) + "</ul></body></html>"


def _sporttery_payload(*, had: tuple[str, str, str]) -> str:
    return json.dumps(
        {
            "errorCode": "0",
            "success": True,
            "value": {
                "totalCount": 1,
                "lastUpdateTime": "2026-09-23 21:50:41",
                "matchInfoList": [
                    {
                        "businessDate": "2026-09-25",
                        "matchWeek": "周五",
                        "subMatchList": [
                            {
                                "matchId": 2041648,
                                "matchNumStr": "周五006",
                                "leagueAbbName": "欧国联",
                                "homeTeamAbbName": "荷兰",
                                "awayTeamAbbName": "德国",
                                "matchDate": "2026-09-26",
                                "matchTime": "02:45:00",
                                "matchStatus": "Selling",
                                "had": {
                                    "h": had[0], "d": had[1], "a": had[2],
                                    "updateDate": "2026-09-23", "updateTime": "18:51:22",
                                },
                                "poolList": [
                                    {
                                        "poolCode": "HAD",
                                        "bettingSingle": 0,
                                        "bettingAllup": 1,
                                        "poolStatus": "Selling",
                                        "poolCloseDate": "2026-09-26",
                                        "poolCloseTime": "02:40:00",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        },
        ensure_ascii=False,
    )


def _outcome(
    source: str,
    *,
    text: str,
    started: dt.datetime,
    received: dt.datetime,
    status: int = 200,
    failure: str | None = None,
) -> LegOutcome:
    raw = text.encode("utf-8")
    return LegOutcome(
        source=source,
        request_started_at=started,
        response_received_at=received,
        latency_ms=(received - started).total_seconds() * 1000.0,
        http_status=status,
        failure_class=failure,
        raw=raw,
        text=text,
    )


def _patch_legs(
    collector: ProspectiveCollector,
    *,
    sporttery_bodies: list[str],
    betexplorer_bodies: list[str],
    base: dt.datetime,
) -> dict[str, int]:
    calls = {"sporttery": 0, "betexplorer": 0}

    def fake_fetch(source: str, request: object) -> LegOutcome:
        if source == SOURCE_OFFICIAL_SPORTTERY:
            index = min(calls["sporttery"], len(sporttery_bodies) - 1)
            calls["sporttery"] += 1
            return _outcome(
                source,
                text=sporttery_bodies[index],
                started=base + dt.timedelta(seconds=calls["sporttery"]),
                received=base + dt.timedelta(seconds=calls["sporttery"], milliseconds=500),
            )
        index = min(calls["betexplorer"], len(betexplorer_bodies) - 1)
        calls["betexplorer"] += 1
        return _outcome(
            source,
            text=betexplorer_bodies[index],
            started=base + dt.timedelta(seconds=calls["betexplorer"]),
            received=base + dt.timedelta(seconds=calls["betexplorer"], milliseconds=700),
        )

    collector._fetch = fake_fetch  # type: ignore[method-assign]
    return calls


BASE = dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC)


def _sealed_collector(store: LedgerStore) -> ProspectiveCollector:
    return ProspectiveCollector(
        CollectorConfig(
            data_root=str(store.data_root),
            dataset_phase=SEALED,
        ),
        store=store,
    )


@pytest.fixture()
def sealed_store(tmp_path: Path):
    with LedgerStore(
        tmp_path / "data", deployed_commit="sealed-commit", dataset_phase=SEALED
    ) as handle:
        yield handle


# ==========================================================================
# §17.1 - the phase is persisted on every formal table
# ==========================================================================


def test_sealed_phase_is_persisted_across_all_formal_tables(sealed_store: LedgerStore) -> None:
    collector = _sealed_collector(sealed_store)
    page = _be_page(
        [_be_row("s001", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("2.15", "3.45", "3.65"))],
        geo="cn", serial="2609081259",
    )
    _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[page, page],
        base=BASE,
    )
    collector.run_round()
    collector.run_round()

    for table in ("captures", "sporttery_facts", "betexplorer_facts"):
        rows = sealed_store._conn.execute(
            f"SELECT DISTINCT dataset_phase AS p FROM {table}"
        ).fetchall()
        assert [row["p"] for row in rows] == [SEALED], table


# ==========================================================================
# §17.2 - qualification stays the default and the legacy behaviour
# ==========================================================================


def test_qualification_remains_the_default_phase() -> None:
    assert DATASET_PHASE == "QUALIFICATION"
    assert CollectorConfig(data_root="/tmp/ignored").dataset_phase == DATASET_PHASE
    assert CollectorConfig(data_root="/tmp/ignored").planned_end_utc is None


def test_qualification_rows_are_still_labelled_qualification(tmp_path: Path) -> None:
    with LedgerStore(tmp_path / "q", deployed_commit="c1") as store:
        collector = ProspectiveCollector(CollectorConfig(data_root=str(store.data_root)), store=store)
        page = _be_page([_be_row("q001", dt_raw="24,9,2026,20,0", ts="1790276400",
                                 odds=("1.90", "3.40", "3.80"))])
        _patch_legs(
            collector,
            sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
            betexplorer_bodies=[page],
            base=BASE,
        )
        collector.run_round()
        assert collector.sealed is False
        rows = store._conn.execute("SELECT DISTINCT dataset_phase AS p FROM captures").fetchall()
        assert [row["p"] for row in rows] == ["QUALIFICATION"]


# ==========================================================================
# §17.3 - the planned end is absolute and does not slide on restart
# ==========================================================================


def _manifest_kwargs(data_root: Path, *, start: dt.datetime) -> dict:
    return {
        "task_id": "TASK-0006",
        "run_id": "TESTRUN",
        "dataset_phase": SEALED,
        "frozen_commit": "deadbeef",
        "collector_version": "test-collector/0.0",
        "parser_version": "test-parser/0.0",
        "data_root": str(data_root),
        "planned_start_utc": start,
        "sporttery_endpoint": "https://example.invalid/sporttery",
        "betexplorer_endpoint": "https://example.invalid/betexplorer",
        "reference_label": "reference_proxy",
        "cadence_seconds": 60.0,
        "http_timeout_seconds": 50.0,
        "schema_version": SCHEMA_VERSION,
        "schema_hash": schema_hash(),
        "service_unit": "evlab-task0006.service",
    }


def test_manifest_planned_end_is_start_plus_120h(tmp_path: Path) -> None:
    start = dt.datetime(2026, 9, 28, 8, 0, tzinfo=UTC)
    manifest = build_manifest(**_manifest_kwargs(tmp_path / "data", start=start))

    assert manifest.duration_hours == SEALED_DURATION_HOURS
    span = dt.datetime.fromisoformat(manifest.planned_end_utc) - dt.datetime.fromisoformat(
        manifest.planned_start_utc
    )
    assert span == dt.timedelta(hours=120)
    # A manifest is publishable metadata: it must carry no secret material.
    rendered = json.dumps(asdict(manifest)).lower()
    for forbidden in ("password", "token", "secret", "api_key", "apikey"):
        assert forbidden not in rendered


def test_planned_end_is_read_from_manifest_and_does_not_slide(tmp_path: Path) -> None:
    """§17.3: a restart re-reads the same deadline instead of restarting the clock."""
    root = tmp_path / "data"
    config = CollectorConfig(data_root=str(root), dataset_phase=SEALED)

    # First "process": create the manifest (planned start fixed in the past).
    create_args = build_parser().parse_args(
        [
            "--data-root", str(root),
            "--dataset-phase", SEALED,
            "--run-id", "TESTRUN",
            "--write-manifest-only",
            "--planned-start-utc", "2026-09-28T08:00:00+00:00",
        ]
    )
    first_end = _resolve_sealed_deadline(create_args, config)

    # Later "processes": only read. The deadline must be identical every time,
    # even though real time has moved on.
    read_args = build_parser().parse_args(["--data-root", str(root)])
    second_end = _resolve_sealed_deadline(read_args, config)
    third_end = _resolve_sealed_deadline(read_args, config)

    assert first_end == second_end == third_end
    assert first_end == dt.datetime(2026, 10, 3, 8, 0, tzinfo=UTC)


# ==========================================================================
# §17.4 - the collector refuses to run past the immutable deadline
# ==========================================================================


def test_collector_stops_after_immutable_planned_end(tmp_path: Path) -> None:
    past = dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC)
    config = CollectorConfig(
        data_root=str(tmp_path / "data"),
        dataset_phase=SEALED,
        planned_end_utc=past,
    )
    collector = ProspectiveCollector(config)

    rounds = {"n": 0}

    def never_round(*args: object, **kwargs: object) -> dict:
        rounds["n"] += 1
        return {}

    collector.run_round = never_round  # type: ignore[method-assign]
    collector.run_forever()
    collector.store.close()

    assert rounds["n"] == 0, "the loop ran a round after the sealed deadline had passed"


def test_collector_runs_before_the_deadline(tmp_path: Path) -> None:
    """The guard must not be unconditional: a future deadline still collects."""
    future = dt.datetime(2099, 1, 1, tzinfo=UTC)
    config = CollectorConfig(
        data_root=str(tmp_path / "data"),
        dataset_phase=SEALED,
        planned_end_utc=future,
        max_rounds=1,
        # Keep the cadence tiny so the loop does not sit in its inter-round wait.
        round_interval_seconds=0.01,
    )
    collector = ProspectiveCollector(config)
    page = _be_page([_be_row("f001", dt_raw="24,9,2026,20,0", ts="1790276400",
                             odds=("1.90", "3.40", "3.80"))])
    _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[page],
        base=BASE,
    )
    collector.run_forever()
    assert collector.store.count_captures() == 2
    collector.store.close()


# ==========================================================================
# §17.5 / §17.6 - restart hydrates the baseline, and a move across a restart
#                is still detected with the honest (wide) interval
# ==========================================================================


def _round_once(data_root: Path, *, page: str, payload: str, base: dt.datetime) -> None:
    with LedgerStore(data_root, deployed_commit="c1", dataset_phase=SEALED) as store:
        collector = _sealed_collector(store)
        _patch_legs(
            collector,
            sporttery_bodies=[payload],
            betexplorer_bodies=[page],
            base=base,
        )
        collector.run_round()


def test_restart_hydrates_prior_reference_baseline(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    page = _be_page(
        [_be_row("hyd001", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("2.15", "3.45", "3.65"))],
        geo="cn", serial="2609081259",
    )
    payload = _sporttery_payload(had=("2.23", "3.56", "2.50"))
    _round_once(data_root, page=page, payload=payload, base=BASE)

    with LedgerStore(data_root, deployed_commit="c1", dataset_phase=SEALED) as store:
        restarted = _sealed_collector(store)
        key = (variant_key_from_label(VARIANT_LABEL), "hyd001")
        assert key in restarted._last_reference, "baseline was not hydrated"
        assert restarted._last_reference[key][0] == (2.15, 3.45, 3.65)
        assert restarted._last_reference[key][1] == BASE + dt.timedelta(seconds=1, milliseconds=700)
        assert restarted._last_variant_label == VARIANT_LABEL
        assert restarted._last_variant_key == ("cn", "2609081259")


def test_same_variant_move_across_restart_is_detected_with_wide_interval(
    tmp_path: Path,
) -> None:
    """§17.6: the move is bracketed by the pre-restart and post-restart receives."""
    data_root = tmp_path / "data"
    before = _be_page(
        [_be_row("xrst01", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("2.15", "3.45", "3.65"))],
        geo="cn", serial="2609081259",
    )
    after = _be_page(
        [_be_row("xrst01", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("1.95", "3.60", "4.10"))],
        geo="cn", serial="2609081259",
    )
    payload = _sporttery_payload(had=("2.23", "3.56", "2.50"))

    _round_once(data_root, page=before, payload=payload, base=BASE)
    second_base = BASE + dt.timedelta(minutes=30)

    with LedgerStore(data_root, deployed_commit="c1", dataset_phase=SEALED) as store:
        collector = _sealed_collector(store)
        calls = _patch_legs(
            collector,
            sporttery_bodies=[payload],
            betexplorer_bodies=[after],
            base=second_base,
        )
        collector.run_round()
        assert calls["sporttery"] == 2, "restart must not lose the baseline comparison"

        change = store._conn.execute("SELECT * FROM reference_changes").fetchone()

    assert change is not None, "a real move across a restart went unnoticed"
    assert change["event_id"] == "xrst01"
    assert change["source_variant"] == VARIANT_LABEL
    assert json.loads(change["previous_tuple"]) == [2.15, 3.45, 3.65]
    assert json.loads(change["current_tuple"]) == [1.95, 3.60, 4.10]
    # The bracket spans the restart gap and is never tightened to look precise.
    lower = dt.datetime.fromisoformat(change["change_interval_lower"])
    upper = dt.datetime.fromisoformat(change["change_interval_upper"])
    assert lower == BASE + dt.timedelta(seconds=1, milliseconds=700)
    assert upper == second_base + dt.timedelta(seconds=1, milliseconds=700)
    assert (upper - lower).total_seconds() > 1700


# ==========================================================================
# §17.7 - variant transitions still never become reference changes
# ==========================================================================


def test_sealed_variant_transition_produces_no_reference_change(
    sealed_store: LedgerStore,
) -> None:
    collector = _sealed_collector(sealed_store)
    same = ("2.15", "3.45", "3.65")
    page_cn = _be_page(
        [_be_row("vtran1", dt_raw="24,9,2026,20,0", ts="1790276400", odds=same)],
        geo="cn", serial="2609081259",
    )
    page_sa = _be_page(
        [_be_row("vtran1", dt_raw="24,9,2026,20,0", ts="1790276400", odds=same)],
        geo="sa", serial="2608290548",
    )
    _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[page_cn, page_sa, page_cn, page_sa],
        base=BASE,
    )
    for _ in range(4):
        collector.run_round()

    assert sealed_store._conn.execute(
        "SELECT COUNT(*) AS n FROM reference_changes"
    ).fetchone()["n"] == 0
    assert sealed_store.count_captures(kind=CAPTURE_KIND_CHANGE_CONFIRMATION) == 0
    assert sealed_store.count_variant_transitions() == 3


# ==========================================================================
# §17.8 - 0 / 1 / N confirmation behaviour is unchanged in sealed mode
# ==========================================================================


def test_sealed_confirmation_behaviour_zero_one_and_n(sealed_store: LedgerStore) -> None:
    collector = _sealed_collector(sealed_store)
    payload = _sporttery_payload(had=("2.23", "3.56", "2.50"))
    BASE_ODDS = ("2.15", "3.45", "3.65")
    MOVED = ("1.95", "3.60", "4.10")
    FINAL = ("1.80", "3.70", "4.30")

    def page(odds: tuple[str, str, str], count: int) -> str:
        return _be_page(
            [
                _be_row(f"cnf{index:03d}", dt_raw="24,9,2026,20,0", ts="1790276400", odds=odds)
                for index in range(count)
            ],
            geo="cn", serial="2609081259",
        )

    def mixed_page() -> str:
        """Four fixtures unchanged, one moved - the 'exactly one' case."""
        rows = [_be_row("cnf000", dt_raw="24,9,2026,20,0", ts="1790276400", odds=MOVED)]
        rows += [
            _be_row(f"cnf{index:03d}", dt_raw="24,9,2026,20,0", ts="1790276400", odds=BASE_ODDS)
            for index in range(1, 5)
        ]
        return _be_page(rows, geo="cn", serial="2609081259")

    # Round 1 establishes five baselines: zero changes -> zero confirmations.
    _patch_legs(
        collector,
        sporttery_bodies=[payload],
        betexplorer_bodies=[page(BASE_ODDS, count=5)],
        base=BASE,
    )
    collector.run_round()
    assert sealed_store.count_captures(kind=CAPTURE_KIND_CHANGE_CONFIRMATION) == 0

    # Round 2: exactly one fixture moves -> exactly one confirmation.
    _patch_legs(
        collector,
        sporttery_bodies=[payload],
        betexplorer_bodies=[mixed_page()],
        base=BASE + dt.timedelta(minutes=5),
    )
    collector.run_round()
    assert sealed_store.count_captures(kind=CAPTURE_KIND_CHANGE_CONFIRMATION) == 1

    # Round 3: all five move in one response -> still exactly one confirmation.
    _patch_legs(
        collector,
        sporttery_bodies=[payload],
        betexplorer_bodies=[page(FINAL, count=5)],
        base=BASE + dt.timedelta(minutes=10),
    )
    collector.run_round()
    assert sealed_store.count_captures(kind=CAPTURE_KIND_CHANGE_CONFIRMATION) == 2

    def confirm_ids(round_seq: int) -> list:
        return sealed_store._conn.execute(
            "SELECT confirmation_capture_id FROM reference_changes WHERE round_seq = ?",
            (round_seq,),
        ).fetchall()

    assert len(confirm_ids(2)) == 1
    third_round = confirm_ids(3)
    assert len(third_round) == 5
    # Five changes from one response, all confirmed by the same snapshot.
    assert len({row["confirmation_capture_id"] for row in third_round}) == 1


# ==========================================================================
# §17.9 / §17.10 - sealed logs carry operations, never results
# ==========================================================================


def test_sealed_logs_do_not_emit_odds(
    sealed_store: LedgerStore, caplog: pytest.LogCaptureFixture
) -> None:
    collector = _sealed_collector(sealed_store)
    page = _be_page(
        [_be_row("log001", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("2.15", "3.45", "3.65"))],
        geo="cn", serial="2609081259",
    )
    _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[page, page],
        base=BASE,
    )
    with caplog.at_level(logging.INFO, logger="task0005.collector"):
        collector.run_round()
        collector.run_round()

    logged = caplog.text
    for odd in ("2.15", "3.45", "3.65", "2.23", "3.56", "2.50"):
        assert odd not in logged, f"sealed log leaked an odds value: {odd}"


def test_sealed_logs_do_not_emit_change_counts_or_event_identity(
    sealed_store: LedgerStore, caplog: pytest.LogCaptureFixture
) -> None:
    collector = _sealed_collector(sealed_store)
    page = _be_page(
        [_be_row("log002", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("2.15", "3.45", "3.65"))],
        geo="cn", serial="2609081259",
    )
    _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[page],
        base=BASE,
    )
    with caplog.at_level(logging.INFO, logger="task0005.collector"):
        summary = collector.run_round()
        collector._log_round_summary(summary)

    logged = caplog.text
    assert "changes" not in logged.lower(), "sealed log leaked a change count"
    assert "log002" not in logged, "sealed log leaked an event identity"
    assert "variant=" not in logged, "sealed log leaked the served variant"
    assert "confirmation" not in logged.lower(), "sealed log leaked confirmation activity"


def test_unsealed_logs_still_carry_the_operational_detail(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The sealed filter must be a filter, not a blanket silence."""
    with LedgerStore(tmp_path / "q", deployed_commit="c1") as store:
        collector = ProspectiveCollector(CollectorConfig(data_root=str(store.data_root)), store=store)
        page = _be_page([_be_row("log003", dt_raw="24,9,2026,20,0", ts="1790276400",
                                 odds=("1.90", "3.40", "3.80"))])
        _patch_legs(
            collector,
            sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
            betexplorer_bodies=[page],
            base=BASE,
        )
        with caplog.at_level(logging.INFO, logger="task0005.collector"):
            summary = collector.run_round()
            collector._log_round_summary(summary)

    assert "variant=" in caplog.text
    assert "changes" in caplog.text.lower()


# ==========================================================================
# §17.11 - incompatible pre-existing state fails closed
# ==========================================================================


def test_phase_guard_fails_closed_on_foreign_rows(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    page = _be_page([_be_row("mix001", dt_raw="24,9,2026,20,0", ts="1790276400",
                             odds=("1.90", "3.40", "3.80"))])
    payload = _sporttery_payload(had=("2.23", "3.56", "2.50"))

    # A qualification run writes into the root first.
    with LedgerStore(data_root, deployed_commit="c1") as store:
        collector = ProspectiveCollector(CollectorConfig(data_root=str(data_root)), store=store)
        _patch_legs(
            collector,
            sporttery_bodies=[payload],
            betexplorer_bodies=[page],
            base=BASE,
        )
        collector.run_round()

    # Opening the same root as a sealed store must refuse, not interleave.
    with pytest.raises(RuntimeError, match="another dataset phase"):
        LedgerStore(data_root, deployed_commit="c1", dataset_phase=SEALED)


def test_unknown_phase_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown dataset_phase"):
        LedgerStore(tmp_path / "data", dataset_phase="NOT_A_PHASE")


def test_fresh_sealed_root_accepts_its_own_phase(tmp_path: Path) -> None:
    """The guard must not block ordinary restarts of the same sealed root."""
    data_root = tmp_path / "data"
    with LedgerStore(data_root, deployed_commit="c1", dataset_phase=SEALED):
        pass
    with LedgerStore(data_root, deployed_commit="c1", dataset_phase=SEALED) as store:
        assert store.dataset_phase == SEALED


# ==========================================================================
# §5.2 - the manifest is immutable and cannot be attached to live data
# ==========================================================================


def test_manifest_is_written_once_and_refuses_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "data"
    start = dt.datetime(2026, 9, 28, 8, 0, tzinfo=UTC)
    manifest = build_manifest(**_manifest_kwargs(root, start=start))

    path, digest = write_manifest(root, manifest)
    assert path.is_file()
    assert read_manifest(root)["run_id"] == "TESTRUN"

    with pytest.raises(ManifestError, match="immutable"):
        write_manifest(root, manifest)
    # The original bytes are untouched by the refused write.
    assert read_manifest(root)["planned_end_utc"] == manifest.planned_end_utc
    assert digest


def test_manifest_refuses_a_root_that_already_holds_captures(tmp_path: Path) -> None:
    root = tmp_path / "data"
    with LedgerStore(root, deployed_commit="c1", dataset_phase=SEALED) as store:
        store.record_capture(
            CaptureRecord(
                round_id="r1",
                capture_kind=CAPTURE_KIND_REGULAR,
                source=SOURCE_REFERENCE_BETEXPLORER,
                request_url="https://example.invalid/",
                request_started_at=BASE,
                response_received_at=BASE,
                latency_ms=1.0,
                http_status=200,
                failure_class=None,
                raw_byte_length=1,
                raw_sha256="0" * 64,
                raw_file_path="x.gz",
                parser_version="p",
                deployed_commit="c1",
            )
        )

    manifest = build_manifest(**_manifest_kwargs(root, start=BASE))
    with pytest.raises(ManifestError, match="before the first formal capture"):
        write_manifest(root, manifest)


def test_sealed_mode_refuses_to_start_without_a_manifest(tmp_path: Path) -> None:
    root = tmp_path / "data"
    config = CollectorConfig(data_root=str(root), dataset_phase=SEALED)
    args = build_parser().parse_args(["--data-root", str(root)])
    with pytest.raises(SystemExit, match="sealed mode requires"):
        _resolve_sealed_deadline(args, config)


# ==========================================================================
# §17.12 - the TASK-0005 qualification suite still passes unchanged
# ==========================================================================


def test_variant_label_round_trip() -> None:
    """The hydrate path depends on the label being reversible."""
    assert variant_key_from_label(VARIANT_LABEL) == ("cn", "2609081259")
    assert variant_key_from_label("geo=?|serial=?") == ("?", "?")
    # A non-variant label has no key, and is not guessed at.
    assert variant_key_from_label("decode_error") is None
    assert variant_key_from_label(None) is None
