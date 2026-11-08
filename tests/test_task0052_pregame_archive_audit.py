"""TASK0052 archive provenance gates, deterministic, no network or bookmaker API."""
import datetime as dt
import hashlib
import json

import pytest

from tools import task0052_pregame_archive_audit as audit


def market(**overrides):
    base = {
        "id": "7", "kickoff_utc": "2026-06-22T18:00:00+00:00",
        "home": "Derry City", "away": "Bohemians",
        "record_hash": "0123456789abcdef", "result": "1",
    }
    return base | overrides


def archived(**overrides):
    base = {
        "id": 7, "kickoff_utc": "2026-06-22T18:00:00+00:00",
        "home": "Derry City", "away": "Bohemians",
        "hash": "0123456789abcdef",
    }
    return base | overrides


def snapshot(day, values):
    return {
        "generated_at": audit.as_utc(day),
        "archive_name": "test-snapshot.json", "sha256": "a" * 64,
        "by_id": {str(x["id"]): x for x in values},
    }


def test_archive_row_is_not_disambiguated_using_results():
    assert audit.row_matches_archived_identity(market(result="2"), archived())
    assert not audit.row_matches_archived_identity(
        market(), archived(away="Bohemians FC")
    )
    assert not audit.row_matches_archived_identity(
        market(), archived(kickoff_utc="2026-06-22T19:00:00+00:00")
    )
    assert not audit.row_matches_archived_identity(
        market(), archived(hash="not-hex")
    )


def test_earliest_pre_match_snapshot_is_mandatory_even_if_later_hash_agrees():
    earlier = snapshot("2026-06-21T05:00:00Z", [
        archived(hash="fedcba9876543210")
    ])
    later = snapshot("2026-06-22T05:00:00Z", [archived()])
    result, evidence = audit.classify(market(), [earlier, later])
    assert result == "ARCHIVED_HASH_CHANGED_IN_LATER_CSV"
    assert evidence["initial_hash"] == "fedcba9876543210"
    assert evidence["later_hash"] == "0123456789abcdef"


def test_time_tie_or_after_kickoff_never_qualifies():
    same_time = snapshot("2026-06-22T18:00:00Z", [archived()])
    result, evidence = audit.classify(market(), [same_time])
    assert result == "NO_SNAPSHOT_BEFORE_KICKOFF" and evidence is None
    result, evidence = audit.classify(market(), [
        snapshot("2026-06-22T19:00:00Z", [archived()])
    ])
    assert result == "NO_SNAPSHOT_BEFORE_KICKOFF" and evidence is None


def test_missing_and_equal_archive_row_paths():
    earlier = snapshot("2026-06-22T05:00:00Z", [archived(id=8)])
    assert audit.classify(market(), [earlier])[0] == "ROW_ABSENT_FROM_PREMATCH_ARCHIVES"
    earlier = snapshot("2026-06-22T05:00:00Z", [archived()])
    state, evidence = audit.classify(market(), [earlier])
    assert state == "PREMATCH_ARCHIVE_ROW_HASH_EQUAL"
    assert evidence["initial_hash"] == "0123456789abcdef"


def test_no_naive_or_out_of_order_timestamps():
    for invalid in ("2026-06-20T12:00:00", "not-a-timestamp"):
        with pytest.raises(ValueError):
            audit.as_utc(invalid)
    assert audit.as_utc("2026-06-20T10:00:00+02:00") == (
        dt.datetime(2026, 6, 20, 8, 0, tzinfo=dt.timezone.utc)
    )


def save_fixture(tmp_path, *, rows=None, generated="2026-06-21T04:40:02+00:00",
                 declared_count=None, name="track-2026-06-21T04-40-01Z.json"):
    if rows is None:
        rows = [archived()]
    content = {
        "generated_at": generated,
        "count": len(rows) if declared_count is None else declared_count,
        "predictions": rows,
    }
    raw = (json.dumps(content) + "\n").encode()
    (tmp_path / name).write_bytes(raw)
    sha = hashlib.sha256(raw).hexdigest()
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "snapshot_utc,sha256,predictions,ots\n"
        f"2026-06-21T04-40-01Z,{sha},1,data/{name}.ots\n",
        encoding="utf-8",
    )
    return manifest, hashlib.sha256(manifest.read_bytes()).hexdigest()


def test_manifest_snapshot_sha_count_time_are_verified(tmp_path):
    manifest, sha = save_fixture(tmp_path)
    found = audit.discover_archives(manifest, tmp_path, manifest_sha=sha)
    assert len(found) == 1
    assert found[0]["by_id"]["7"]["hash"] == "0123456789abcdef"
    with pytest.raises(ValueError, match="manifest SHA"):
        audit.discover_archives(manifest, tmp_path, manifest_sha="a" * 64)
    with pytest.raises(ValueError, match="archive SHA"):
        (tmp_path / "track-2026-06-21T04-40-01Z.json").write_text("tampered")
        audit.discover_archives(manifest, tmp_path, manifest_sha=sha)


def test_snapshot_count_mismatch_is_rejected(tmp_path):
    manifest, sha = save_fixture(tmp_path, declared_count=2)
    with pytest.raises(ValueError, match="prediction count"):
        audit.discover_archives(manifest, tmp_path, manifest_sha=sha)


def test_snapshot_day_mismatch_is_rejected(tmp_path):
    manifest, sha = save_fixture(tmp_path, generated="2026-06-22T04:40:02Z")
    with pytest.raises(ValueError, match="generation day"):
        audit.discover_archives(manifest, tmp_path, manifest_sha=sha)


def test_snapshot_duplicate_ids_rejected(tmp_path):
    manifest, sha = save_fixture(tmp_path, rows=[archived(), archived()])
    with pytest.raises(ValueError, match="duplicate predictor"):
        audit.discover_archives(manifest, tmp_path, manifest_sha=sha)


def test_snapshot_duplicate_filenames_rejected(tmp_path):
    manifest, sha = save_fixture(tmp_path)
    lines = manifest.read_text()
    manifest.write_text(lines + lines.splitlines()[-1] + "\n")
    newsha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="duplicate/unsafe"):
        audit.discover_archives(manifest, tmp_path, manifest_sha=newsha)


def test_tampered_fixture_names_are_not_hash_qualified():
    bad = archived(home="Fake FC")
    status, evidence = audit.classify(market(), [
        snapshot("2026-06-21T04:40:02Z", [bad])
    ])
    assert status == "ARCHIVED_FIXTURE_IDENTITY_OR_HASH_INVALID"
    assert evidence is None
