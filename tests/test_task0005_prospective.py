"""Deterministic tests for the TASK-0005 prospective collector and its parsers.

Everything here is offline. The collector's HTTP legs are exercised through a
monkeypatched fetch, so these tests never touch the network - a capture test
that reached the internet would fail for reasons unrelated to the code.

The ten cases the task lists (§10) are covered by, in order:

1. ``test_betexplorer_parses_current_page_1x2``
2. ``test_betexplorer_collapses_desktop_mobile_duplicates``
3. ``test_betexplorer_fails_closed_on_invalid_rows``
4. ``test_request_and_response_clocks_stay_distinct``
5. ``test_betexplorer_provider_update_time_is_absent_not_invented``
6. ``test_reference_change_interval_is_bracketed_not_invented``
7. ``test_changed_reference_triggers_exactly_one_confirmation``
8. ``test_unchanged_reference_triggers_no_confirmation``
9. ``test_restart_appends_and_never_overwrites``
10. ``test_raw_hash_and_provenance_are_recorded``
"""

from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import pytest

from football_betting.data.betexplorer import (
    REFERENCE_PROXY_LABEL,
    BetExplorerQuote,
    parse_homepage,
)
from football_betting.prospective.collector import (
    CollectorConfig,
    LegOutcome,
    ProspectiveCollector,
)
from football_betting.prospective.ledger import (
    CAPTURE_KIND_CHANGE_CONFIRMATION,
    CAPTURE_KIND_REGULAR,
    DATASET_PHASE,
    SOURCE_OFFICIAL_SPORTTERY,
    LedgerStore,
)

UTC = dt.timezone.utc


# --------------------------------------------------------------------------
# Fixtures: a real-shaped BetExplorer row and a real-shaped Sporttery payload
# --------------------------------------------------------------------------

def _be_row(
    event_id: str,
    *,
    dt_raw: str,
    ts: str,
    odds: tuple[str, str, str],
    home: str = "Home FC",
    away: str = "Away FC",
    cls_suffix: str = "tournamentLiContentMobile",
) -> str:
    """One match ``<li>`` in the measured homepage dialect."""
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


def _be_page(rows: list[str]) -> str:
    return "<html><body><ul>" + "".join(rows) + "</ul></body></html>"


def _sporttery_payload(*, had: tuple[str, str, str]) -> str:
    """A minimal but real-shaped ``getMatchCalculatorV1.qry`` body."""
    return json.dumps(
        {
            "errorCode": "0",
            "errorMessage": "处理成功",
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


@pytest.fixture()
def store(tmp_path: Path) -> LedgerStore:
    with LedgerStore(tmp_path / "data", deployed_commit="test-commit") as handle:
        yield handle


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


# --------------------------------------------------------------------------
# 1. BetExplorer current-page 1X2 parsing
# --------------------------------------------------------------------------

def test_betexplorer_parses_current_page_1x2() -> None:
    page = _be_page(
        [
            _be_row("aaa111", dt_raw="24,9,2026,2,30", ts="1790213400",
                    odds=("1.76", "3.88", "4.14")),
            _be_row("bbb222", dt_raw="24,9,2026,17,0", ts="1790265600",
                    odds=("4.05", "2.65", "2.23")),
        ]
    )
    received = dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC)
    result = parse_homepage(page, response_received_at=received)

    assert len(result.quotes) == 2
    first = result.quotes[0]
    assert first.event_id == "aaa111"
    assert first.odds_tuple == (1.76, 3.88, 4.14)
    assert first.home == "Home FC" and first.away == "Away FC"
    assert first.event_url == "/football/eng/england/aaa111/"
    # data-ts is an unambiguous epoch -> aware UTC kickoff.
    assert first.kickoff_utc == dt.datetime(2026, 9, 24, 1, 30, tzinfo=UTC)
    # The raw dialect string is preserved verbatim, un-normalised.
    assert first.data_dt_raw == "24,9,2026,2,30"


# --------------------------------------------------------------------------
# 2. Desktop/mobile duplicate collapse
# --------------------------------------------------------------------------

def test_betexplorer_collapses_desktop_mobile_duplicates() -> None:
    shared = {"dt_raw": "24,9,2026,19,45", "ts": "1790275500", "odds": ("1.46", "4.60", "6.23")}
    page = _be_page(
        [
            # Same event rendered twice; the second copy is discarded.
            _be_row("dup001", cls_suffix="tournamentLiContentMobile", **shared),
            _be_row("dup001", cls_suffix="tournamentLiContentDesktop", **shared),
            _be_row("solo002", dt_raw="24,9,2026,20,0", ts="1790276400",
                    odds=("2.00", "3.00", "3.50")),
        ]
    )
    result = parse_homepage(page, response_received_at=dt.datetime(2026, 9, 25, tzinfo=UTC))

    assert result.rows_seen == 3
    assert len(result.quotes) == 2
    assert result.duplicates_collapsed == 1
    # Provider identifiers stay in full - never truncated to "the unique part".
    assert [q.event_id for q in result.quotes] == ["dup001", "solo002"]


# --------------------------------------------------------------------------
# 3. Ambiguous / invalid rows fail closed
# --------------------------------------------------------------------------

def test_betexplorer_fails_closed_on_invalid_rows() -> None:
    page = _be_page(
        [
            # Two odds only -> ambiguous triple, must be rejected, not guessed.
            _be_row("short01", dt_raw="24,9,2026,20,0", ts="1790276400",
                    odds=("1.50", "3.20")),
            # Non-numeric value -> rejected.
            _be_row("badnum1", dt_raw="24,9,2026,20,0", ts="1790276400",
                    odds=("1.50", "abc", "3.20")),
            # A plausible odd of 1.00 cannot be a decimal price -> rejected.
            _be_row("oneodd1", dt_raw="24,9,2026,20,0", ts="1790276400",
                    odds=("1.00", "3.20", "4.00")),
            # Valid, and must survive alongside the rejections.
            _be_row("good001", dt_raw="24,9,2026,20,0", ts="1790276400",
                    odds=("1.90", "3.40", "3.80")),
        ]
    )
    result = parse_homepage(page, response_received_at=dt.datetime(2026, 9, 25, tzinfo=UTC))

    assert len(result.quotes) == 1
    assert result.quotes[0].event_id == "good001"
    assert len(result.issues) == 3
    assert {issue.reason for issue in result.issues} == {"unparsable_1x2"}
    # Rejections are retained with detail, never silently dropped.
    assert all(issue.detail for issue in result.issues)


def test_rows_without_odds_are_not_counted_as_issues() -> None:
    """An unpriced fixture is an ordinary state, not a parse defect."""
    page = _be_page(
        [
            _be_row("noodds1", dt_raw="24,9,2026,20,0", ts="1790276400", odds=()),
            _be_row("good002", dt_raw="24,9,2026,20,0", ts="1790276400",
                    odds=("1.90", "3.40", "3.80")),
        ]
    )
    result = parse_homepage(page, response_received_at=dt.datetime(2026, 9, 25, tzinfo=UTC))
    assert len(result.quotes) == 1
    assert result.issues == ()
    assert result.rows_without_odds == 1


# --------------------------------------------------------------------------
# 4. Request-start / response-receive clocks remain distinct
# --------------------------------------------------------------------------

def test_request_and_response_clocks_stay_distinct(store: LedgerStore) -> None:
    started = dt.datetime(2026, 9, 25, 3, 0, 0, tzinfo=UTC)
    received = dt.datetime(2026, 9, 25, 3, 0, 45, tzinfo=UTC)  # 45s slow response
    page = _be_page([_be_row("clk001", dt_raw="24,9,2026,20,0",
                             ts="1790276400", odds=("1.9", "3.4", "3.8"))])
    collector = ProspectiveCollector(
        CollectorConfig(data_root=str(store.data_root)), store=store
    )

    def fake_fetch(source: str, request: object) -> LegOutcome:
        return _outcome(source, text=page, started=started, received=received)

    collector._fetch = fake_fetch  # type: ignore[method-assign]
    capture_id, _changes = collector._capture_betexplorer(
        round_id="r00001", kind=CAPTURE_KIND_REGULAR
    )

    row = store._conn.execute(
        "SELECT request_started_at, response_received_at, latency_ms FROM captures "
        "WHERE capture_id = ?",
        (capture_id,),
    ).fetchone()

    assert row["request_started_at"] != row["response_received_at"]
    assert row["request_started_at"] == started.isoformat()
    assert row["response_received_at"] == received.isoformat()
    assert row["latency_ms"] == pytest.approx(45_000.0, abs=1.0)

    # A quote is never knowable before it arrived: the stored fact timestamp is
    # the response time, not the request time.
    fact = store._conn.execute(
        "SELECT response_received_at FROM betexplorer_facts WHERE capture_id = ?",
        (capture_id,),
    ).fetchone()
    assert fact["response_received_at"] == received.isoformat()


# --------------------------------------------------------------------------
# 5. BetExplorer provider update time is absent, not invented
# --------------------------------------------------------------------------

def test_betexplorer_provider_update_time_is_absent_not_invented() -> None:
    quote_fields = set(BetExplorerQuote.__dataclass_fields__)
    # No field may claim to be a provider-side update time.
    suspicious = {
        name
        for name in quote_fields
        if "provider" in name or "source_updated" in name or "updated_at" in name
    }
    assert suspicious == set(), f"BetExplorer quote must not expose {suspicious}"

    result = parse_homepage(
        _be_page([_be_row("t001", dt_raw="24,9,2026,20,0", ts="1790276400",
                          odds=("1.9", "3.4", "3.8"))]),
        response_received_at=dt.datetime(2026, 9, 25, tzinfo=UTC),
    )
    quote = result.quotes[0]
    # The only timestamp we may carry is our own receive time, and it is labelled
    # as exactly that.
    assert quote.response_received_at.tzinfo is not None
    assert quote.source_label == REFERENCE_PROXY_LABEL


# --------------------------------------------------------------------------
# 6. Reference change interval generation
# --------------------------------------------------------------------------

def test_reference_change_interval_is_bracketed_not_invented(store: LedgerStore) -> None:
    previous = dt.datetime(2026, 9, 25, 3, 0, 0, tzinfo=UTC)
    current = dt.datetime(2026, 9, 25, 3, 1, 0, tzinfo=UTC)

    change_id = store.record_reference_change(
        event_id="chg001",
        previous_tuple=(2.00, 3.30, 3.60),
        current_tuple=(1.85, 3.40, 3.90),
        previous_response_received_at=previous,
        current_response_received_at=current,
        confirmation_capture_id=42,
        round_id="r00007",
    )

    row = store._conn.execute(
        "SELECT * FROM reference_changes WHERE change_id = ?", (change_id,)
    ).fetchone()

    assert json.loads(row["previous_tuple"]) == [2.00, 3.30, 3.60]
    assert json.loads(row["current_tuple"]) == [1.85, 3.40, 3.90]
    # The interval is a bracket: after the previous observation, at or before
    # the current one. The exact provider instant is never claimed.
    assert row["change_interval_lower"] == previous.isoformat()
    assert row["change_interval_upper"] == current.isoformat()
    assert row["change_interval_lower"] != row["change_interval_upper"]
    assert row["dataset_phase"] == DATASET_PHASE
    assert row["confirmation_capture_id"] == 42


# --------------------------------------------------------------------------
# 7 & 8. Change detection -> exactly one confirmation; no change -> none
# --------------------------------------------------------------------------

def _patch_legs(
    collector: ProspectiveCollector,
    *,
    sporttery_bodies: list[str],
    betexplorer_bodies: list[str],
    base: dt.datetime,
) -> dict[str, int]:
    """Replace the network legs with deterministic scripted responses."""
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
                status=200,
            )
        index = min(calls["betexplorer"], len(betexplorer_bodies) - 1)
        calls["betexplorer"] += 1
        return _outcome(
            source,
            text=betexplorer_bodies[index],
            started=base + dt.timedelta(seconds=calls["betexplorer"]),
            received=base + dt.timedelta(seconds=calls["betexplorer"], milliseconds=700),
            status=200,
        )

    collector._fetch = fake_fetch  # type: ignore[method-assign]
    return calls


def test_changed_reference_triggers_exactly_one_confirmation(store: LedgerStore) -> None:
    collector = ProspectiveCollector(
        CollectorConfig(data_root=str(store.data_root)), store=store
    )
    page_round1 = _be_page(
        [_be_row("evt001", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("2.00", "3.30", "3.60"))]
    )
    page_round2 = _be_page(
        [_be_row("evt001", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("1.85", "3.40", "3.90"))]  # moved
    )
    calls = _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[page_round1, page_round2],
        base=dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC),
    )

    collector.run_round()  # establishes the baseline, no change expected
    assert store.count_captures(kind=CAPTURE_KIND_CHANGE_CONFIRMATION) == 0

    collector.run_round()  # tuple moved -> one confirmation fetch
    confirmations = store.count_captures(kind=CAPTURE_KIND_CHANGE_CONFIRMATION)
    assert confirmations == 1, f"expected exactly one confirmation, got {confirmations}"

    # Exactly one extra Sporttery call happened (2 regular + 1 confirmation).
    assert calls["sporttery"] == 3

    change = store._conn.execute("SELECT * FROM reference_changes").fetchone()
    assert change["event_id"] == "evt001"
    assert json.loads(change["previous_tuple"]) == [2.00, 3.30, 3.60]
    assert json.loads(change["current_tuple"]) == [1.85, 3.40, 3.90]
    # The confirmation capture is linked by id.
    linked = store._conn.execute(
        "SELECT capture_kind, change_event_id FROM captures WHERE capture_id = ?",
        (change["confirmation_capture_id"],),
    ).fetchone()
    assert linked["capture_kind"] == CAPTURE_KIND_CHANGE_CONFIRMATION
    assert linked["change_event_id"] == "evt001"


def test_unchanged_reference_triggers_no_confirmation(store: LedgerStore) -> None:
    collector = ProspectiveCollector(
        CollectorConfig(data_root=str(store.data_root)), store=store
    )
    stable = _be_page(
        [_be_row("evt002", dt_raw="24,9,2026,20,0", ts="1790276400",
                 odds=("2.00", "3.30", "3.60"))]
    )
    _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[stable, stable, stable],
        base=dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC),
    )

    collector.run_round()
    collector.run_round()
    collector.run_round()

    assert store.count_captures(kind=CAPTURE_KIND_CHANGE_CONFIRMATION) == 0
    assert store._conn.execute("SELECT COUNT(*) AS n FROM reference_changes").fetchone()["n"] == 0


# --------------------------------------------------------------------------
# 9. Restart / ledger idempotency: append, never overwrite
# --------------------------------------------------------------------------

def test_restart_appends_and_never_overwrites(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    page = _be_page([_be_row("rst001", dt_raw="24,9,2026,20,0", ts="1790276400",
                             odds=("1.9", "3.4", "3.8"))])
    payload = _sporttery_payload(had=("2.23", "3.56", "2.50"))
    base = dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC)

    # First "process".
    with LedgerStore(data_root, deployed_commit="c1") as store1:
        collector = ProspectiveCollector(
            CollectorConfig(data_root=str(data_root)), store=store1
        )
        _patch_legs(collector, sporttery_bodies=[payload],
                    betexplorer_bodies=[page], base=base)
        collector.run_round()
        first_total = store1.count_captures()
        first_be_facts = store1._conn.execute(
            "SELECT COUNT(*) AS n FROM betexplorer_facts"
        ).fetchone()["n"]

    # Second "process" against the same data root - simulating a service restart.
    with LedgerStore(data_root, deployed_commit="c1") as store2:
        collector = ProspectiveCollector(
            CollectorConfig(data_root=str(data_root)), store=store2
        )
        _patch_legs(collector, sporttery_bodies=[payload],
                    betexplorer_bodies=[page], base=base + dt.timedelta(minutes=1))
        collector.run_round()
        second_total = store2.count_captures()
        second_be_facts = store2._conn.execute(
            "SELECT COUNT(*) AS n FROM betexplorer_facts"
        ).fetchone()["n"]

    # New rows appended; nothing from the first run lost or mutated.
    assert second_total == first_total * 2
    assert second_be_facts == first_be_facts * 2
    assert second_total == 4


def test_raw_capture_filename_embeds_content_hash(store: LedgerStore) -> None:
    """Identical bytes are written once; different bytes never overwrite."""
    moment = dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC)
    digest_a, path_a = store.persist_raw(b"payload-A", source="s", observed_at=moment)
    digest_b, path_b = store.persist_raw(b"payload-A", source="s", observed_at=moment)
    digest_c, path_c = store.persist_raw(b"payload-B", source="s", observed_at=moment)

    assert digest_a == digest_b and path_a == path_b
    assert digest_a != digest_c and path_a != path_c
    written = list((store.data_root / "raw").rglob("*.gz"))
    assert len(written) == 2


# --------------------------------------------------------------------------
# 10. Raw-hash / provenance recording
# --------------------------------------------------------------------------

def test_raw_hash_and_provenance_are_recorded(store: LedgerStore) -> None:
    import hashlib

    page = _be_page([_be_row("prov01", dt_raw="24,9,2026,20,0", ts="1790276400",
                             odds=("1.9", "3.4", "3.8"))])
    started = dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC)
    received = dt.datetime(2026, 9, 25, 3, 0, 2, tzinfo=UTC)
    collector = ProspectiveCollector(
        CollectorConfig(data_root=str(store.data_root)), store=store
    )

    def fake_fetch(source: str, request: object) -> LegOutcome:
        return _outcome(source, text=page, started=started, received=received)

    collector._fetch = fake_fetch  # type: ignore[method-assign]
    capture_id, _changes = collector._capture_betexplorer(
        round_id="r00009", kind=CAPTURE_KIND_REGULAR
    )

    row = store._conn.execute(
        "SELECT * FROM captures WHERE capture_id = ?", (capture_id,)
    ).fetchone()

    expected = hashlib.sha256(page.encode("utf-8")).hexdigest()
    assert row["raw_sha256"] == expected
    assert row["raw_byte_length"] == len(page.encode("utf-8"))
    assert row["raw_file_path"] is not None
    assert row["deployed_commit"] == "test-commit"
    assert row["parser_version"]
    assert row["dataset_phase"] == DATASET_PHASE

    # The stored raw file really is the captured body, byte for byte.
    import gzip

    stored = gzip.decompress((store.data_root / "raw" / row["raw_file_path"]).read_bytes())
    assert hashlib.sha256(stored).hexdigest() == expected
    assert stored.decode("utf-8") == page


def test_failed_capture_still_keeps_raw_hash(store: LedgerStore) -> None:
    """TASK-0005 §7: keep the raw hash even when parsing fails."""
    challenge = "<html><body><script>navigator; verify()</script></body></html>"
    outcome = _outcome(
        SOURCE_OFFICIAL_SPORTTERY,
        text=challenge,
        started=dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC),
        received=dt.datetime(2026, 9, 25, 3, 0, 5, tzinfo=UTC),
        status=567,
        failure="http_error_567",
    )
    collector = ProspectiveCollector(
        CollectorConfig(data_root=str(store.data_root)), store=store
    )
    capture_id = collector._persist_leg(outcome, round_id="r00010", kind=CAPTURE_KIND_REGULAR)

    row = store._conn.execute(
        "SELECT * FROM captures WHERE capture_id = ?", (capture_id,)
    ).fetchone()
    assert row["failure_class"] == "http_error_567"
    assert row["http_status"] == 567
    assert row["raw_sha256"] is not None
    assert row["parser_version"] == "task0005-collector/0.1"


# --------------------------------------------------------------------------
# Boundary guards
# --------------------------------------------------------------------------

def test_naive_timestamps_are_rejected(store: LedgerStore) -> None:
    with pytest.raises(ValueError):
        parse_homepage(
            _be_page([]),
            response_received_at=dt.datetime(2026, 9, 25),  # naive
        )


def test_no_overlapping_rounds(store: LedgerStore, monkeypatch: pytest.MonkeyPatch) -> None:
    """Rounds must not overlap: no round may start before the previous finishes."""
    collector = ProspectiveCollector(
        CollectorConfig(data_root=str(store.data_root), round_interval_seconds=60.0),
        store=store,
    )
    page = _be_page([_be_row("ovl001", dt_raw="24,9,2026,20,0", ts="1790276400",
                             odds=("1.9", "3.4", "3.8"))])
    _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[page],
        base=dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC),
    )

    events: list[tuple[str, float]] = []
    clock = {"t": 1000.0}

    original_run_round = collector.run_round

    def tracking_round(*args: object, **kwargs: object) -> dict[str, object]:
        events.append(("enter", clock["t"]))
        clock["t"] += 5.0  # a round costs 5 seconds
        try:
            return original_run_round(*args, **kwargs)  # type: ignore[arg-type]
        finally:
            events.append(("exit", clock["t"]))

    def fake_monotonic() -> float:
        return clock["t"]

    def limited_wait(seconds: float) -> bool:
        clock["t"] += max(seconds, 0.0)
        if len([e for e in events if e[0] == "exit"]) >= 3:
            collector._stop.set()
        return False

    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    monkeypatch.setattr(collector, "run_round", tracking_round)
    monkeypatch.setattr(collector._stop, "wait", limited_wait)

    collector.run_forever()

    # Depth never exceeds one: rounds are strictly sequential.
    depth = 0
    peak = 0
    for kind, _t in events:
        depth += 1 if kind == "enter" else -1
        peak = max(peak, depth)
    assert peak == 1, f"rounds overlapped: {events}"
    assert len([e for e in events if e[0] == "enter"]) == 3

    # Start-to-start spacing holds: round N+1 begins ~60s after round N began.
    enters = [t for kind, t in events if kind == "enter"]
    for index, start in enumerate(enters[1:], start=1):
        gap = start - enters[index - 1]
        assert gap >= 60.0, f"rounds started {gap}s apart, expected >= 60s"


def test_dataset_phase_is_qualification_everywhere(store: LedgerStore) -> None:
    """Qualification data must never be mistakable for the sealed dataset."""
    assert DATASET_PHASE == "QUALIFICATION"
    page = _be_page([_be_row("phase1", dt_raw="24,9,2026,20,0", ts="1790276400",
                             odds=("1.9", "3.4", "3.8"))])
    collector = ProspectiveCollector(
        CollectorConfig(data_root=str(store.data_root)), store=store
    )
    _patch_legs(
        collector,
        sporttery_bodies=[_sporttery_payload(had=("2.23", "3.56", "2.50"))],
        betexplorer_bodies=[page],
        base=dt.datetime(2026, 9, 25, 3, 0, tzinfo=UTC),
    )
    collector.run_round()

    for table in ("captures", "sporttery_facts", "betexplorer_facts"):
        rows = store._conn.execute(f"SELECT DISTINCT dataset_phase FROM {table}").fetchall()
        assert [r["dataset_phase"] for r in rows] == [DATASET_PHASE], table
