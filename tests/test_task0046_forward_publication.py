"""TASK0046 mandatory negative controls for autonomous pre-kickoff Git anchoring."""
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from tools.phase2_forecast_lab import _create_only
from tools import task0046_forward_publication as f

UTC = dt.timezone.utc
NOW = dt.datetime(2027, 2, 1, 5, 0, tzinfo=UTC)
KICKOFF = NOW + dt.timedelta(hours=4)
MODEL_KEYS = ("global_frequency", "league_frequency", "pooled_elo_davidson", "league_poisson")


def frozen():
    return {
        "task": "TASK0043",
        "frozen_at_utc": (NOW - dt.timedelta(minutes=2)).isoformat(),
        "capture": {
            "received_utc": (NOW - dt.timedelta(minutes=3)).isoformat(),
            "sha256": "a" * 64, "capture_source_commit": "b" * 40
        },
        "identity_ledger_sha256": "c"*64,
        "history": {
            "last_training_date": "2026-07-04",
            "published_at_utc": "2026-07-05T01:23:18+00:00",
            "source_fixture_sha256": "d"*64,
            "source_manifest_sha256": "e"*64,
        },
        "model_qualified": 1,
        "market_prices_input_to_models": False,
        "new_results_input_to_models": False,
        "no_bet_or_buy": True,
        "predictions": [{
            "matchId": "20270001", "kickoff_utc": KICKOFF.isoformat(),
            "official_home_id": "1", "official_away_id": "2",
            "models_1x2_home_draw_away": {k:[.5,.25,.25] for k in MODEL_KEYS},
        }],
    }


def candidate(tmp_path, edit=None):
    val = frozen()
    if edit: edit(val)
    root = tmp_path / "candidate.json"
    _create_only(root, val)
    return root


def test_valid_ledger_has_clear_missing_market_and_training_provenance(tmp_path):
    path = candidate(tmp_path)
    original_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    ledger = f.build_ledger(path, now=NOW, previous=[])
    assert ledger["frozen_file_sha256"] == original_sha
    assert ledger["training_last_date"] == "2026-07-04"
    assert ledger["historical_fixture_sha256"] == "d"*64
    assert ledger["market_quote_status"] == "UNVERIFIED_NOT_INCLUDED"
    assert ledger["market_quote_time_utc"] is None
    assert ledger["official_result_status"] == "PENDING"
    assert ledger["predictions"][0]["models_1x2_home_draw_away"]["league_poisson"] == [.5,.25,.25]
    assert path.read_bytes() == candidate_data(path)


def candidate_data(path):
    return path.read_bytes()


@pytest.mark.parametrize("mutation,pattern", [
    (lambda x: x["capture"].update(sha256="z"*64), "source SHA256"),
    (lambda x: x["history"].update(last_training_date="2026-13-04"), "month"),
    (lambda x: x["history"].update(last_training_date="2027-02-01"), "training date"),
    (lambda x: x["history"].update(published_at_utc="2027-02-02T00:00:00Z"), "published"),
    (lambda x: x.update(market_prices_input_to_models=True), "forbidden"),
    (lambda x: x.update(new_results_input_to_models=True), "forbidden"),
    (lambda x: x["predictions"][0].update(kickoff_utc=(NOW+dt.timedelta(minutes=30)).isoformat()), "too late"),
    (lambda x: x["predictions"][0]["models_1x2_home_draw_away"].pop("league_poisson"), "keys changed"),
    (lambda x: x["predictions"][0].update(official_away_id="1"), "opponent"),
    (lambda x: x["capture"].update(received_utc=(NOW+dt.timedelta(minutes=1)).isoformat()), "capture time"),
])
def test_invalid_or_retroactive_data_refused(tmp_path, mutation, pattern):
    path = candidate(tmp_path, mutation)
    with pytest.raises(ValueError, match=pattern):
        f.build_ledger(path, now=NOW, previous=[])


def test_duplicate_prior_fixture_refused(tmp_path):
    path = candidate(tmp_path)
    previous = tmp_path/"prior.json"
    _create_only(previous, {
        "status":"PRE_KICKOFF_FROZEN_RESEARCH_ONLY",
        "predictions":[{"matchId":"20270001"}],
    })
    with pytest.raises(ValueError, match="previously committed"):
        f.build_ledger(path, now=NOW, previous=[previous])


def test_gitrepo_preflight_rejects_unexpected_remote_dirty_or_divergent(monkeypatch,tmp_path):
    def fake(*args,**kwargs):
        key = args[1:]
        if key == ("remote","get-url","origin"):
            return "https://github.com/other/stock.git"
        return ""
    monkeypatch.setattr(f,"git",fake)
    with pytest.raises(ValueError,match="unexpected Git remote"):
        f.git_preflight(tmp_path)
    def fake_dirty(*args, **kwargs):
        key=args[1:]
        if key==("remote","get-url","origin"):return "https://github.com/lixiuzuapple-a11y/football-betting-research.git"
        if key==("branch","--show-current"):return "main"
        if key==("status","--porcelain","--untracked-files=all"):return " M tools/task0044_forward_orchestrator.py"
        return ""
    monkeypatch.setattr(f,"git",fake_dirty)
    with pytest.raises(ValueError,match="dirty"):
        f.git_preflight(tmp_path)
    def fake_diverged(*args, **kwargs):
        key=args[1:]
        if key==("remote","get-url","origin"):return "git@github.com:lixiuzuapple-a11y/football-betting-research.git"
        if key==("branch","--show-current"):return "main"
        if key==("rev-parse","HEAD"):return "0"*40
        if key==("rev-parse","refs/remotes/origin/main"):return "1"*40
        return ""
    monkeypatch.setattr(f,"git",fake_diverged)
    with pytest.raises(ValueError,match="diverged"):
        f.git_preflight(tmp_path)


def test_publish_create_only_git_remote_verified(monkeypatch,tmp_path):
    local = candidate(tmp_path)
    ledger = f.build_ledger(local,now=NOW,previous=[])
    run_git=[]
    sha="f"*40
    def fake(repo,*args,**kwargs):
        run_git.append(args)
        if args[:1]==("rev-parse",):return sha
        if args[:1]==("ls-remote",):return sha+"\trefs/heads/main"
        return ""
    pub = f.publish(tmp_path, ledger, local, now=NOW, git_fn=fake)
    assert pub["status"] == "PUSHED_GIT_PRE_KICKOFF_LOCAL_CLOCK"
    assert [a[0] for a in run_git] == ["add","commit","rev-parse","push","ls-remote"]
    assert (tmp_path/"research").glob("task0046_forward_*.json")
    with pytest.raises(FileExistsError):
        f.publish(tmp_path, ledger, local, now=NOW, git_fn=fake)


def test_publish_no_silent_remote_mismatch(monkeypatch,tmp_path):
    local=candidate(tmp_path)
    ledger=f.build_ledger(local,now=NOW,previous=[])
    def fake(repo,*args,**kwargs):
        if args[0]=="rev-parse":return "f"*40
        if args[0]=="ls-remote":return "a"*40+"\trefs/heads/main"
        return ""
    with pytest.raises(ValueError,match="remote Git commitment"):
        f.publish(tmp_path,ledger,local,now=NOW,git_fn=fake)
    assert list((tmp_path/"research").glob("task0046_forward_*.json"))


def test_no_eligible_still_creates_durable_single_run_journal(monkeypatch,tmp_path):
    count=[]
    monkeypatch.setattr(f,"capture_and_freeze",lambda **kw: count.append(kw) or {
        "status":"NO_NEW_ELIGIBLE_PREMATCH_FIXTURES","source_observed":40,
        "skipped_previous_ids":["2042359"]})
    repo=tmp_path/"repo"
    (repo/"research").mkdir(parents=True)
    out=f.one_run(repo=repo,evidence_base=tmp_path/"evidence",
                  identity=repo/"identity",history=repo/"history",
                  commit="a"*40,mode="probe",now=NOW)
    assert out["status"]=="NO_NEW_ELIGIBLE_PREMATCH_FIXTURES"
    assert len(count)==1
    assert len(list((tmp_path/"evidence"/"journal").glob("*.json")))==1
    assert not list((repo/"research").glob("task0046_forward_*.json"))


def test_dirty_git_preflight_blocks_capture_and_retains_failure(monkeypatch,tmp_path):
    monkeypatch.setattr(f,"git_preflight",lambda *a: (_ for _ in ()).throw(ValueError("dirty")))
    monkeypatch.setattr(f,"capture_and_freeze",lambda **kw: pytest.fail("capture not allowed"))
    repo=tmp_path/"repo"
    (repo/"research").mkdir(parents=True)
    out=f.one_run(repo=repo,evidence_base=tmp_path/"evidence",
                  identity=repo/"identity",history=repo/"history",
                  commit="a"*40,mode="publish",now=NOW)
    assert out["status"]=="FAILED_RETAIN_ALL_EVIDENCE"
    assert "dirty" in out["error"]
    assert len(list((tmp_path/"evidence"/"journal").glob("*.json")))==1
