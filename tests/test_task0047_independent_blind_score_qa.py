"""TASK0047 independent replay: adversarial source/anchor/metrics QA."""
import copy
import hashlib
import json
import math
import subprocess

import pytest

from tools import task0047_independent_blind_score_qa as qa


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def make_case(tmp_path, monkeypatch, *, crlf_ledger=True):
    repo = tmp_path / "repo"
    repo.mkdir()
    source = tmp_path / "source"
    source.mkdir()
    r = tmp_path / "scored"
    r.mkdir()
    t_freeze = "2026-10-29T07:36:26.021565+00:00"
    t_observed = "2026-10-29T07:31:11.376632+00:00"
    t_commit = "2026-10-29T07:42:36+00:00"
    t_kick = "2026-10-30T18:00:00+00:00"
    models = {k:[.6,.2,.2] for k in qa.MODEL_KEYS}
    forecast = {"matchId":"2042359",
                "kickoff_utc":t_kick,
                "official_home_id":"618","official_away_id":"613",
                "models_1x2_home_draw_away":models}
    frozen = {"task":"TASK0043","frozen_at_utc":t_freeze,
              "capture":{"sha256":"1"*64,"received_utc":t_observed},
              "history":{"last_training_date":"2026-07-04",
                         "published_at_utc":"2026-07-05T01:23:18+00:00"},
              "market_prices_input_to_models":False,
              "new_results_input_to_models":False,
              "predictions":[forecast]}
    fb = json.dumps(frozen,sort_keys=True).encode()
    fpath = source/"freeze.json"
    fpath.write_bytes(fb)
    ledger={"task":"TASK0043",
            "status":"PRE_KICKOFF_FROZEN_RESEARCH_ONLY",
            "frozen_file_sha256":sha(fb),
            "official_raw_sha256":"1"*64,
            "predictions":[forecast],"qualified":1}
    git_bytes = (json.dumps(ledger,sort_keys=True,indent=2)+"\n").encode()
    local_bytes = git_bytes.replace(b"\n",b"\r\n") if crlf_ledger else git_bytes
    ledger_path = source/"ledger.json"
    ledger_path.write_bytes(local_bytes)
    official = {
        "success":True,"errorCode":0,
        "value":{"total":1,"matchResult":[{
            "matchId":"2042359","matchDate":"2026-10-31",
            "homeTeamId":"618","awayTeamId":"613",
            "matchResultStatus":"2","sectionsNo999":"3:2"
        }]}
    }
    raw=json.dumps(official,sort_keys=True).encode()
    raw_path = r/"official-2026-10-31-page-1.json"
    raw_path.write_bytes(raw)
    manifest = {
        "frozen_sha256":sha(fb),
        "pages":[{
            "file":raw_path.name,
            "sha256":sha(raw),"bytes":len(raw),"http_status":200,
            "source_url":qa.RESULT_URL+"?matchBeginDate=2026-10-31",
            "request_started_utc":"2026-10-31T04:30:02.300000+00:00",
            "response_received_utc":"2026-10-31T04:30:02.600000+00:00"
        }]
    }
    (r/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest))
    score = {
        "task":"TASK0044","n":1,
        "matched":[{"matchId":"2042359","target":0,"verified_score":[3,2]}],
        "model_metrics":{k:{
            "n":1, "mean_logloss":-math.log(.6),
            "mean_brier3":(.6-1)**2+.2**2+.2**2,
            "accuracy":1.0} for k in qa.MODEL_KEYS},
        "scored_at_utc":"2026-10-31T04:30:02.900000+00:00",
        "raw_result_sha256":[sha(raw)],
        "frozen_sha256":sha(fb),
        "committed_prediction_ledger_sha256":sha(local_bytes)
    }
    (r/"BLIND_SCORE.json").write_text(json.dumps(score))
    def fake_run(command,**kwargs):
        if command[:2] == ["git","show"] and len(command)==3:
            return subprocess.CompletedProcess(command,0,stdout=git_bytes)
        if command[:3] == ["git","show","-s"]:
            return subprocess.CompletedProcess(command,0,stdout=t_commit+"\n")
        raise AssertionError("unexpected subprocess")
    monkeypatch.setattr(qa.subprocess,"run",fake_run)
    return repo,fpath,ledger_path,r,git_bytes,t_commit


def audit(paths):
    repo,frozen,ledger,result,_,_=paths
    return qa.independent_audit(repo=repo,freeze=frozen,ledger=ledger,
                                result_root=result)


def load(path):
    return json.loads(path.read_text())


def put(path,value):
    path.write_text(json.dumps(value))


def test_success_independent_recomputation_crlf_canonical(tmp_path,monkeypatch):
    paths=make_case(tmp_path,monkeypatch)
    out=audit(paths)
    assert out["n"]==1
    assert out["matched"][0]["full_time_score"]==[3,2]
    assert out["model_metrics_independently_recomputed"]["league_poisson"]["mean_logloss"] == pytest.approx(-math.log(.6))
    assert out["git_checkout_differs_only_in_crlf_to_lf"] is True
    assert out["git_ledger_byte_identity"] is False


def test_success_exact_git_blob_bytes(tmp_path,monkeypatch):
    out=audit(make_case(tmp_path,monkeypatch,crlf_ledger=False))
    assert out["git_ledger_byte_identity"] is True
    assert out["git_checkout_differs_only_in_crlf_to_lf"] is False


def test_git_anchor_substantive_difference_refused(tmp_path,monkeypatch):
    paths=make_case(tmp_path,monkeypatch)
    repo,freeze,ledger,results,git_bytes,commit=paths
    def fake(cmd,**kw):
        if len(cmd)==3:return subprocess.CompletedProcess(cmd,0,stdout=git_bytes.replace(b"2042359",b"2042358"))
        return subprocess.CompletedProcess(cmd,0,stdout=commit+"\n")
    monkeypatch.setattr(qa.subprocess,"run",fake)
    with pytest.raises(ValueError,match="differs beyond"):
        audit(paths)


@pytest.mark.parametrize("field,alter,pattern",[
    ("official",lambda x:x["value"]["matchResult"][0].update(homeTeamId="999"),"identity"),
    ("official",lambda x:x["value"]["matchResult"][0].update(matchResultStatus="1"),"final status"),
    ("official",lambda x:x["value"]["matchResult"].clear(),"incomplete"),
    ("official",lambda x:x["value"]["matchResult"].append(copy.deepcopy(x["value"]["matchResult"][0])),"duplicate"),
    ("score",lambda x:x["model_metrics"]["league_poisson"].update(mean_logloss=0.4),"independently recomputed"),
    ("score",lambda x:x["matched"][0].update(target=2),"scored outcome"),
])
def test_independent_negative_cases(tmp_path,monkeypatch,field,alter,pattern):
    paths=make_case(tmp_path,monkeypatch)
    r=paths[3]
    if field=="official":
        raw=r/"official-2026-10-31-page-1.json"
        obj=load(raw)
        alter(obj)
        new_raw=json.dumps(obj).encode()
        raw.write_bytes(new_raw)
        manifest=load(r/"SOURCE_MANIFEST.json")
        manifest["pages"][0]["sha256"]=sha(new_raw)
        manifest["pages"][0]["bytes"]=len(new_raw)
        put(r/"SOURCE_MANIFEST.json",manifest)
        scr=load(r/"BLIND_SCORE.json")
        scr["raw_result_sha256"]=[sha(new_raw)]
        put(r/"BLIND_SCORE.json",scr)
    else:
        sc=r/"BLIND_SCORE.json"
        obj=load(sc);alter(obj);put(sc,obj)
    with pytest.raises(ValueError,match=pattern):
        audit(paths)


def test_unmodified_sha_corruption_rejected(tmp_path,monkeypatch):
    paths=make_case(tmp_path,monkeypatch)
    raw=paths[3]/"official-2026-10-31-page-1.json"
    raw.write_bytes(raw.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA"):
        audit(paths)


def test_modified_freeze_prohibited_even_if_status_same(tmp_path,monkeypatch):
    paths=make_case(tmp_path,monkeypatch)
    frozen=paths[1]
    data=load(frozen)
    data["predictions"][0]["models_1x2_home_draw_away"]["league_poisson"]=[.9,.05,.05]
    put(frozen,data)
    with pytest.raises(ValueError,match="freeze SHA"):
        audit(paths)
