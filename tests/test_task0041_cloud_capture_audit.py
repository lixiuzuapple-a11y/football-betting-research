"""TASK0041 immutable cloud capture audit adversarial validations."""
import gzip,hashlib,json,sqlite3
import pytest
from pathlib import Path
from tools.task0041_cloud_capture_audit import audit
from tools.task0017_official_only import SCHEMA

PARSER=Path(__file__).resolve().parents[1]/"tools"/"task0017_official_only.py"
NO_OFFER={"success":True,"value":{"vtoolsConfig":{
    "offLineSaleStatus":1,"onLineSaleStatus":1,
    "onLineStopMessage":"抱歉，本彩种已停止销售"}}}
OK={"success":True,"value":{"matchInfoList":[{"subMatchList":[{"matchId":900}]}],"lastUpdateTime":"x"}}

def make_ledger(root, entries):
    root.mkdir()
    (root/"raw").mkdir()
    db=sqlite3.connect(root/"official.sqlite3")
    db.execute(SCHEMA)
    for idx,(status,object_) in enumerate(entries,1):
        raw=json.dumps(object_,ensure_ascii=False).encode("utf-8")
        sha=hashlib.sha256(raw).hexdigest()
        fn=root/"raw"/f"{sha}.json.gz"
        fn.write_bytes(gzip.compress(raw,mtime=0))
        db.execute("""INSERT INTO captures
          (capture_id,observed_at_utc,request_url,http_status,result,match_count,raw_sha256,raw_path,raw_length,source_commit)
          VALUES(?,?,?,?,?,?,?,?,?,?)""",
          (idx,f"2026-10-26T23:0{idx}:42+00:00","https://webapi.sporttery.cn/",
           200,status,0 if status=="empty" else 1,sha,f"raw/{sha}.json.gz",len(raw),"audited"))
    db.commit()
    db.close()

def test_real_normal_no_offer_legacy_reclassification(tmp_path):
    root=tmp_path/"data"
    make_ledger(root,[("ok",OK),("empty",NO_OFFER),("empty",NO_OFFER)])
    v=audit(root,PARSER)
    assert v["captures"]==3 and v["verified_sha_captures"]==3
    assert v["historical_empty_to_normal_no_offer"]==2
    assert v["reclassified_by_fixed_parser"]=={"ok":1,"no_offer":2}
    assert v["raw_distinct_files_hashed"]==2
    assert v["sqlite_quick_check"]=="ok"

def test_mutated_raw_bytes_fail_sha(tmp_path):
    root=tmp_path/"data"
    make_ledger(root,[("empty",NO_OFFER)])
    path=next((root/"raw").glob("*.gz"))
    path.write_bytes(gzip.compress(b"{}",mtime=0))
    with pytest.raises(ValueError,match="source hash"):
        audit(root,PARSER)

def test_unapproved_empty_not_reclassified_safely(tmp_path):
    root=tmp_path/"data"
    make_ledger(root,[("empty",{"success":True,"value":{"vtoolsConfig":{}}})])
    with pytest.raises(ValueError,match="mismatched result"):
        audit(root,PARSER)
