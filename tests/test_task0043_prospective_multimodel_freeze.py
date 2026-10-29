"""TASK0043 safeguards: market separation, time gates and approved identities."""
import datetime as dt
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from tools.phase3_multimodel_walkforward import Game, Scheduled, State
from tools.task0017_official_only import SCHEMA, ENDPOINT
from tools.task0043_prospective_multimodel_freeze import (
    load_capture, qualify_fixtures, model_fixtures, frozen_team_bridge,
)

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 10, 29, 8, 0, tzinfo=UTC)


def fixture(*, odds="2.00", kickoff="2026-10-31", home="博德闪耀",
            away="维京", league="挪超"):
    return {
        "matchId": "2042359", "matchDate": kickoff, "matchTime": "02:00:00",
        "leagueAbbName": league, "homeTeamId": "618", "awayTeamId": "613",
        "homeTeamAllName": home, "awayTeamAllName": away,
        "had": {"h": odds, "d": "3.50", "a": "3.50"},
        "score": [0, 88],  # hostile result-shaped value must never reach prediction
    }


def source(tmp_path: Path, *, received: dt.datetime = NOW - dt.timedelta(minutes=2),
           payload: dict | None = None):
    root = tmp_path / "raw_official"
    root.mkdir(parents=True)
    cfg = {
        "mode": "QUALIFICATION_OFFICIAL_ONLY", "url": ENDPOINT,
        "max_rounds": 1, "source_commit": "a" * 40,
        "created_at_utc": (received - dt.timedelta(seconds=1)).isoformat(),
    }
    (root / "CONFIG.json").write_text(json.dumps(cfg))
    doc = payload or {"success": True, "errorCode": 0, "value": {
        "matchInfoList": [{"subMatchList": [fixture()]}]}}
    raw = json.dumps(doc, ensure_ascii=False).encode("utf8")
    sha = hashlib.sha256(raw).hexdigest()
    rel = f"raw/20261029/{sha}.json.gz"
    p = root / rel
    p.parent.mkdir(parents=True)
    p.write_bytes(gzip.compress(raw, mtime=0))
    con = sqlite3.connect(root / "official.sqlite3")
    con.execute(SCHEMA)
    con.execute(
        """INSERT INTO captures (capture_id,observed_at_utc,request_url,
           http_status,result,match_count,raw_sha256,raw_path,raw_length,source_commit)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (1, received.isoformat(), ENDPOINT, 200, "ok", 1,
         sha, rel, len(raw), "a" * 40),
    )
    con.commit()
    con.close()
    return root, p


def seeded_state() -> State:
    s = State()
    ids = (569, 564, 8000, 8001)
    for i in range(60):
        # Many distinct actual-historical-pattern fixtures ensure 25+ league
        # matches and both teams' proper home/away histories.
        g = Game(i+1, dt.date(2025, 7, 1) + dt.timedelta(days=i),
                 dt.datetime(2025, 7, 1) + dt.timedelta(days=i),
                 23, ids[i % 4], ids[(i+1) % 4], (i % 3), ((i+1) % 3))
        s.add_training(g)
    return s


def approved():
    return {"618": (569, "博德闪耀"), "613": (564, "维京")}


def test_scheduled_input_has_no_score_or_odds_and_models_predict():
    assert not hasattr(Scheduled(23, 569, 564), "gh")
    assert not hasattr(Scheduled(23, 569, 564), "odds")
    selected, rejected = qualify_fixtures([fixture()], approved(), NOW)
    assert len(selected) == 1 and not rejected
    output, blocked = model_fixtures(selected, seeded_state())
    assert not blocked and len(output) == 1
    assert set(output[0]["models_1x2_home_draw_away"]) == {
        "global_frequency", "league_frequency", "pooled_elo_davidson",
        "league_poisson",
    }


def test_market_odds_and_fake_result_do_not_change_independent_probs():
    state = seeded_state()
    a, _ = qualify_fixtures([fixture(odds="1.10")], approved(), NOW)
    b, _ = qualify_fixtures([fixture(odds="300.00")], approved(), NOW)
    # Scores and odds can vary in provider documents without entering model request.
    x = fixture(odds="300.00")
    x["score"] = [999, 0]
    c, _ = qualify_fixtures([x], approved(), NOW)
    p1, _ = model_fixtures(a, state)
    p2, _ = model_fixtures(b, state)
    p3, _ = model_fixtures(c, state)
    assert p1 == p2 == p3


def test_fail_closed_unapproved_identifiers_names_and_leagues():
    a, bad = qualify_fixtures([fixture(home="完全不同")], approved(), NOW)
    assert not a and bad == {"approved_team_name_conflict": 1}
    a, bad = qualify_fixtures([fixture(league="欧冠")], approved(), NOW)
    assert not a and bad == {"league_not_approved_for_forward_model": 1}
    a, bad = qualify_fixtures([fixture()], {"618": approved()["618"]}, NOW)
    assert not a and bad == {"missing_preapproved_both_team_identity": 1}
    a, bad = qualify_fixtures([fixture(kickoff="2026-10-28")], approved(), NOW)
    assert not a and bad == {"not_future_at_freeze": 1}


def test_real_official_single_raw_sha_parses_and_is_read_only(tmp_path):
    root, p = source(tmp_path)
    before = hashlib.sha256((root / "official.sqlite3").read_bytes()).hexdigest()
    records, provenance = load_capture(root, NOW)
    assert len(records) == 1 and provenance["fixture_count"] == 1
    assert provenance["sha256"] == hashlib.sha256(gzip.open(p,"rb").read()).hexdigest()
    assert hashlib.sha256((root / "official.sqlite3").read_bytes()).hexdigest() == before


def test_raw_mutation_rejected(tmp_path):
    root, path = source(tmp_path)
    path.write_bytes(gzip.compress(b"{}", mtime=0))
    with pytest.raises(ValueError, match="SHA/byte"):
        load_capture(root, NOW)


def test_future_or_stale_capture_refused(tmp_path):
    future, _ = source(tmp_path / "future", received=NOW + dt.timedelta(seconds=5))
    with pytest.raises(ValueError, match="future-dated or stale"):
        load_capture(future, NOW)
    old, _ = source(tmp_path / "old", received=NOW - dt.timedelta(hours=7))
    with pytest.raises(ValueError, match="future-dated or stale"):
        load_capture(old, NOW)


def test_duplicate_official_fixture_in_same_capture_fails(tmp_path):
    m = fixture()
    doc = {"success": True, "value": {"matchInfoList": [
        {"subMatchList": [m, m]}]}}
    root, _ = source(tmp_path, payload=doc)
    with pytest.raises(ValueError, match="count/identity"):
        load_capture(root, NOW)


def test_unapproved_identity_file_sha_rejected(tmp_path):
    path = tmp_path / "identity.json"
    path.write_text(json.dumps({"accepted": [], "new_unique_cup_identity": 35}))
    with pytest.raises(ValueError, match="approved identity ledger changed"):
        frozen_team_bridge(path)
