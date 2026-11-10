"""TASK0060 defensive limits: only approved new clubs, old evidence immutable."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from tools import task0043_prospective_multimodel_freeze as gate
from tools import task0046_forward_publication as pub
from tools import task0044_forward_orchestrator as post

ASSET = Path(__file__).resolve().parents[1] / "research" / (
    "task0060_verified_club_extension_20261110.json"
)
UTC = dt.timezone.utc


def original_70():
    # Disjoint, test-only mocks: historical original E evidence remains off-Git.
    return {str(100000 + i): (100000 + i, f"old_{i}") for i in range(70)}


def fake_base(monkeypatch):
    original = original_70()
    monkeypatch.setattr(gate, "frozen_team_bridge",
                        lambda path: (dict(original), gate.EXPECTED_BRIDGE_SHA))
    return original


def rewrite(path: Path, value: dict):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8")


def test_exact_pinned_addition_73_and_prior_70_are_immutable(monkeypatch):
    original = fake_base(monkeypatch)
    expanded, meta = gate.verified_extended_team_bridge(
        Path("unused-origin"), ASSET
    )
    assert len(expanded) == 143
    assert len({x[0] for x in expanded.values()}) == 143
    assert all(expanded[k] == v for k, v in original.items())
    assert meta["original_identity_ledger_sha256"] == gate.EXPECTED_BRIDGE_SHA
    assert meta["identity_extension_sha256"] == gate.TASK0060_EXTENSION_SHA
    assert meta["identity_version"] == "TASK0060_ADDITIVE_143"
    assert len(meta["identity_combined_sha256"]) == 64
    assert hashlib.sha256(ASSET.read_bytes()).hexdigest() == gate.TASK0060_EXTENSION_SHA


def test_mutated_source_bytes_rejected_without_approval(monkeypatch, tmp_path):
    fake_base(monkeypatch)
    alternate = tmp_path / "tampered.json"
    alternate.write_bytes(ASSET.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="extension SHA mismatch"):
        gate.verified_extended_team_bridge(Path("unused"), alternate)


@pytest.mark.parametrize("change,error", [
    ("duplicate_official", "duplicate/invalid"),
    ("duplicate_hf", "duplicate/invalid"),
    ("modify_count", "source review"),
    ("modify_old_sha", "source review"),
    ("missing_witness", "duplicate/invalid"),
    ("training_too_few", "duplicate/invalid"),
])
def test_repin_cannot_override_semantic_conflicts(monkeypatch, tmp_path, change, error):
    fake_base(monkeypatch)
    val = json.loads(ASSET.read_text(encoding="utf8"))
    if change == "duplicate_official":
        val["additions"][1]["official_id"] = val["additions"][0]["official_id"]
    elif change == "duplicate_hf":
        val["additions"][1]["hf_team_id"] = val["additions"][0]["hf_team_id"]
    elif change == "modify_count":
        val["additional_clubs"] += 1
    elif change == "modify_old_sha":
        val["original_bridge_sha256"] = "0" * 64
    elif change == "missing_witness":
        val["additions"][0]["witnesses"] = []
    elif change == "training_too_few":
        val["additions"][0]["minimum_pre_july_league_games"] = 0
    altered = tmp_path / "repinned.json"
    rewrite(altered, val)
    monkeypatch.setattr(gate, "TASK0060_EXTENSION_SHA",
                        hashlib.sha256(altered.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match=error):
        gate.verified_extended_team_bridge(Path("unused"), altered)


def test_same_preapproved_teams_and_unknown_names_still_rejected(monkeypatch):
    fake_base(monkeypatch)
    expanded, meta = gate.verified_extended_team_bridge(Path("unused"), ASSET)
    official_ids = [
        str(row["official_id"]) for row in
        json.loads(ASSET.read_text(encoding="utf8"))["additions"]
    ]
    first, second = official_ids[:2]
    name1 = expanded[first][1]
    name2 = expanded[second][1]
    instant = dt.datetime(2026, 11, 11, 8, tzinfo=UTC)
    source = {
        "matchId": "2990000", "leagueAbbName": "英超",
        "matchDate": "2026-11-12", "matchTime": "23:00",
        "homeTeamId": first, "awayTeamId": second,
        "homeTeamAllName": name1, "awayTeamAllName": name2,
    }
    good, rejects = gate.qualify_fixtures([source], expanded, instant)
    assert len(good) == 1 and not rejects
    wrong_name = dict(source, homeTeamAllName=name1 + "_unapproved")
    no_name, rejects = gate.qualify_fixtures([wrong_name], expanded, instant)
    assert not no_name and rejects == {"approved_team_name_conflict": 1}
    unknown = dict(source, homeTeamId="777777777")
    no_team, rejects = gate.qualify_fixtures([unknown], expanded, instant)
    assert not no_team and rejects == {"missing_preapproved_both_team_identity": 1}
    after = dt.datetime(2026, 11, 13, tzinfo=UTC)
    no_retro, rejects = gate.qualify_fixtures([source], expanded, after)
    assert not no_retro and rejects == {"not_future_at_freeze": 1}


def test_new_git_prediction_ledger_binds_both_original_and_extension_SHA():
    now = dt.datetime(2027, 2, 1, 5, tzinfo=UTC)
    kickoff = now + dt.timedelta(hours=4)
    frozen = {
        "task": "TASK0043",
        "frozen_at_utc": (now - dt.timedelta(minutes=3)).isoformat(),
        "capture": {
            "received_utc": (now - dt.timedelta(minutes=5)).isoformat(),
            "sha256": "a"*64,
            "capture_source_commit": "b"*40,
        },
        "history": {
            "last_training_date": "2026-07-04",
            "published_at_utc": "2026-07-05T01:23:18+00:00",
            "source_fixture_sha256": "c"*64,
            "source_manifest_sha256": "d"*64,
        },
        "identity_ledger_sha256": "e"*64,
        "original_identity_ledger_sha256": gate.EXPECTED_BRIDGE_SHA,
        "identity_extension_sha256": gate.TASK0060_EXTENSION_SHA,
        "identity_version": "TASK0060_ADDITIVE_143",
        "model_qualified": 1,
        "market_prices_input_to_models": False,
        "new_results_input_to_models": False,
        "no_bet_or_buy": True,
        "predictions": [{
            "matchId": "2990000", "kickoff_utc": kickoff.isoformat(),
            "official_home_id": "7", "official_away_id": "9",
            "models_1x2_home_draw_away": {
                k: [.5, .25, .25] for k in post.MODEL_KEYS
            },
        }],
    }
    # A real Git ledger stores extension source and original SHA alongside
    # the combined SHA, so later audits can unambiguously select the policy.
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        snap = Path(d)/"freeze.json"
        rewrite(snap, frozen)
        commitment = pub.build_ledger(snap, now=now, previous=[])
        for name in ("identity_extension_sha256",
                     "original_identity_ledger_sha256", "identity_version"):
            assert commitment[name] == frozen[name]
        ledger = Path(d)/"ledger.json"
        rewrite(ledger, commitment)
        post.verified_freeze(snap, ledger)
        changed = copy.deepcopy(commitment)
        changed["identity_extension_sha256"] = "0"*64
        rewrite(ledger, changed)
        with pytest.raises(ValueError, match="provenance mismatch"):
            post.verified_freeze(snap, ledger)
