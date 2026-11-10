"""Source catalog/alias guard and prospective odds timing adversarial checks."""
import copy
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from tools import task0061_club_registry as registry
from tools import task0061_same_time_odds as audit


def fixture():
    frozen = "2026-11-08T07:14:16Z"
    model = {
        "record_schema": "EVLAB_TASK0046_FORWARD_V1",
        "status": "PRE_KICKOFF_FROZEN_RESEARCH_ONLY",
        "frozen_at_utc": frozen,
        "market_quote_status": "UNVERIFIED_NOT_INCLUDED",
        "market_odds": None,
        "predictions": [{
            "matchId": "2042640", "official_home_id": "179",
            "official_away_id": "182", "hf_home_id": 214, "hf_away_id": 209,
            "league": "法甲", "kickoff_utc": "2026-11-08T19:45:00Z",
        }],
    }
    source = [{
        "id": "ev_123", "sport_key": "soccer_france_ligue_one",
        "commence_time": "2026-11-08T19:45:00Z",
        "home_team": "Lens", "away_team": "Marseille",
        "bookmakers": [{
            "key": "book_test",
            "last_update": "2026-11-08T07:10:00Z",
            "markets": [{
                "key": "h2h", "last_update": "2026-11-08T07:10:00Z",
                "outcomes": [
                    {"name": "Lens", "price": 2.06},
                    {"name": "Draw", "price": 3.94},
                    {"name": "Marseille", "price": 3.20},
                ],
            }],
        }],
    }]
    body = json.dumps(source, sort_keys=True).encode()
    candidate = {
        "official_match_id": "2042640", "provider_event_id": "ev_123",
        "sport_key": "soccer_france_ligue_one",
        "bookmaker_key": "book_test", "period": "FULL_TIME_90",
        "market_key": "h2h",
        "identity_bridge": {
            "status": "INDEPENDENT_TWO_SIDE_EVENT_ACCEPTED",
            "official_match_id": "2042640", "provider_event_id": "ev_123",
            "official_home_id": "179", "official_away_id": "182",
            "hf_home_id": 214, "hf_away_id": 209,
            "league_zh": "法甲", "kickoff_utc": "2026-11-08T19:45:00Z",
            "provider_home_team": "Lens", "provider_away_team": "Marseille",
            "evidence_sha256": "f" * 64,
        },
        "receipt": {
            "http_status": 200, "source_provider": "the-odds-api",
            "source_url": "https://api.the-odds-api.com/v4/sports/soccer/odds",
            "first_received_utc": "2026-11-08T07:11:00Z",
            "git_anchor_time_utc": "2026-11-08T07:12:00Z",
            "raw_sha256": hashlib.sha256(body).hexdigest(),
        },
    }
    return model, candidate, body


def fails(model, candidate, raw, reason):
    with pytest.raises(audit.RejectedEvidence) as err:
        audit.evaluate(model, candidate, raw)
    assert err.value.reason == reason


def test_qualifies_only_synthetic_full_1x2_same_time_pre_model_book():
    model, candidate, raw = fixture()
    result = audit.evaluate(model, candidate, raw)
    assert result["status"].startswith("SAME_MATCH_SAME_TIME_SOURCE_GATE_ACCEPTED")
    assert len(result["devigged_market_1x2"]) == 3
    assert sum(result["devigged_market_1x2"]) == pytest.approx(1.0)
    assert result["not_tradeable_profit_or_CLV_proof"] is True


def test_unverified_team_bridge_never_auto_promoted():
    m, c, b = fixture()
    c["identity_bridge"]["status"] = "FUZZY_SCORE_99_PERCENT"
    fails(m, c, b, "CROSS_PROVIDER_IDENTITY_NOT_INDEPENDENTLY_APPROVED")


def test_one_side_market_provider_home_team_reversal_rejected():
    m, c, b = fixture()
    source = json.loads(b)
    source[0]["home_team"], source[0]["away_team"] = (
        source[0]["away_team"], source[0]["home_team"],
    )
    bad = json.dumps(source).encode()
    c["receipt"]["raw_sha256"] = hashlib.sha256(bad).hexdigest()
    fails(m, c, bad, "MARKET_HOME_AWAY_REVERSED_OR_UNKNOWN")


def test_quoted_data_captured_after_model_freeze_rejected():
    m, c, b = fixture()
    c["receipt"]["first_received_utc"] = "2026-11-08T07:16:00Z"
    c["receipt"]["git_anchor_time_utc"] = "2026-11-08T07:17:00Z"
    fails(m, c, b, "MARKET_CAPTURE_NOT_GIT_ANCHORED_BEFORE_MODEL")


def test_market_received_before_model_but_too_old_rejected():
    m, c, b = fixture()
    c["receipt"]["first_received_utc"] = "2026-11-08T06:11:00Z"
    c["receipt"]["git_anchor_time_utc"] = "2026-11-08T06:12:00Z"
    fails(m, c, b, "MARKET_QUOTE_NOT_AT_MODEL_TIME")


def test_old_bookmaker_quote_rejected_even_if_scraped_recently():
    m, c, b = fixture()
    source = json.loads(b)
    source[0]["bookmakers"][0]["markets"][0]["last_update"] = (
        "2026-11-01T06:01:00Z"
    )
    bad = json.dumps(source).encode()
    c["receipt"]["raw_sha256"] = hashlib.sha256(bad).hexdigest()
    fails(m, c, bad, "BOOKMAKER_PRICE_STALE_AT_MODEL_TIME")


def test_missing_original_bookmaker_response_never_valid():
    m, c, b = fixture()
    fails(m, c, None, "RAW_MARKET_RESPONSE_NOT_PRESERVED")


def test_source_raw_sha_mutation_rejected():
    m, c, b = fixture()
    fails(m, c, b + b" ", "MARKET_RAW_SOURCE_SHA_MISMATCH")


def test_model_market_leakage_is_rejected():
    m, c, b = fixture()
    m["market_odds"] = [2, 4, 3]
    fails(m, c, b, "FORECAST_CONTAMINATED_BY_MARKET_INPUT")


def test_full_1x2_market_required_not_two_way_moneyline():
    m, c, b = fixture()
    source = json.loads(b)
    source[0]["bookmakers"][0]["markets"][0]["outcomes"].pop(1)
    bad = json.dumps(source).encode()
    c["receipt"]["raw_sha256"] = hashlib.sha256(bad).hexdigest()
    fails(m, c, bad, "INCOMPLETE_OR_MISLABELED_1X2")


def test_market_only_proposal_cannot_claim_independent_provenance():
    m, c, b = fixture()
    c["identity_bridge"]["evidence_sha256"] = ""
    fails(m, c, b, "CROSS_PROVIDER_IDENTITY_NOT_INDEPENDENTLY_APPROVED")


def test_quote_capture_without_pre_model_git_anchor_rejected():
    m, c, b = fixture()
    c["receipt"]["git_anchor_time_utc"] = "2026-11-08T07:15:00Z"
    fails(m, c, b, "MARKET_CAPTURE_NOT_GIT_ANCHORED_BEFORE_MODEL")


def test_historical_club_source_alias_is_never_an_approved_bookmaker_alias():
    assert registry.TYPE_MARKER.search("Real Madrid B")
    assert registry.TYPE_MARKER.search("Chelsea Women")
    assert registry.TYPE_MARKER.search("Ajax U21")
    assert not registry.TYPE_MARKER.search("Bayer Leverkusen")
    assert not registry.TYPE_MARKER.search("Manchester City")


def test_unapproved_market_page_candidate_reports_rejection_not_success(tmp_path):
    m, c, b = fixture()
    c["identity_bridge"]["status"] = "PUBLISHED_PAGE_UNVERIFIED"
    c["receipt"] = {
        "source_url": "https://tipsaudit.com/match/15694/lens-vs-marseille-2026-11-08",
        "source_provider": "tipsaudit_public_web_page",
        "first_received_utc": "2026-11-10T07:00:00Z",
    }
    path_m = tmp_path / "model.json"
    path_c = tmp_path / "candidate.json"
    path_m.write_text(json.dumps(m))
    path_c.write_text(json.dumps([c]))
    res = audit.audit(path_m, path_c, tmp_path)
    assert res["candidates_seen"] == 1
    assert res["contemporaneous_markets_accepted"] == 0
    assert res["results"][0]["reason"] == "CROSS_PROVIDER_IDENTITY_NOT_INDEPENDENTLY_APPROVED"


def test_archived_registry_v1_is_complete_and_sha_immutable():
    folder = Path(__file__).resolve().parents[1] / "research/registry/v1-20261110"
    doc = json.loads((folder/"registry_manifest.json").read_text(encoding="utf8"))
    assert doc["approved_leagues"] == 14
    assert doc["master_distinct_hf_keys"] == 501
    assert doc["league_membership_rows"] == 605
    assert doc["published_verified_club_keys"] == 143
    assert doc["unverified_master_clubs"] == 358
    assert doc["never_auto_accept_by_similarity"] is True
    assert doc["not_current_2026_27_roster"] is True
    for name, record in doc["files"].items():
        path = folder/name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
        with path.open(encoding="utf-8", newline="") as stream:
            assert sum(1 for _ in csv.DictReader(stream)) == record["rows"]


def test_hist_only_teams_have_no_promoted_official_ids():
    path = (Path(__file__).resolve().parents[1] /
            "research/registry/v1-20261110/team_master.csv")
    with path.open(encoding="utf8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 501
    unapproved = [x for x in rows if x["mapping_status"] ==
                  "HF_HISTORY_ONLY_UNVERIFIED"]
    approved = [x for x in rows if x["mapping_status"] ==
                "VERIFIED_PUBLISHED"]
    assert len(unapproved) == 358 and len(approved) == 143
    assert all(not x["official_team_id"] and not x["official_name_zh"]
               for x in unapproved)
    assert len({int(x["hf_team_id"]) for x in approved}) == 143
