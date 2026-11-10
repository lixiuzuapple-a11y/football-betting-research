"""TASK0058: old official snapshot coverage cannot become fake model forecasts."""
import collections
import datetime as dt
import gzip
import hashlib
import json
import sqlite3

import pytest

from tools import task0058_forward_supply_audit as a

UTC = dt.timezone.utc
START = dt.datetime(2026, 11, 8, 7, 0, tzinfo=UTC)
END = dt.datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
COMMIT = "a" * 40


def official(league="法甲", home="朗斯", time="19:00", *, duplicate=False):
    fixture = {
        "matchId": "2042640", "matchDate": "2026-11-08", "matchTime": time,
        "leagueAbbName": league,
        "homeTeamId": "179", "awayTeamId": "182",
        "homeTeamAllName": home, "awayTeamAllName": "马赛",
    }
    fixtures = [fixture, dict(fixture)] if duplicate else [fixture]
    return json.dumps({
        "success": True, "errorCode": 0,
        "value": {"matchInfoList": [{"subMatchList": fixtures}]},
    }, sort_keys=True).encode()


def fixture_cycle(tmp_path, *, payload=None, statuses=("ok", "ok", "transport_error"),
                  when=("2026-11-08T08:00:00Z",
                        "2026-11-08T08:30:00Z",
                        "2026-11-08T08:45:00Z")):
    root = tmp_path / "run-20261108T080000000000Z-aaaaaa"
    root.mkdir()
    payload = official() if payload is None else payload
    sha = hashlib.sha256(payload).hexdigest()
    relative = f"raw/20261108/{sha}.json.gz"
    path = root / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(gzip.compress(payload))
    (root / "CONFIG.json").write_text(json.dumps({
        "mode": "QUALIFICATION_OFFICIAL_ONLY", "url": a.ENDPOINT,
        "source_commit": COMMIT,
    }))
    (root / "CYCLE_OUTCOME.json").write_text(json.dumps({
        "task": "TASK0045", "collector_exit": 0, "sqlite": "ok",
        "source_commit": COMMIT, "captures": len(statuses),
        "status_counts": dict(collections.Counter(statuses)),
        "first_utc": when[0], "last_utc": when[-1],
    }))
    db = sqlite3.connect(root / "official.sqlite3")
    db.execute(
        "CREATE TABLE captures (capture_id INTEGER, observed_at_utc TEXT,"
        " request_url TEXT, http_status INTEGER, result TEXT,"
        " match_count INTEGER, raw_sha256 TEXT, raw_path TEXT,"
        " raw_length INTEGER, source_commit TEXT)"
    )
    for i, (status, stamp) in enumerate(zip(statuses, when), 1):
        valid = status == "ok"
        db.execute("INSERT INTO captures VALUES (?,?,?,?,?,?,?,?,?,?)", (
            i, stamp, a.ENDPOINT, 200 if valid or status == "no_offer" else None,
            status, len(json.loads(payload)["value"]["matchInfoList"][0]["subMatchList"])
            if valid else 0,
            sha if valid else None, relative if valid else None,
            len(payload) if valid else None, COMMIT,
        ))
    db.commit()
    db.close()
    bridge = tmp_path / "immutable-team-bridge.json"
    bridge.write_bytes(b"fake strict bridge")
    return root, bridge, path


def audit_fixture(root, bridge, monkeypatch):
    monkeypatch.setattr(a, "EXPECTED_BRIDGE_SHA", a.hash_file(bridge))
    monkeypatch.setattr(a, "frozen_team_bridge", lambda _: (
        {"179": (123, "朗斯"), "182": (456, "马赛")}, a.hash_file(bridge)
    ))
    return a.audit_runs([root], bridge, first_utc=START, last_utc=END)


def test_original_sha_checked_and_repeated_captures_not_independent(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path)
    result = audit_fixture(root, bridge, monkeypatch)
    assert result["completed_runs_used"] == 1
    assert result["source_captures_observed"] == 3
    assert result["verified_captures"] == 2
    assert result["unusable_source_captures"] == 1
    assert result["unique_fixture_ids_any_status"] == 1
    assert result["unique_fixture_ids_observed_before_kickoff"] == 1
    assert result["unique_ids_in_approved_leagues_before_kickoff"] == 1
    assert result["unique_ids_strict_identity_and_league_preapproved"] == 1
    assert result["eligible_observation_windows"]["2042640"]["observations"] == 2
    assert result["by_beijing_date"]["2026-11-08"]["unusable_capture_count"] == 1


def test_nonapproved_league_cannot_be_promoted_by_repeated_observations(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path, payload=official(league="德甲"))
    result = audit_fixture(root, bridge, monkeypatch)
    assert result["unique_ids_in_approved_leagues_before_kickoff"] == 0
    assert result["unique_ids_strict_identity_and_league_preapproved"] == 0
    assert result["by_beijing_date"]["2026-11-08"]["rejection_observations"][
        "league_not_approved_for_forward_model"
    ] == 2


def test_approved_league_but_wrong_team_identity_cannot_qualify(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path, payload=official(home="错译队名"))
    result = audit_fixture(root, bridge, monkeypatch)
    assert result["unique_ids_in_approved_leagues_before_kickoff"] == 1
    assert result["unique_ids_strict_identity_and_league_preapproved"] == 0
    assert result["by_beijing_date"]["2026-11-08"]["rejection_observations"][
        "approved_team_name_conflict"
    ] == 2


def test_finished_match_cannot_qualify_as_prospective(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path, payload=official(time="14:00"))
    result = audit_fixture(root, bridge, monkeypatch)
    assert result["unique_fixture_ids_observed_before_kickoff"] == 0
    assert result["unique_ids_strict_identity_and_league_preapproved"] == 0


def test_corrupted_raw_sha_fails_closed(tmp_path, monkeypatch):
    root, bridge, path = fixture_cycle(tmp_path)
    path.write_bytes(gzip.compress(b'{"success":true}'))
    with pytest.raises(ValueError, match="source bytes/SHA mismatch"):
        audit_fixture(root, bridge, monkeypatch)


def test_duplicate_ids_in_one_official_page_fails(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path, payload=official(duplicate=True))
    with pytest.raises(ValueError, match="duplicate official fixture"):
        audit_fixture(root, bridge, monkeypatch)


def test_corrupt_source_path_rejected_before_read(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path)
    db = sqlite3.connect(root / "official.sqlite3")
    db.execute("UPDATE captures SET raw_path = '../outside.json.gz' WHERE capture_id = 1")
    db.commit()
    db.close()
    with pytest.raises(ValueError, match="unsafe source path"):
        audit_fixture(root, bridge, monkeypatch)


def test_same_file_with_conflicting_sha_metadata_rejected(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path)
    db = sqlite3.connect(root / "official.sqlite3")
    db.execute("UPDATE captures SET raw_sha256 = ? WHERE capture_id=2", ("e" * 64,))
    db.commit()
    db.close()
    with pytest.raises(ValueError, match="conflicting SHA"):
        audit_fixture(root, bridge, monkeypatch)


def test_tampered_collector_summary_rejected(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path)
    outcome = json.loads((root / "CYCLE_OUTCOME.json").read_text())
    outcome["captures"] += 1
    (root / "CYCLE_OUTCOME.json").write_text(json.dumps(outcome))
    with pytest.raises(ValueError, match="count disagrees"):
        audit_fixture(root, bridge, monkeypatch)


def test_untrusted_team_bridge_sha_rejected(tmp_path):
    root, bridge, _ = fixture_cycle(tmp_path)
    with pytest.raises(ValueError, match="mapping SHA changed"):
        a.audit_runs([root], bridge, first_utc=START, last_utc=END)


def test_no_offer_is_valid_observation_but_no_fixture(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(
        tmp_path, statuses=("no_offer",), when=("2026-11-08T08:00:00Z",)
    )
    result = audit_fixture(root, bridge, monkeypatch)
    assert result["verified_captures"] == 1
    assert result["unique_fixture_ids_any_status"] == 0
    assert result["unique_ids_strict_identity_and_league_preapproved"] == 0


def test_no_completed_or_out_of_window_cannot_claim_coverage(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path)
    monkeypatch.setattr(a, "EXPECTED_BRIDGE_SHA", a.hash_file(bridge))
    monkeypatch.setattr(a, "frozen_team_bridge", lambda _: ({}, a.hash_file(bridge)))
    with pytest.raises(ValueError, match="no completed official collector"):
        a.audit_runs([root], bridge,
                     first_utc=dt.datetime(2026, 11, 10, tzinfo=UTC),
                     last_utc=dt.datetime(2026, 11, 11, tzinfo=UTC))


def test_naive_time_or_invalid_interval_rejected(tmp_path, monkeypatch):
    root, bridge, _ = fixture_cycle(tmp_path)
    monkeypatch.setattr(a, "EXPECTED_BRIDGE_SHA", a.hash_file(bridge))
    with pytest.raises(ValueError, match="bounded UTC"):
        a.audit_runs([root], bridge, first_utc=END, last_utc=START)
    with pytest.raises(ValueError, match="naive"):
        a.as_utc("2026-11-10T11:15:00")
