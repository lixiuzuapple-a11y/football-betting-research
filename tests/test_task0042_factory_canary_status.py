"""TASK-0042: real canary statuses must survive the existing official factory."""
import gzip
import hashlib
import json
import sqlite3

import pytest

from tools.phase1_data_factory import build
from tools.task0017_official_only import SCHEMA

TIMES = [
    "2026-10-27T02:44:06+00:00",
    "2026-10-27T02:46:06+00:00",
    "2026-10-27T02:48:06+00:00",
    "2026-10-27T02:50:06+00:00",
]
NO_OFFER = {"success": True, "value": {"vtoolsConfig": {
    "offLineSaleStatus": 1, "onLineSaleStatus": 1,
    "onLineStopMessage": "抱歉，本彩种已停止销售"}}}
MATCH = {"matchId": 123, "matchDate": "2026-10-28", "matchTime": "04:00:00",
         "homeTeamId": 1, "awayTeamId": 2, "matchStatus": "Selling",
         "sellStatus": 1, "poolList": [{"poolCode": "HAD", "poolStatus": "Selling"}],
         "had": {"h": "2.10", "d": "3.10", "a": "3.40", "hf": "0",
                 "df": "0", "af": "0", "updateDate": "2026-10-27",
                 "updateTime": "10:45:00"}}


def make_canary(tmp_path):
    root = tmp_path / "captured"
    root.mkdir()
    con = sqlite3.connect(root / "official.sqlite3")
    con.execute(SCHEMA)
    entries = [("no_offer", NO_OFFER), ("no_offer", NO_OFFER),
               ("transport_error", None),
               ("ok", {"success": True, "value": {
                   "matchInfoList": [{"subMatchList": [MATCH]}]}})]
    for i, (state, data) in enumerate(entries, 1):
        raw = json.dumps(data, ensure_ascii=False).encode() if data else None
        sha = hashlib.sha256(raw).hexdigest() if raw else None
        rel = f"raw/20261027/{sha}.json.gz" if sha else None
        if raw:
            path = root / rel
            path.parent.mkdir(exist_ok=True, parents=True)
            if not path.exists():
                path.write_bytes(gzip.compress(raw, mtime=0))
        con.execute(
            """INSERT INTO captures
               (capture_id,observed_at_utc,request_url,http_status,result,
                match_count,raw_sha256,raw_path,raw_length,error,source_commit)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (i, TIMES[i-1], "https://official.example",
             200 if raw else None, state, 1 if state == "ok" else 0,
             sha, rel, len(raw) if raw else None,
             "IncompleteRead" if not raw else None, "frozen"))
    con.commit()
    con.close()
    return root


def test_no_offer_then_transport_failure_then_ok_is_importable(tmp_path):
    root = make_canary(tmp_path)
    before = hashlib.sha256((root / "official.sqlite3").read_bytes()).hexdigest()
    result = build([root], tmp_path / "candidate.sqlite3")
    assert result["counts"]["captures"] == 4
    assert result["counts"]["result_no_offer"] == 2
    assert result["counts"]["result_transport_error"] == 1
    assert result["counts"]["result_ok"] == 1
    assert result["counts"]["verified_raw"] == 3
    assert result["counts"]["quote_events"] == 1
    assert result["distinct_fixtures"] == 1
    assert hashlib.sha256((root / "official.sqlite3").read_bytes()).hexdigest() == before


def test_no_offer_source_sha_tamper_fails_closed(tmp_path):
    root = make_canary(tmp_path)
    first = next((root / "raw").rglob("*.gz"))
    first.write_bytes(gzip.compress(b"{}", mtime=0))
    output = tmp_path / "not_created.sqlite3"
    with pytest.raises(ValueError, match="SHA256"):
        build([root], output)
    assert not output.exists()
