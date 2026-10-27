"""TASK0041: regressions for normal empty/no-sale pages and bounded collector loop.

'no_offer' with HTTP200 is a successful observation, NOT a broken connection.
Only explicitly documented provider stop-sale config may be accepted.
"""
import json
from tools import task0017_official_only as collector

def _response(cfg):
    return json.dumps({"dataFrom":"web","emptyFlag":False,"errorCode":0,
                       "errorMessage":"处理成功","success":True,
                       "value":{"vtoolsConfig":cfg}},ensure_ascii=False).encode("utf-8")

SALE_STOP={"offLineSaleStatus":1,"offLineStopMessage":"抱歉，本彩种已停止销售",
           "onLineSaleStatus":1,"onLineStopMessage":"抱歉，本彩种已停止销售"}

def test_actual_277_byte_response_family_no_offer():
    assert collector.classify(_response(SALE_STOP))==("no_offer",0,None)

def test_invalid_config_and_provider_error_fail_closed():
    invalid={"offLineSaleStatus":0,"onLineSaleStatus":1,"onLineStopMessage":"抱歉，本彩种已停止销售"}
    assert collector.classify(_response(invalid))[0]=="schema_error"
    assert collector.classify(_response({"offLineSaleStatus":1,"onLineSaleStatus":1,
                                         "onLineStopMessage":"系统错误"}))[0]=="schema_error"
    b=json.loads(_response(SALE_STOP));b["success"]=False
    assert collector.classify(json.dumps(b).encode())[0]=="source_error"

def test_zero_matches_in_valid_matchinfolist_no_offer():
    assert collector.classify(json.dumps({"success":True,"value":{
        "matchInfoList":[{"subMatchList":[]}],"lastUpdateTime":"2026-10-27 07:05:42"
    }}).encode())==("no_offer",0,"2026-10-27 07:05:42")

def test_multiple_normal_no_offer_observations_do_not_terminate(monkeypatch,tmp_path):
    records=iter(["no_offer","no_offer","no_offer","no_offer","ok"])
    calls=[]
    def fake_capture(con,root,*,timeout,commit):
        value=next(records);calls.append(value)
        return {"capture_id":len(calls),"result":value,"matches":int(value=="ok")}
    monkeypatch.setattr(collector,"capture_once",fake_capture)
    monkeypatch.setattr(collector.time,"sleep",lambda _:None)
    ret=collector.run(tmp_path/"fresh-root",max_rounds=5,max_hours=2,
                      cadence=60,timeout=10,max_bad=3,commit="verified")
    assert ret==0 and len(calls)==5
    assert (tmp_path/"fresh-root"/"CONFIG.json").exists()

def test_three_actual_source_failures_still_stop(monkeypatch,tmp_path):
    values=iter(["no_offer","schema_error","transport_error","source_error","ok"])
    observed=[]
    def fake_capture(con,root,*,timeout,commit):
        v=next(values);observed.append(v)
        return {"capture_id":len(observed),"result":v,"matches":0}
    monkeypatch.setattr(collector,"capture_once",fake_capture)
    monkeypatch.setattr(collector.time,"sleep",lambda _:None)
    ret=collector.run(tmp_path/"new-root",max_rounds=5,max_hours=2,
                      cadence=60,timeout=10,max_bad=3,commit="verified")
    assert ret==2 and observed==["no_offer","schema_error","transport_error","source_error"]
