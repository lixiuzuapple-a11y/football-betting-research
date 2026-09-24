"""Parser tests for the official Sporttery match-calculator payload.

The payload below is a trimmed copy of a real ``getMatchCalculatorV1.qry``
response captured 2026-09-24 (see ``REPORTS/TASK-0004.md`` §A). One extra row is
synthetic and marked as such. Everything is embedded so these tests need no
network and stay deterministic - a capture test that reaches the internet would
fail for reasons unrelated to the parser.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from football_betting.data.sporttery_webapi import (
    BEIJING,
    DEFAULT_REFERER,
    build_request,
    looks_like_challenge,
    parse_match_calculator,
    parse_provider_time,
    pools_of,
)

#: A ~7 kB interception page, not match data.
CHALLENGE_HTML = (
    "<!DOCTYPE html><html><head><title>Access</title></head><body>"
    "<script>window.navigator.userAgent; verify();</script></body></html>"
)


def _payload() -> dict[str, object]:
    return {
        "errorCode": "0",
        "errorMessage": "处理成功",
        "success": True,
        "value": {
            "totalCount": 2,
            "lastUpdateTime": "2026-09-23 21:50:41",
            "matchInfoList": [
                {
                    "businessDate": "2026-09-24",
                    "matchWeek": "周四",
                    "matchCount": 1,
                    "subMatchList": [
                        {
                            "matchId": 2041648,
                            "matchNumStr": "周四006",
                            "leagueAbbName": "欧国联",
                            "leagueCode": "UEFA",
                            "homeTeamAbbName": "荷兰",
                            "awayTeamAbbName": "德国",
                            "matchDate": "2026-09-25",
                            "matchTime": "02:45:00",
                            "matchStatus": "Selling",
                            "sellStatus": 2,
                            "had": {
                                "h": "2.23", "d": "3.56", "a": "2.50",
                                "updateDate": "2026-09-23", "updateTime": "09:17:36",
                            },
                            "hhad": {
                                "h": "4.35", "d": "4.22", "a": "1.51", "goalLine": "-1",
                                "updateDate": "2026-09-23", "updateTime": "09:17:36",
                            },
                            "ttg": {
                                "s0": "21.00", "s1": "7.25", "s2": "4.30", "s3": "3.60",
                                "s4": "4.60", "s5": "7.10", "s6": "12.00", "s7": "15.00",
                                "updateDate": "2026-09-23", "updateTime": "09:17:36",
                            },
                            "crs": {"some": "value"},
                            "hafu": {"hf": "1.50", "hd": "8.00", "ha": "12.00"},
                        }
                    ],
                },
                {
                    "businessDate": "2026-09-24",
                    "matchWeek": "周四",
                    "matchCount": 1,
                    "subMatchList": [
                        {
                            # Handicap-only listing: no standard 1X2 on sale.
                            "matchId": 2041645,
                            "matchNumStr": "周四003",
                            "leagueAbbName": "国际赛",
                            "leagueCode": "FRI",
                            "homeTeamAbbName": "中国",
                            "awayTeamAbbName": "马尔代夫",
                            "matchDate": "2026-09-24",
                            "matchTime": "19:35:00",
                            "matchStatus": "Selling",
                            "sellStatus": 2,
                            "had": {},
                            "hhad": {
                                "h": "2.30", "d": "4.80", "a": "2.06", "goalLine": "-4",
                                "updateDate": "2026-09-23", "updateTime": "09:17:36",
                            },
                            "ttg": {"s0": "100.0", "s1": "20.00", "s2": "8.75", "s3": "5.65",
                                    "s4": "4.60", "s5": "4.75", "s6": "5.80", "s7": "3.95"},
                        }
                    ],
                },
                {
                    "businessDate": "2026-09-24",
                    "matchWeek": "周四",
                    "matchCount": 1,
                    "subMatchList": [
                        {
                            # Synthetic row (not from the live capture): same
                            # shape, but every updateDate/updateTime stripped.
                            # It exists to prove the parser never back-fills a
                            # provider timestamp from our own clock.
                            "matchId": 2041999,
                            "matchNumStr": "周四099",
                            "leagueAbbName": "国际赛",
                            "leagueCode": "FRI",
                            "homeTeamAbbName": "甲队",
                            "awayTeamAbbName": "乙队",
                            "matchDate": "2026-09-24",
                            "matchTime": "20:00:00",
                            "matchStatus": "Selling",
                            "sellStatus": 2,
                            "had": {"h": "1.90", "d": "3.30", "a": "3.60"},
                            "hhad": {"h": "3.50", "d": "3.60", "a": "1.85", "goalLine": "-1"},
                            "ttg": {"s0": "9.00", "s1": "4.10", "s2": "3.25", "s3": "3.90",
                                    "s4": "6.50", "s5": "13.00", "s6": "26.00", "s7": "38.00"},
                        }
                    ],
                },
            ],
        },
    }


@pytest.fixture
def captured_at() -> datetime:
    return datetime(2026, 9, 24, 9, 18, 37, tzinfo=BEIJING)


def _parse(captured_at: datetime):
    return parse_match_calculator(
        json.dumps(_payload(), ensure_ascii=False), observed_at=captured_at
    )


def test_referer_header_is_always_sent() -> None:
    """Omitting Referer is what triggers the HTTP 567 challenge."""
    assert build_request().get_header("Referer") == DEFAULT_REFERER
    assert build_request(referer="https://www.lottery.gov.cn/").get_header("Referer") == (
        "https://www.lottery.gov.cn/"
    )


def test_challenge_body_is_recognised_and_refused(captured_at: datetime) -> None:
    assert looks_like_challenge(CHALLENGE_HTML) is True
    assert looks_like_challenge(json.dumps(_payload())) is False
    with pytest.raises(ValueError, match="challenge"):
        parse_match_calculator(CHALLENGE_HTML, observed_at=captured_at)


def test_naive_observed_at_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_match_calculator(
            json.dumps(_payload()), observed_at=datetime(2026, 9, 24, 9, 18, 37)
        )


def test_parses_both_markets_and_all_pools(captured_at: datetime) -> None:
    quotes, meta = _parse(captured_at)
    assert meta.match_count == 3
    assert len(quotes) == 3

    dutch = next(q for q in quotes if q.match_num_str == "周四006")
    assert dutch.had == (2.23, 3.56, 2.50)
    assert dutch.hhad == (4.35, 4.22, 1.51)
    assert dutch.goal_line == "-1"
    assert dutch.pools == ("crs", "had", "hafu", "hhad", "ttg")
    assert pools_of(quotes) >= {"had", "hhad", "ttg", "crs"}

    china = next(q for q in quotes if q.match_num_str == "周四003")
    assert china.had is None, "a handicap-only listing must not fabricate a 1X2"
    assert china.hhad == (2.30, 4.80, 2.06)
    assert china.goal_line == "-4"


def test_ttg_buckets_are_s0_through_s7(captured_at: datetime) -> None:
    quotes, _ = _parse(captured_at)
    dutch = next(q for q in quotes if q.match_num_str == "周四006")
    assert dutch.ttg == (21.00, 7.25, 4.30, 3.60, 4.60, 7.10, 12.00, 15.00)


def test_our_clock_is_never_overwritten_by_the_provider_clock(captured_at: datetime) -> None:
    """The whole point of the task: observed_at and provider update time are
    different facts and must survive parsing as different values."""
    quotes, meta = _parse(captured_at)
    dutch = next(q for q in quotes if q.match_num_str == "周四006")

    assert dutch.observed_at == captured_at
    assert dutch.odds_updated_at == datetime(2026, 9, 23, 9, 17, 36, tzinfo=BEIJING)
    assert dutch.odds_updated_at < dutch.observed_at
    assert meta.observed_at == captured_at
    assert meta.provider_last_update_time == datetime(2026, 9, 23, 21, 50, 41, tzinfo=BEIJING)


def test_missing_provider_time_stays_absent(captured_at: datetime) -> None:
    quotes, _ = _parse(captured_at)
    synthetic = next(q for q in quotes if q.match_num_str == "周四099")
    # every pool block in that row has no updateDate/updateTime
    assert synthetic.odds_updated_at is None
    assert synthetic.had == (1.90, 3.30, 3.60)


def test_odds_updated_at_is_the_latest_pool_stamp(captured_at: datetime) -> None:
    quotes, _ = _parse(captured_at)
    china = next(q for q in quotes if q.match_num_str == "周四003")
    # hhad moved at 09:17:36, ttg carries no stamp -> the stamp that exists wins
    assert china.odds_updated_at == datetime(2026, 9, 23, 9, 17, 36, tzinfo=BEIJING)


def test_parse_provider_time_rejects_incomplete_input() -> None:
    assert parse_provider_time(None, "09:17:36") is None
    assert parse_provider_time("2026-09-23", None) is None
    assert parse_provider_time("not-a-date", "09:17:36") is None
    assert parse_provider_time("2026-09-23", "09:17:36") == datetime(
        2026, 9, 23, 9, 17, 36, tzinfo=BEIJING
    )


def test_kickoff_is_read_as_beijing_time(captured_at: datetime) -> None:
    quotes, _ = _parse(captured_at)
    dutch = next(q for q in quotes if q.match_num_str == "周四006")
    assert dutch.kickoff_local == datetime(2026, 9, 25, 2, 45, tzinfo=BEIJING)
    assert dutch.kickoff_local.utcoffset() == timedelta(hours=8)


def test_payload_hash_is_recorded(captured_at: datetime) -> None:
    quotes, meta = _parse(captured_at)
    assert len(meta.payload_sha256) == 64
    assert {q.payload_sha256 for q in quotes} == {meta.payload_sha256}
