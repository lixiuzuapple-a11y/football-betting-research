"""TASK0044 negative controls: duplicate prevention, frozen provenance and blind score."""
import datetime as dt
import hashlib
import json
import math

import pytest

from tools import task0044_forward_orchestrator as flow
from tools.phase2_forecast_lab import _create_only

UTC = dt.timezone.utc
FIRST = dt.datetime(2026, 10, 30, 18, 0, tzinfo=UTC)
LAST = dt.datetime(2026, 10, 30, 20, 5, tzinfo=UTC)
BEFORE = dt.datetime(2026, 10, 30, 13, 30, tzinfo=UTC)
AFTER = dt.datetime(2026, 10, 31, 3, 30, tzinfo=UTC)
PS = [0.45, 0.25, 0.30]


def records():
    return [
        {"matchId": "2042359", "official_home_id": "618",
         "official_away_id": "613", "kickoff_utc": FIRST.isoformat(),
         "models_1x2_home_draw_away": {k: list(PS) for k in flow.MODEL_KEYS}},
        {"matchId": "2042364", "official_home_id": "180",
         "official_away_id": "179", "kickoff_utc": LAST.isoformat(),
         "models_1x2_home_draw_away": {k: list(PS) for k in flow.MODEL_KEYS}},
    ]


def freeze_and_ledger(tmp_path):
    frozen = {
        "task": "TASK0043", "frozen_at_utc": BEFORE.isoformat(),
        "capture": {"sha256": "1" * 64},
        "market_prices_input_to_models": False, "new_results_input_to_models": False,
        "no_bet_or_buy": True, "predictions": records(),
    }
    path = tmp_path / "freeze.json"
    sha = _create_only(path, frozen)
    ledger = {
        "task": "TASK0043", "status": "PRE_KICKOFF_FROZEN_RESEARCH_ONLY",
        "frozen_file_sha256": sha, "official_raw_sha256": "1" * 64,
        "frozen_at_utc": BEFORE.isoformat(), "predictions": records(), "qualified": 2,
    }
    anch = tmp_path / "ledger.json"
    _create_only(anch, ledger)
    return path, anch


def raw_result_pages(*, status="2", home="618", away="613", duplicate=False,
                     score1="1:0", score2="0:2"):
    rows = [
        {"matchId": 2042359, "homeTeamId": home, "awayTeamId": away,
         "matchDate": "2026-10-31", "matchResultStatus": status,
         "sectionsNo999": score1},
        {"matchId": 2042364, "homeTeamId": "180", "awayTeamId": "179",
         "matchDate": "2026-10-31", "matchResultStatus": "2",
         "sectionsNo999": score2},
    ]
    if duplicate:
        rows.append(dict(rows[0]))
    raw = json.dumps({"success": True, "errorCode": 0,
                      "value": {"matchResult": rows, "total": len(rows)}}).encode()
    meta = {
        "source_url": flow.RESULT_BASE + "?day=2026-10-31",
        "http_status": 200,
        "request_started_utc": (AFTER - dt.timedelta(seconds=4)).isoformat(),
        "response_received_utc": (AFTER - dt.timedelta(seconds=3)).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
    }
    return [{"meta": meta, "raw": raw}]


def test_official_two_match_blind_score_all_fixed_models():
    freeze = {"predictions": records()}
    result = flow.score_evidence(frozen=freeze, raw_pages=raw_result_pages(), now=AFTER)
    assert result["n"] == 2
    assert [r["target"] for r in result["matched"]] == [0, 2]
    assert not result["no_market_clv_or_profit_claim"] is False
    for stats in result["model_metrics"].values():
        assert stats["n"] == 2
        assert stats["mean_logloss"] == pytest.approx(
            (-math.log(PS[0])-math.log(PS[2])) / 2)
        assert stats["accuracy"] == 0.5


@pytest.mark.parametrize("mutation,why", [
    ({"status": "1"}, "final status"),
    ({"home": "99999"}, "identity conflict"),
    ({"score1": "99:0"}, "implausible"),
    ({"duplicate": True}, "duplicate"),
])
def test_refuse_incomplete_or_conflicting_official_results(mutation, why):
    with pytest.raises(ValueError, match=why):
        flow.score_evidence(frozen={"predictions": records()},
                            raw_pages=raw_result_pages(**mutation), now=AFTER)


def test_refuse_scoring_before_all_kickoffs_plus_three_hours():
    with pytest.raises(ValueError, match="post-kickoff"):
        flow.score_evidence(frozen={"predictions": records()},
                            raw_pages=raw_result_pages(),
                            now=LAST + dt.timedelta(hours=2, minutes=59))


def test_refuse_modified_official_response_sha_and_future_receive():
    pages = raw_result_pages()
    pages[0]["raw"] += b" "
    with pytest.raises(ValueError, match="provenance"):
        flow.score_evidence(frozen={"predictions": records()},
                            raw_pages=pages, now=AFTER)
    pages = raw_result_pages()
    pages[0]["meta"]["response_received_utc"] = (AFTER + dt.timedelta(hours=1)).isoformat()
    with pytest.raises(ValueError, match="provenance"):
        flow.score_evidence(frozen={"predictions": records()},
                            raw_pages=pages, now=AFTER)


def test_missing_official_result_not_guessed():
    pages = raw_result_pages()
    raw = json.loads(pages[0]["raw"])
    raw["value"]["matchResult"] = raw["value"]["matchResult"][:1]
    pages[0]["raw"] = json.dumps(raw).encode()
    pages[0]["meta"]["sha256"] = hashlib.sha256(pages[0]["raw"]).hexdigest()
    pages[0]["meta"]["bytes"] = len(pages[0]["raw"])
    with pytest.raises(ValueError, match="missing official"):
        flow.score_evidence(frozen={"predictions": records()},
                            raw_pages=pages, now=AFTER)


def test_official_source_page_false_status_fails_closed():
    pages = raw_result_pages()
    pages[0]["meta"]["http_status"] = 404
    with pytest.raises(ValueError, match="provenance"):
        flow.score_evidence(frozen={"predictions": records()},
                            raw_pages=pages, now=AFTER)


def test_freeze_sha_committed_ledger_guard_and_no_rewrite(tmp_path):
    frozen_path, ledger_path = freeze_and_ledger(tmp_path)
    original, ledger = flow.verified_freeze(frozen_path, ledger_path)
    assert len(original["predictions"]) == 2
    assert ledger["qualified"] == 2
    with pytest.raises(FileExistsError):
        _create_only(frozen_path, original)
    content = json.loads(frozen_path.read_text())
    content["predictions"][0]["models_1x2_home_draw_away"]["league_poisson"] = [.9,.05,.05]
    frozen_path.write_text(json.dumps(content))
    with pytest.raises(ValueError, match="provenance mismatch"):
        flow.verified_freeze(frozen_path, ledger_path)


def test_no_network_before_scoring_deadline(tmp_path, monkeypatch):
    frozen_path, ledger_path = freeze_and_ledger(tmp_path)
    called = []
    monkeypatch.setattr(flow, "official_get", lambda *_: called.append("call"))
    with pytest.raises(ValueError, match="before last fixture"):
        flow.fetch_and_score(frozen_path=frozen_path, ledger_path=ledger_path,
                             out_root=tmp_path / "should-not-exist", now=BEFORE)
    assert not called
    assert not (tmp_path / "should-not-exist").exists()


def test_after_deadline_official_fetch_saves_raw_and_scores(tmp_path, monkeypatch):
    frozen_path, ledger_path = freeze_and_ledger(tmp_path)
    page = raw_result_pages()[0]["raw"]
    monkeypatch.setattr(flow, "official_get", lambda *_: (
        flow.RESULT_BASE+"?verified=1", page, 200))
    # Simulate the later scoring window. The real CLI has no --now override.
    actual_scorer = flow.score_evidence
    monkeypatch.setattr(flow, "score_evidence",
                        lambda *, frozen, raw_pages, now:
                        actual_scorer(frozen=frozen, raw_pages=raw_pages, now=AFTER))
    out = tmp_path / "official-evidence"
    observed = flow.fetch_and_score(frozen_path=frozen_path, ledger_path=ledger_path,
                                    out_root=out, now=AFTER)
    assert observed["matched"] == 2
    assert (out / "SOURCE_MANIFEST.json").exists()
    assert (out / "BLIND_SCORE.json").exists()
    assert hashlib.sha256((out/"official-2026-10-31-page-1.json").read_bytes()).hexdigest() == hashlib.sha256(page).hexdigest()
    with pytest.raises(FileExistsError):
        flow.fetch_and_score(frozen_path=frozen_path, ledger_path=ledger_path,
                             out_root=out, now=AFTER)


def test_no_repeat_predicted_fixture_when_capture_recurs(tmp_path, monkeypatch):
    prior, ledger_path = freeze_and_ledger(tmp_path)
    calls = []
    monkeypatch.setattr(flow, "collector_run", lambda root, **kwargs: calls.append(root) or 0)
    class FakeDB:
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def execute(self, *_):
            class Rows:
                def fetchall(self): return [("ok", 200)]
            return Rows()
    monkeypatch.setattr(flow.sqlite3, "connect", lambda *_1, **_2: FakeDB())
    monkeypatch.setattr(flow, "model_build", lambda **_: {
        "predictions": records(), "model_qualified": 2,
        "capture": {"sha256": "1" * 64}, "total_observed_fixtures": 19,
    })
    out = tmp_path / "new-collection"
    result = flow.capture_and_freeze(output_root=out, identity=tmp_path/"identity"/"map.json",
                                    history=tmp_path/"history", commit="a"*40,
                                    previous_ledgers=[ledger_path], now=BEFORE)
    assert result["status"] == "NO_NEW_ELIGIBLE_PREMATCH_FIXTURES"
    assert len(result["skipped_previous_ids"]) == 2
    assert calls
    assert not (out / "NEW_FORECAST_FREEZE.json").exists()
    with pytest.raises(FileExistsError):
        flow.capture_and_freeze(output_root=out, identity=tmp_path/"identity"/"map.json",
                                history=tmp_path/"history", commit="a"*40,
                                previous_ledgers=[ledger_path], now=BEFORE)


def test_expected_no_offer_is_recorded_without_model_invention(tmp_path, monkeypatch):
    _, ledger_path = freeze_and_ledger(tmp_path)
    monkeypatch.setattr(flow, "collector_run", lambda *_a, **_kw: 0)
    class NoOfferDB:
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def execute(self, *_):
            class Rows:
                def fetchall(self): return [("no_offer", 200)]
            return Rows()
    monkeypatch.setattr(flow.sqlite3, "connect", lambda *_1, **_2: NoOfferDB())
    monkeypatch.setattr(flow, "model_build",
                        lambda **_: pytest.fail("no model permitted for no_offer"))
    # The output cannot be inside immutable historical/identity roots.
    root = tmp_path / "run"
    result = flow.capture_and_freeze(output_root=root, identity=tmp_path/"identity"/"id.json",
                                     history=tmp_path/"history", commit="a"*40,
                                     previous_ledgers=[ledger_path])
    assert result["status"] == "NORMAL_NO_OFFER_NOT_A_FAILURE"
    assert (root/"NO_OFFER.json").exists()
