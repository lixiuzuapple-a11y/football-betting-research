"""TASK0040 actual-new-period prospective source PIT and tamper/adversarial QA."""
import hashlib,json
from pathlib import Path
import pytest
from tools.task0040_new_window_gate import run,validate_source,classify_one

def demo_match():
    return {
      "matchId":2042245,"matchDate":"2026-10-27","matchTime":"07:00:00",
      "matchStatus":"Selling","sellStatus":1,"leagueAbbName":"巴甲",
      "homeTeamAbbEnName":"FLA","awayTeamAbbEnName":"ALM",
      "homeTeamId":571,"awayTeamId":563,
      "poolList":[{"poolCode":"HAD","poolStatus":"Selling"}],
      "had":{"h":"1.20","d":"5.40","a":"9.00","hf":"0","df":"0","af":"0",
             "updateDate":"2026-10-26","updateTime":"10:43:11"}
    }

def source(tmp_path,match=None,when="2026-10-26T03:49:44.926854+00:00"):
    obj={"success":True,"errorCode":0,"value":{"matchInfoList":[{"subMatchList":[match or demo_match()]}]}}
    raw=json.dumps(obj).encode()
    p=tmp_path/"sporttery-20261026T034944Z.json"
    p.write_bytes(raw)
    manifest={"raw_filename":p.name,"raw_bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
              "http_status":200,"group_count":1,"fixture_count":1,
              "url":"https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry",
              "request_started_at_utc":"2026-10-26T03:49:44.707513+00:00",
              "response_received_at_utc":when}
    mp=tmp_path/(p.name+".manifest.json")
    mp.write_text(json.dumps(manifest),encoding="utf-8")
    return mp

def test_independent_accepted_strict_quote_with_no_results(tmp_path):
    result=run(source(tmp_path))
    assert result["fixture_total"]==1
    assert result["strict_had_accepted"]==1
    assert result["numeric_had_accepted"]==1
    assert result["no_result_join"] and result["no_executable_odds_claim"]
    row=result["matches"][0]
    assert row["matchId"]=="2042245"
    assert row["hours_before_kickoff_at_receipt"]>18
    assert abs(sum(row["frozen_had_fair_market_probabilities"])-1)<1e-10
    assert row["overround"]>0
    assert "y" not in row and "roi" not in row and "score" not in row

def test_nonzero_price_flags_rejected_despite_numeric(tmp_path):
    m=demo_match();m["had"]["hf"]="1"
    r=run(source(tmp_path,m))
    assert r["strict_had_accepted"]==0 and r["numeric_had_accepted"]==1
    assert r["rejected_strict_reasons"]=={"nonzero_HAD_flags":1}

def test_provider_updated_in_future_not_accepted(tmp_path):
    m=demo_match()
    m["had"]["updateDate"]="2026-10-27"
    m["had"]["updateTime"]="23:00:00"
    r=run(source(tmp_path,m))
    assert r["strict_had_accepted"]==0 and r["numeric_had_accepted"]==0
    assert "timestamps_or_unclassified" in r["matches"][0]["rejection_reasons"]

def test_at_kickoff_must_pass_no_quoting(tmp_path):
    m=demo_match()
    m["matchDate"]="2026-10-26";m["matchTime"]="10:00:00"
    r=run(source(tmp_path,m))
    assert r["strict_had_accepted"]==0 and r["numeric_had_accepted"]==0
    assert "at_or_after_kickoff" in r["matches"][0]["rejection_reasons"]

def test_sha256_tamper_detected(tmp_path):
    mp=source(tmp_path);meta=json.loads(mp.read_text())
    p=tmp_path/meta["raw_filename"];p.write_bytes(p.read_bytes()+b" ")
    with pytest.raises(ValueError,match="byte count"):
        validate_source(mp)
    p.write_bytes(p.read_bytes()[:-1])
    obj=json.loads(p.read_bytes())
    obj["value"]["matchInfoList"][0]["subMatchList"][0]["had"]["h"]="2.00"
    t=json.dumps(obj).encode()
    p.write_bytes(t)
    meta["raw_bytes"]=len(t)
    mp.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match="sha mismatch"):
        validate_source(mp)

def test_manifest_rejects_invalid_timing_and_path_traversal(tmp_path):
    mp=source(tmp_path);meta=json.loads(mp.read_text())
    meta["request_started_at_utc"]="2026-10-26T03:55:00+00:00"
    mp.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match="time interval"):validate_source(mp)
    meta["request_started_at_utc"]="2026-10-26T03:49:44+00:00"
    meta["raw_filename"]="../sporttery-20261026T034944Z.json"
    mp.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match="noncanonical"):validate_source(mp)

def test_duplicate_fixture_id_rejected(tmp_path):
    mp=source(tmp_path)
    meta=json.loads(mp.read_text())
    p=tmp_path/meta["raw_filename"]
    obj=json.loads(p.read_bytes())
    matches=obj["value"]["matchInfoList"][0]["subMatchList"]
    matches.append(matches[0])
    raw=json.dumps(obj).encode();p.write_bytes(raw)
    meta["raw_bytes"]=len(raw);meta["sha256"]=hashlib.sha256(raw).hexdigest()
    meta["fixture_count"]=2
    mp.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match="duplicate match ID"):validate_source(mp)

def test_non_selling_match_rejected(tmp_path):
    m=demo_match();m["matchStatus"]="Closed"
    r=run(source(tmp_path,m))
    assert not r["matches"][0]["strict_had_pre_kickoff"]
    assert "match_not_selling" in r["matches"][0]["rejection_reasons"]
