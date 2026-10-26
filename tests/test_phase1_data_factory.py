"""Factory regression: batch ordering, source immutability and fail-closed gates."""
import copy
import gzip
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from tools import task0017_official_only as source_schema
from tools.phase1_data_factory import build

BASE = datetime(2026, 10, 26, 4, 0, tzinfo=timezone.utc)

def match(price="2.10", provider_time="12:00:00", *, mid=100, flags="0"):
    return {
        "matchId": mid, "matchDate": "2026-10-27", "matchTime": "04:00:00",
        "homeTeamId": 11, "awayTeamId": 22, "matchStatus": "Selling", "sellStatus": 1,
        "poolList": [{"poolCode": "HAD", "poolStatus": "Selling"}],
        "had": {"h": price, "d": "3.30", "a": "3.40", "hf": flags,
                "df": "0", "af": "0", "updateDate": "2026-10-26",
                "updateTime": provider_time},
    }

def source(tmp, name, captures):
    root = tmp / name
    root.mkdir()
    con = sqlite3.connect(root / "official.sqlite3")
    con.execute(source_schema.SCHEMA)
    original = []
    for i, (when, fixture, status) in enumerate(captures, start=1):
        doc = {"success": True, "value": {"matchInfoList": [{"subMatchList": fixture}]}}
        raw = json.dumps(doc).encode()
        hash_ = hashlib.sha256(raw).hexdigest()
        rel = f"raw/20261026/{hash_}.json.gz"
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(raw))
        original.append((path, hashlib.sha256(path.read_bytes()).digest()))
        con.execute(
            """INSERT INTO captures
            (capture_id, observed_at_utc, request_url, http_status, result, match_count,
             raw_sha256, raw_path, raw_length, source_commit) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (i, when.isoformat(), "https://official.example", 200, status, len(fixture),
             hash_, rel, len(raw), "frozen123"))
    con.commit()
    con.close()
    return root, original

def test_sorted_merging_duplicate_suppression_and_output(tmp_path):
    late, originals_a = source(tmp_path, "late", [
        (BASE + timedelta(minutes=3), [match("2.50", "12:03:00")], "ok")
    ])
    early, originals_b = source(tmp_path, "early", [
        (BASE, [match()], "ok"),
        (BASE + timedelta(minutes=1), [match()], "ok")
    ])
    output = tmp_path / "factory.sqlite3"
    result = build([late, early], output)
    assert result["counts"]["captures"] == 3
    assert result["counts"]["verified_raw"] == 3
    assert result["counts"]["quote_events"] == 2
    assert result["distinct_fixtures"] == 1
    assert result["pools"]["had"]["duplicate"] == 1
    con = sqlite3.connect(output)
    entries = con.execute("SELECT event_kind, odds_json, source_root FROM quote_candidates ORDER BY id").fetchall()
    assert [x[0] for x in entries] == ["initial", "advance_change"]
    assert [x[2] for x in entries] == ["early", "late"]
    assert con.execute("SELECT COUNT(*) FROM fixtures").fetchone()[0] == 1
    con.close()
    for path, hashed in originals_a + originals_b:
        assert hashlib.sha256(path.read_bytes()).digest() == hashed
    with pytest.raises(FileExistsError):
        build([late, early], output)

def test_corrupt_source_fails_without_publishing_output(tmp_path):
    root, files = source(tmp_path, "s1", [(BASE, [match()], "ok")])
    files[0][0].write_bytes(gzip.compress(b'{"bad":"tamper"}'))
    out = tmp_path / "refused.sqlite3"
    with pytest.raises(ValueError, match="SHA256"):
        build([root], out)
    assert not out.exists()

def test_identity_conflict_fail_closed(tmp_path):
    other = match()
    other["homeTeamId"] = 99
    root, _ = source(tmp_path, "s2", [
        (BASE, [match()], "ok"),
        (BASE + timedelta(minutes=1), [other], "ok")
    ])
    out = tmp_path / "no.sqlite3"
    with pytest.raises(ValueError, match="identity changed"):
        build([root], out)
    assert not out.exists()

def test_reject_stale_nonzero_flag_and_future_while_preserving_counts(tmp_path):
    a = match(provider_time="00:00:00")  # > 6h old
    b = match(flags="1", mid=101)
    c = match(mid=102, provider_time="13:00:00") # provider future
    root, _ = source(tmp_path, "s3", [(BASE, [a, b, c], "ok")])
    result = build([root], tmp_path / "clean.sqlite3")
    assert result["counts"].get("quote_events", 0) == 0
    assert result["pools"]["had"]["stale_provider_quote"] == 1
    assert result["pools"]["had"]["flagged"] == 1
    assert result["pools"]["had"]["future_provider_time"] == 1

def test_reject_postkickoff_and_infinite_quotes(tmp_path):
    post = match(mid=104)
    post["matchDate"], post["matchTime"] = "2026-10-26", "11:30:00"
    infinite = match(price="Infinity", mid=105)
    root, _ = source(tmp_path, "s4", [(BASE, [post, infinite], "ok")])
    result = build([root], tmp_path / "clean.sqlite3")
    assert result["pools"]["had"]["at_or_after_kickoff"] == 1
    assert result["pools"]["had"]["invalid_price"] == 1
    assert result["counts"].get("quote_events", 0) == 0

def test_duplicate_match_in_single_response_refuses(tmp_path):
    root, _ = source(tmp_path, "s5", [(BASE, [match(), copy.deepcopy(match())], "ok")])
    with pytest.raises(ValueError, match="duplicate match"):
        build([root], tmp_path / "out.sqlite3")

def test_root_guards_and_bounded_scan(tmp_path):
    root, _ = source(tmp_path, "unique", [
        (BASE, [match()], "ok"), (BASE + timedelta(minutes=1), [match()], "ok")
    ])
    with pytest.raises(ValueError, match="under source"):
        build([root], root / "new.sqlite3")
    with pytest.raises(ValueError, match="unique"):
        build([root, root], tmp_path / "bad.sqlite3")
    result = build([root], tmp_path / "partial.sqlite3", max_captures=1)
    assert result["partial_scan"] and result["counts"]["captures"] == 1
