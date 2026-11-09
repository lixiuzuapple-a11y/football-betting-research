"""TASK0048 scorer must never invent, rewrite, or silently omit results."""
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tools import task0048_scheduled_score as a
from tools.task0044_forward_orchestrator import OfficialFinalPending
from tools.phase2_forecast_lab import _create_only

UTC=dt.timezone.utc
NOW=dt.datetime(2026,11,2,5,0,tzinfo=UTC)


def setup_case(tmp_path, monkeypatch, *, kickoff=None, published=None):
    kickoff=kickoff or (NOW-dt.timedelta(days=1))
    published=published or (kickoff-dt.timedelta(days=2))
    repo=tmp_path/"repo"
    (repo/"research").mkdir(parents=True)
    base=tmp_path/"forward"
    (base/"journal").mkdir(parents=True)
    score=tmp_path/"scores"
    run=base/"runs"/"run-test"
    run.mkdir(parents=True)
    filename="task0046_forward_20261030T090000Z_"+"a"*12+".json"
    ledger=repo/"research"/filename
    freeze=run/"NEW_FORECAST_FREEZE.json"
    ps={k:[.5,.25,.25] for k in (
        "global_frequency","league_frequency","pooled_elo_davidson","league_poisson")}
    forecast={"task":"TASK0043","frozen_at_utc":(published-dt.timedelta(minutes=2)).isoformat(),
              "capture":{"sha256":"1"*64}, "market_prices_input_to_models":False,
              "new_results_input_to_models":False,"no_bet_or_buy":True,
              "predictions":[{"matchId":"10001","kickoff_utc":kickoff.isoformat(),
                              "official_home_id":"1","official_away_id":"2",
                              "models_1x2_home_draw_away":ps}]}
    digest=_create_only(freeze,forecast)
    pledge={"task":"TASK0043","status":"PRE_KICKOFF_FROZEN_RESEARCH_ONLY",
            "frozen_file_sha256":digest,"official_raw_sha256":"1"*64,
            "frozen_at_utc":forecast["frozen_at_utc"],
            "predictions":forecast["predictions"],"qualified":1}
    _create_only(ledger,pledge)
    head="b"*40
    event={"status":"PUSHED_GIT_PRE_KICKOFF_LOCAL_CLOCK",
           "run_root":str(run),
           "capture_result":{"path":str(freeze)},
           "commit_result":{
               "ledger":str(ledger),"git_head":head,"remote_head":head,
               "frozen_file_sha256":digest,
               "status":"PUSHED_GIT_PRE_KICKOFF_LOCAL_CLOCK"}}
    _create_only(base/"journal"/"run-20261030.json",event)
    def git(command,**kwargs):
        if command[:2]==["git","show"] and len(command)==3:
            return subprocess.CompletedProcess(command,0,stdout=ledger.read_bytes().replace(b"\r\n",b"\n"))
        if command[:3]==["git","show","-s"]:
            return subprocess.CompletedProcess(command,0,stdout=published.isoformat()+"\n")
        if command[:2]==["git","merge-base"]:
            return subprocess.CompletedProcess(command,0,stdout=b"")
        raise AssertionError("unapproved git call")
    monkeypatch.setattr(a.subprocess,"run",git)
    return repo,base,score,ledger,freeze,event


def test_no_committed_future_predictions_no_scoring(tmp_path):
    repo=tmp_path/"repo"; repo.mkdir()
    base=tmp_path/"forward"; (base/"journal").mkdir(parents=True)
    result=a.run(repo=repo,forward_base=base,score_base=tmp_path/"scored",now=NOW,
                 score_fn=lambda **kw: pytest.fail("no legitimate freeze"))
    assert result["status"]=="NO_COMMITTED_NEW_PROSPECTS"
    assert result["eligible_committed_cohorts"]==0


def test_before_delay_no_official_fetch_and_retained_journal(tmp_path,monkeypatch):
    repo,base,score,ledger,freeze,event=setup_case(
        tmp_path,monkeypatch,kickoff=NOW+dt.timedelta(hours=1))
    result=a.run(repo=repo,forward_base=base,score_base=score,now=NOW,
                 score_fn=lambda **kw:pytest.fail("premature official fetch"))
    assert result["results"][0]["status"]=="WAIT_KICKOFF_PLUS_THREE_HOURS"
    assert len(list((score/"journal").glob("*.json")))==1


def test_after_delay_reuses_scorer_and_independent_qa_and_no_duplicate(tmp_path,monkeypatch):
    repo,base,score,ledger,freeze,event=setup_case(tmp_path,monkeypatch)
    calls=[]
    def fake_score(**kwargs):
        calls.append(("score",kwargs))
        kwargs["out_root"].mkdir(parents=True)
        _create_only(kwargs["out_root"]/"BLIND_SCORE.json",{"ok":True})
        return {"status":"OFFICIAL_RESULTS_SCORED","matched":1}
    def fake_audit(**kwargs):
        calls.append(("audit",kwargs))
        return {"verdict":"ACCEPT_FIRST_REAL_OFFICIAL_PROSPECTIVE_SCORE_N2","n":1}
    result=a.run(repo=repo,forward_base=base,score_base=score,now=NOW,
                 score_fn=fake_score,audit_fn=fake_audit)
    assert result["status"]=="SCORING_CHECK_COMPLETE"
    assert result["results"][0]["status"]=="INDEPENDENT_SCORE_ACCEPTED"
    assert [x[0] for x in calls]==["score","audit"]
    assert calls[0][1]["frozen_path"]==freeze
    assert calls[1][1]["ledger_git_path"]=="research/"+ledger.name
    again=a.run(repo=repo,forward_base=base,score_base=score,
                now=NOW+dt.timedelta(seconds=1),
                score_fn=lambda **kw:pytest.fail("duplicate result fetch"))
    assert again["results"][0]["status"]=="ALREADY_INDEPENDENTLY_ACCEPTED"


def test_official_result_missing_failure_retains_evidence_then_retries(tmp_path,monkeypatch):
    repo,base,score,ledger,freeze,event=setup_case(tmp_path,monkeypatch)
    calls=[]
    def unavailable(**kwargs):
        calls.append(kwargs)
        kwargs["out_root"].mkdir(parents=True)
        _create_only(kwargs["out_root"]/"RAW_API_RESULT.json",{"status":"incomplete"})
        raise ValueError("missing official target final results")
    first=a.run(repo=repo,forward_base=base,score_base=score,now=NOW,score_fn=unavailable)
    assert first["status"]=="ATTEMPTS_REQUIRE_REVIEW"
    assert first["results"][0]["status"]=="FAILED_RETAIN_ALL_EVIDENCE"
    second=a.run(repo=repo,forward_base=base,score_base=score,
                 now=NOW+dt.timedelta(minutes=5),score_fn=unavailable)
    assert second["status"]=="ATTEMPTS_REQUIRE_REVIEW"
    assert len(calls)==2
    assert calls[0]["out_root"] != calls[1]["out_root"]
    assert all((x["out_root"]/"RAW_API_RESULT.json").is_file() for x in calls)
    assert len(list((score/"journal").glob("*.json")))==2


def test_verified_official_unfinished_result_remains_pending_without_fake_score(tmp_path,monkeypatch):
    repo,base,score,ledger,freeze,event=setup_case(tmp_path,monkeypatch)
    calls=[]
    def unfinished(**kwargs):
        calls.append(kwargs["out_root"])
        kwargs["out_root"].mkdir(parents=True)
        _create_only(kwargs["out_root"]/"SOURCE_MANIFEST.json",
                     {"pages": [{"sha256":"a"*64}], "provider_status": "1"})
        _create_only(kwargs["out_root"]/"official-2026-11-01-page-1.json",
                     {"matchId":"10001","matchResultStatus":"1","sectionsNo999":""})
        raise OfficialFinalPending("official final status not yet confirmed for match 10001")
    qa=[]
    first=a.run(repo=repo,forward_base=base,score_base=score,now=NOW,
                score_fn=unfinished,audit_fn=lambda **kw:qa.append(kw))
    assert first["status"]=="WAITING_FOR_OFFICIAL_FINAL"
    assert first["results"][0]["status"]=="WAIT_OFFICIAL_FINAL"
    assert not qa
    journal=json.loads(next((score/"journal").glob("*.json")).read_text())
    assert journal["status"]=="WAIT_OFFICIAL_FINAL"
    assert Path(journal["raw_result_root"]).is_dir()
    assert not list((score/"attempts").rglob("BLIND_SCORE.json"))
    assert not list((score/"attempts").rglob("INDEPENDENT_AUDIT.json"))
    second=a.run(repo=repo,forward_base=base,score_base=score,
                 now=NOW+dt.timedelta(minutes=10),
                 score_fn=unfinished,audit_fn=lambda **kw:qa.append(kw))
    assert second["status"]=="WAITING_FOR_OFFICIAL_FINAL"
    assert len(calls)==2 and calls[0]!=calls[1]
    assert len(list((score/"journal").glob("*.json")))==2
    assert not qa


def test_official_pending_exception_without_source_manifest_is_hard_failure(tmp_path,monkeypatch):
    repo,base,score,ledger,freeze,event=setup_case(tmp_path,monkeypatch)
    def missing_raw(**kwargs):
        kwargs["out_root"].mkdir(parents=True)
        raise OfficialFinalPending("not final but no source evidence")
    result=a.run(repo=repo,forward_base=base,score_base=score,
                 now=NOW,score_fn=missing_raw)
    assert result["status"]=="ATTEMPTS_REQUIRE_REVIEW"
    assert result["results"][0]["status"]=="FAILED_RETAIN_ALL_EVIDENCE"


@pytest.mark.parametrize("mutation,pattern",[
    (lambda e:e["commit_result"].update(remote_head="z"*40),"verified Git remote"),
    (lambda e:e["commit_result"].update(git_head="not git hash"),"verified Git remote"),
    (lambda e:e["capture_result"].update(path="c:/wrong/other.json"),"relocated"),
])
def test_unanchored_or_moved_evidence_cannot_be_scored(tmp_path,monkeypatch,mutation,pattern):
    repo,base,score,ledger,freeze,event=setup_case(tmp_path,monkeypatch)
    mutation(event)
    _create_only(base/"journal"/"additional.json",event)
    (base/"journal"/"run-20261030.json").write_text(json.dumps(event))
    result=a.run(repo=repo,forward_base=base,score_base=score,now=NOW,
                 score_fn=lambda **kw:pytest.fail("never call score"))
    assert result["results"][0]["status"]=="FAILED_RETAIN_ALL_EVIDENCE"
    assert pattern in json.loads(next((score/"journal").glob("*.json")).read_text())["error"]


def test_git_anchor_after_kickoff_fails_closed(tmp_path,monkeypatch):
    repo,base,score,ledger,freeze,event=setup_case(
        tmp_path,monkeypatch,published=NOW)
    result=a.run(repo=repo,forward_base=base,score_base=score,now=NOW,
                 score_fn=lambda **kw:pytest.fail("never score unanchored"))
    assert result["results"][0]["status"]=="FAILED_RETAIN_ALL_EVIDENCE"
    assert "retroactive" in json.loads(next((score/"journal").glob("*.json")).read_text())["error"]


def test_damaged_previous_score_does_not_get_silently_skipped(tmp_path,monkeypatch):
    repo,base,score,ledger,freeze,event=setup_case(tmp_path,monkeypatch)
    (score/"journal").mkdir(parents=True)
    _create_only(score/"journal"/"old.json",{
        "ledger_file":ledger.name,"status":"INDEPENDENT_SCORE_ACCEPTED",
        "audit_file":str(score/"missing.json"),
        "score_file":str(score/"missing_score.json"),
        "audit_sha256":"a"*64,"score_sha256":"b"*64,
    })
    result=a.run(repo=repo,forward_base=base,score_base=score,now=NOW,
                 score_fn=lambda **kw:pytest.fail("must fail on corrupted audit"))
    assert result["status"]=="ATTEMPTS_REQUIRE_REVIEW"
    assert result["results"][0]["status"]=="FAILED_RETAIN_ALL_EVIDENCE"
