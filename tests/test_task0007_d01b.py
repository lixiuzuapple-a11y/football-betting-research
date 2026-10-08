from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from football_betting.analysis.d01b import (
    analyze,
    batch_stratum,
    executable_had,
    observed_stale,
    proxy_metrics,
)
from football_betting.matching.teams import (
    ReferenceFixture,
    SportteryFixture,
    TeamNameMap,
    match_fixture,
    normalize_english_name,
)
from football_betting.prospective.ledger import (
    CAPTURE_KIND_CHANGE_CONFIRMATION,
    CAPTURE_KIND_REGULAR,
    PHASE_PROSPECTIVE_SEALED,
    SOURCE_OFFICIAL_SPORTTERY,
    SOURCE_REFERENCE_BETEXPLORER,
    CaptureRecord,
    LedgerStore,
)

UTC = timezone.utc
BJ = timezone(timedelta(hours=8))


def _map_path(tmp_path: Path) -> Path:
    path = tmp_path / "map.json"
    path.write_text(
        json.dumps(
            {
                "E0": [
                    {
                        "en": "Manchester United",
                        "cn": "曼联",
                        "cn_full": "曼彻斯特联",
                        "aliases": [],
                    },
                    {
                        "en": "Arsenal",
                        "cn": "阿森纳",
                        "cn_full": "阿森纳",
                        "aliases": [],
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _map(tmp_path: Path) -> TeamNameMap:
    return TeamNameMap(_map_path(tmp_path))


def test_normalize_english_name_reuses_legacy_conservative_shape() -> None:
    assert normalize_english_name("Manchester United FC") == "manchester"
    assert normalize_english_name("Arsenal") == "arsenal"


def test_match_fixture_requires_direction_and_kickoff(tmp_path: Path) -> None:
    team_map = _map(tmp_path)
    ref = ReferenceFixture(
        "be1",
        "Manchester United",
        "Arsenal",
        datetime(2026, 10, 1, 12, tzinfo=UTC),
    )
    sport = [
        SportteryFixture(
            "jc1",
            "曼联",
            "阿森纳",
            datetime(2026, 10, 1, 20, 5, tzinfo=BJ),
        )
    ]
    matched = match_fixture(ref, sport, team_map)
    assert matched is not None
    assert matched.match_id == "jc1"
    assert matched.kickoff_delta_seconds == 300


def test_match_fixture_fails_closed_on_ambiguity(tmp_path: Path) -> None:
    team_map = _map(tmp_path)
    ref = ReferenceFixture(
        "be1",
        "Manchester United",
        "Arsenal",
        datetime(2026, 10, 1, 12, tzinfo=UTC),
    )
    sport = [
        SportteryFixture(
            "jc1", "曼联", "阿森纳", datetime(2026, 10, 1, 20, tzinfo=BJ)
        ),
        SportteryFixture(
            "jc2", "曼联", "阿森纳", datetime(2026, 10, 1, 20, 1, tzinfo=BJ)
        ),
    ]
    assert match_fixture(ref, sport, team_map) is None


def test_observed_stale_requires_odds_and_provider_time_unchanged() -> None:
    odds = (2.2, 3.1, 3.0)
    assert observed_stale(
        odds,
        "2026-10-01T10:00:00+08:00",
        odds,
        "2026-10-01T10:00:00+08:00",
    )
    assert not observed_stale(
        odds,
        "2026-10-01T10:00:00+08:00",
        odds,
        "2026-10-01T10:01:00+08:00",
    )
    assert observed_stale(odds, None, odds, None) is None


def test_executable_had_is_strict_and_close_aware() -> None:
    observed = datetime(2026, 10, 1, 19, 0, tzinfo=BJ)
    assert executable_had(
        pool_status="Selling",
        betting_single=0,
        betting_allup=1,
        close_date="2026-10-01",
        close_time="19:30:00",
        observed_at=observed,
    )
    assert not executable_had(
        pool_status="Selling",
        betting_single=1,
        betting_allup=1,
        close_date="2026-10-01",
        close_time="18:59:00",
        observed_at=observed,
    )
    assert (
        executable_had(
            pool_status=None,
            betting_single=1,
            betting_allup=1,
            close_date=None,
            close_time=None,
            observed_at=observed,
        )
        is None
    )


def test_proxy_metrics_only_report_probability_increases() -> None:
    metrics = proxy_metrics((2.0, 3.5, 4.0), (1.8, 3.8, 4.5), (2.1, 3.2, 3.1))
    assert metrics
    assert all(float(row["delta_q"]) > 0 for row in metrics)
    assert {str(row["side"]) for row in metrics}.issubset({"H", "D", "A"})


def test_batch_strata_are_frozen() -> None:
    assert batch_stratum(1) == "1"
    assert batch_stratum(2) == "2-5"
    assert batch_stratum(5) == "2-5"
    assert batch_stratum(6) == "6-20"
    assert batch_stratum(20) == "6-20"
    assert batch_stratum(21) == ">20"


def _capture(
    store: LedgerStore,
    *,
    round_id: str,
    kind: str,
    source: str,
    when: datetime,
    variant: str | None = None,
) -> int:
    return store.record_capture(
        CaptureRecord(
            round_id=round_id,
            round_seq=1,
            run_session_id="synthetic",
            capture_kind=kind,
            source=source,
            source_variant=variant,
            request_url="https://example.invalid/",
            request_started_at=when - timedelta(seconds=1),
            response_received_at=when,
            latency_ms=1000.0,
            http_status=200,
            failure_class=None,
            raw_byte_length=3,
            raw_sha256="0" * 64,
            raw_file_path="synthetic",
            parser_version="synthetic",
            deployed_commit="synthetic",
        )
    )


def _build_synthetic_ledger(
    tmp_path: Path,
    *,
    confirmation_provider_time: str = "2026-10-01T19:00:00+08:00",
) -> tuple[Path, Path]:
    root = tmp_path / "ledger"
    team_map = _map_path(tmp_path)
    t_prev = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    t_curr = datetime(2026, 10, 1, 12, 1, tzinfo=UTC)
    t_confirm = datetime(2026, 10, 1, 12, 1, 5, tzinfo=UTC)
    t_next = datetime(2026, 10, 1, 12, 2, tzinfo=UTC)
    variant = "geo=cn|serial=1"
    provider_time = "2026-10-01T19:00:00+08:00"

    with LedgerStore(
        root,
        deployed_commit="synthetic",
        dataset_phase=PHASE_PROSPECTIVE_SEALED,
    ) as store:
        sp0 = _capture(
            store,
            round_id="r0",
            kind=CAPTURE_KIND_REGULAR,
            source=SOURCE_OFFICIAL_SPORTTERY,
            when=t_prev - timedelta(seconds=5),
        )
        store.record_sporttery_facts(
            sp0,
            [
                {
                    "match_id": "jc1",
                    "match_num_str": "周四001",
                    "league": "英超",
                    "home": "曼联",
                    "away": "阿森纳",
                    "kickoff_local": "2026-10-01T23:00:00+08:00",
                    "had_h": 2.20,
                    "had_d": 3.20,
                    "had_a": 3.00,
                    "provider_had_updated_at": provider_time,
                    "had_betting_single": 1,
                    "had_betting_allup": 1,
                    "had_pool_status": "Selling",
                    "had_close_date": "2026-10-01",
                    "had_close_time": "22:55:00",
                    "observed_at": (t_prev - timedelta(seconds=5)).isoformat(),
                    "payload_sha256": "1" * 64,
                }
            ],
        )

        be0 = _capture(
            store,
            round_id="r0",
            kind=CAPTURE_KIND_REGULAR,
            source=SOURCE_REFERENCE_BETEXPLORER,
            when=t_prev,
            variant=variant,
        )
        store.record_betexplorer_facts(
            be0,
            [
                {
                    "event_id": "be1",
                    "source_variant": variant,
                    "event_url": "/football/test/",
                    "home": "Manchester United",
                    "away": "Arsenal",
                    "kickoff_utc": "2026-10-01T15:00:00+00:00",
                    "home_odds": 2.00,
                    "draw_odds": 3.50,
                    "away_odds": 4.00,
                    "response_received_at": t_prev.isoformat(),
                    "duplicate_copies_collapsed": 1,
                    "parser_status": "ok",
                }
            ],
        )

        be1 = _capture(
            store,
            round_id="r1",
            kind=CAPTURE_KIND_REGULAR,
            source=SOURCE_REFERENCE_BETEXPLORER,
            when=t_curr,
            variant=variant,
        )
        store.record_betexplorer_facts(
            be1,
            [
                {
                    "event_id": "be1",
                    "source_variant": variant,
                    "event_url": "/football/test/",
                    "home": "Manchester United",
                    "away": "Arsenal",
                    "kickoff_utc": "2026-10-01T15:00:00+00:00",
                    "home_odds": 1.80,
                    "draw_odds": 3.80,
                    "away_odds": 4.50,
                    "response_received_at": t_curr.isoformat(),
                    "duplicate_copies_collapsed": 1,
                    "parser_status": "ok",
                }
            ],
        )

        confirm = _capture(
            store,
            round_id="r1",
            kind=CAPTURE_KIND_CHANGE_CONFIRMATION,
            source=SOURCE_OFFICIAL_SPORTTERY,
            when=t_confirm,
        )
        store.record_sporttery_facts(
            confirm,
            [
                {
                    "match_id": "jc1",
                    "match_num_str": "周四001",
                    "league": "英超",
                    "home": "曼联",
                    "away": "阿森纳",
                    "kickoff_local": "2026-10-01T23:00:00+08:00",
                    "had_h": 2.20,
                    "had_d": 3.20,
                    "had_a": 3.00,
                    "provider_had_updated_at": confirmation_provider_time,
                    "had_betting_single": 1,
                    "had_betting_allup": 1,
                    "had_pool_status": "Selling",
                    "had_close_date": "2026-10-01",
                    "had_close_time": "22:55:00",
                    "observed_at": t_confirm.isoformat(),
                    "payload_sha256": "2" * 64,
                }
            ],
        )
        store.record_reference_change(
            event_id="be1",
            source_variant=variant,
            previous_tuple=(2.00, 3.50, 4.00),
            current_tuple=(1.80, 3.80, 4.50),
            previous_response_received_at=t_prev,
            current_response_received_at=t_curr,
            confirmation_capture_id=confirm,
            round_id="r1",
            round_seq=1,
            run_session_id="synthetic",
        )

        be2 = _capture(
            store,
            round_id="r2",
            kind=CAPTURE_KIND_REGULAR,
            source=SOURCE_REFERENCE_BETEXPLORER,
            when=t_next,
            variant=variant,
        )
        store.record_betexplorer_facts(
            be2,
            [
                {
                    "event_id": "be1",
                    "source_variant": variant,
                    "event_url": "/football/test/",
                    "home": "Manchester United",
                    "away": "Arsenal",
                    "kickoff_utc": "2026-10-01T15:00:00+00:00",
                    "home_odds": 1.80,
                    "draw_odds": 3.80,
                    "away_odds": 4.50,
                    "response_received_at": t_next.isoformat(),
                    "duplicate_copies_collapsed": 1,
                    "parser_status": "ok",
                }
            ],
        )
    return root / "ledger.sqlite3", team_map


def test_synthetic_end_to_end_primary_candidate_and_determinism(tmp_path: Path) -> None:
    db, team_map = _build_synthetic_ledger(tmp_path)
    first = analyze(db, team_map, tmp_path / "out1")
    second = analyze(db, team_map, tmp_path / "out2")
    assert first == second
    assert first["reference_change_rows"] == 1
    assert first["matched_change_rows"] == 1
    assert first["primary_candidate_rows"] == 1
    assert first["primary_candidate_fixtures"] == 1
    assert first["primary_candidate_calendar_days"] == 1
    assert first["batch_size_summary"]["confirmation_capture_strata"] == {"1": 1}
    assert first["reference_persistence"] == {"persists_next_observation": 1}


def test_synthetic_provider_timestamp_change_blocks_primary_stale(tmp_path: Path) -> None:
    db, team_map = _build_synthetic_ledger(
        tmp_path,
        confirmation_provider_time="2026-10-01T19:01:00+08:00",
    )
    summary = analyze(db, team_map, tmp_path / "out")
    assert summary["analyzable_change_rows"] == 1
    assert summary["observed_stale_rows"] == 0
    assert summary["primary_candidate_rows"] == 0
