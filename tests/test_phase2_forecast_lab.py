"""Phase2 predictor: no score leakage, no market contamination, real freeze contract."""
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from tools.phase2_forecast_lab import build_forecast, score_frozen, _create_only

UTC = dt.timezone.utc
AT = dt.datetime(2026, 10, 26, 9, 0, tzinfo=UTC)
RECEIVED = AT - dt.timedelta(minutes=4)


def prior(path: Path, *, future=False):
    day = "2026-10-27" if future else "2026-10-10"
    rows = [{
        "matchId": str(i), "matchDate": day,
        "source": "sporttery_official_result_api",
        "matchResultStatus": "2", "homeTeamId": str(i+300),
        "awayTeamId": str(i+600), "score": [i % 4, (i+1) % 3],
        "sectionsNo999": f"{i % 4}:{(i+1) % 3}",
    } for i in range(25)]
    path.write_text(json.dumps(rows), encoding="utf8")
    return path


def manifest(root: Path, *, h="2.1", status="Selling", response=RECEIVED):
    root.mkdir(parents=True, exist_ok=True)
    bjt = dt.timezone(dt.timedelta(hours=8))
    kick = (AT + dt.timedelta(hours=10)).astimezone(bjt)
    match = {
        "matchId": 3000, "matchDate": kick.date().isoformat(),
        "matchTime": kick.strftime("%H:%M:%S"), "leagueAbbName": "Test League",
        "homeTeamId": 12, "awayTeamId": 34,
        "matchStatus": status, "sellStatus": 1,
        "poolList": [{"poolCode": "HAD", "poolStatus": "Selling"}],
        "had": {
            "h": h, "d": "3.2", "a": "3.5",
            "hf": "0", "df": "0", "af": "0",
            "updateDate": response.astimezone(bjt).date().isoformat(),
            "updateTime": response.astimezone(bjt).strftime("%H:%M:%S"),
        }
    }
    raw = json.dumps({"success": True, "errorCode": 0, "value": {
        "matchInfoList": [{"subMatchList": [match]}]
    }}).encode()
    src = root/"sporttery-test.json"
    src.write_bytes(raw)
    evidence = {
        "http_status": 200, "raw_filename": src.name,
        "raw_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "group_count": 1, "fixture_count": 1,
        "request_started_at_utc": (response-dt.timedelta(seconds=1)).isoformat(),
        "response_received_at_utc": response.isoformat(),
        "url": "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry",
    }
    m = root/"test-manifest.json"
    m.write_text(json.dumps(evidence), encoding="utf8")
    return m


def test_forward_frozen_probability_and_market_separation(tmp_path):
    lab = build_forecast(labels=prior(tmp_path/"labels.json"),
                         quote_manifest=manifest(tmp_path/"src"), at=AT)
    assert lab["labels_count"] == 25
    assert lab["no_future_results_joined"] and lab["model_input_market_odds"] is False
    row = lab["fixtures"][0]
    assert len(row["independent_1x2"]) == 3
    assert sum(row["independent_1x2"]) == pytest.approx(1)
    assert sum(row["market_1x2"]) == pytest.approx(1)
    assert row["kickoff_utc"] > lab["created_at_utc"]
    assert row["independent_model"].startswith("observed-frequency")


def test_odds_change_does_not_modify_independent_predictions(tmp_path):
    labels = prior(tmp_path/"labels.json")
    a = build_forecast(labels=labels, quote_manifest=manifest(tmp_path/"one", h="2.1"), at=AT)
    b = build_forecast(labels=labels, quote_manifest=manifest(tmp_path/"two", h="1.2"), at=AT)
    assert a["fixtures"][0]["independent_1x2"] == b["fixtures"][0]["independent_1x2"]
    assert a["fixtures"][0]["independent_prediction_id"] == b["fixtures"][0]["independent_prediction_id"]
    assert a["fixtures"][0]["market_1x2"] != b["fixtures"][0]["market_1x2"]


def test_independent_prediction_available_when_market_rejected(tmp_path):
    lab = build_forecast(labels=prior(tmp_path/"labels.json"),
                         quote_manifest=manifest(tmp_path/"src", status="Closed"), at=AT)
    row = lab["fixtures"][0]
    assert row["market_1x2"] is None
    assert row["market_rejection_reasons"]


def test_no_after_kickoff_and_no_future_training_labels(tmp_path):
    labels = prior(tmp_path/"labels.json")
    source = manifest(tmp_path/"src")
    with pytest.raises(ValueError, match="kickoff"):
        build_forecast(labels=labels, quote_manifest=source,
                       at=AT+dt.timedelta(hours=12))
    prior(labels, future=True)
    with pytest.raises(ValueError, match="future"):
        build_forecast(labels=labels, quote_manifest=source, at=AT)


def test_frozen_results_scoring_only_after_match_and_identity_verified(tmp_path):
    lab = build_forecast(labels=prior(tmp_path/"labels.json"),
                         quote_manifest=manifest(tmp_path/"src"), at=AT)
    row = lab["fixtures"][0]
    day = dt.datetime.fromisoformat(row["kickoff_utc"]).astimezone(dt.timezone(dt.timedelta(hours=8))).date().isoformat()
    outcome = [{
        "matchId": row["matchId"], "source": "sporttery_official_result_api",
        "matchResultStatus": "2", "matchDate": day,
        "homeTeamId": row["homeTeamId"], "awayTeamId": row["awayTeamId"],
        "score": [1, 0], "sectionsNo999": "1:0",
    }]
    with pytest.raises(ValueError, match="before kickoff"):
        score_frozen(lab, outcome, now=AT)
    score = score_frozen(lab, outcome, now=AT + dt.timedelta(hours=12))
    assert score["n"] == score["market_n"] == 1
    assert score["independent"]["logloss"] > 0
    outcome[0]["homeTeamId"] = "WRONG"
    with pytest.raises(ValueError, match="identity"):
        score_frozen(lab, outcome, now=AT + dt.timedelta(hours=12))


def test_no_results_returns_zero_not_fake_accuracy(tmp_path):
    lab = build_forecast(labels=prior(tmp_path/"labels.json"),
                         quote_manifest=manifest(tmp_path/"src"), at=AT)
    score = score_frozen(lab, [], now=AT)
    assert score["n"] == 0 and score["independent"] is None


def test_freeze_file_create_only(tmp_path):
    out = tmp_path / "record.json"
    sha = _create_only(out, {"fixture": 1})
    assert sha == hashlib.sha256(out.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        _create_only(out, {"fixture": 2})
