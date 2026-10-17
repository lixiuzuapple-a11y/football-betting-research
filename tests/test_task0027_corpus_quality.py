import gzip
import hashlib
import json
import sqlite3

import pytest

from tools.task0027_corpus_quality import audit, POOLS


def test_quality_audit_replay_and_coverage(tmp_path):
    root = tmp_path / "run"
    root.mkdir()
    db = sqlite3.connect(root / "official.sqlite3")
    db.execute("create table captures (capture_id integer primary key,observed_at_utc text,result text,raw_sha256 text,raw_path text)")
    for i, odds in enumerate(("1.9", "2.0", "1.9"), 1):
        doc = {"value": {"matchInfoList": [{"subMatchList": [{"matchId": "42", "had": {"h": odds}}]}]}}
        body = json.dumps(doc).encode()
        sha = hashlib.sha256(body).hexdigest()
        name = f"{i}.json.gz"
        with gzip.open(root / name, "wb") as f:
            f.write(body)
        db.execute("insert into captures values (?,?,?,?,?)", (i, f"2026-10-17T00:0{i}:00+00:00", "ok", sha, name))
    db.execute("insert into captures values (?,?,?,?,?)", (4, "2026-10-17T00:04:00+00:00", "transport_error", None, None))
    db.commit()
    db.close()
    r = audit([root])
    assert r["distinct_matches"] == 1
    assert r["total_match_observations"] == 3
    assert r["pool_diagnostics"]["had"]["raw_field_transitions"] == 2
    assert r["pool_diagnostics"]["had"]["returns_to_earlier_seen_state"] == 1
    assert r["run_stats"][0]["counts"]["transport_error"] == 1
    assert r["outcome_results_verified"] == 0


def test_tampered_raw_rejected(tmp_path):
    root = tmp_path
    c = sqlite3.connect(root / "official.sqlite3")
    c.execute("create table captures (capture_id integer primary key,observed_at_utc text,result text,raw_sha256 text,raw_path text)")
    with gzip.open(root / "data.gz", "wb") as f:
        f.write(b"{}")
    c.execute("insert into captures values (1, '2026-10-17T00:00:00+00:00', 'ok', 'bad', 'data.gz')")
    c.commit()
    c.close()
    with pytest.raises(ValueError, match="hash mismatch"):
        audit([root])
