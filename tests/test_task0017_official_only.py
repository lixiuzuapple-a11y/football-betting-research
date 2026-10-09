"""TASK-0017 source-only parser and persistence tests."""
import gzip
import json
import sqlite3
from pathlib import Path

from tools import task0017_official_only as collector


def test_classify_full_and_empty():
    full={"success":True,"value":{"matchInfoList":[
        {"subMatchList":[{"matchId":1,"had":{},"hhad":{},"ttg":{},"crs":{},"hafu":{}}]},
        {"subMatchList":[{"matchId":2}]}],"lastUpdateTime":"x"}}
    assert collector.classify(json.dumps(full).encode())==("ok",2,"x")
    assert collector.classify(json.dumps({"success":True,"value":{"vtoolsConfig":{}}}).encode())==("empty",0,None)
    assert collector.classify(json.dumps({"success":False}).encode())[0]=="source_error"


def test_persistence_and_hash(monkeypatch, tmp_path: Path):
    body=json.dumps({"success":True,"value":{"matchInfoList":[{"subMatchList":[{"matchId":2}]}]}}).encode()
    monkeypatch.setattr(collector,"fetch",lambda timeout:(body,200))
    con=sqlite3.connect(tmp_path/"test.sqlite3")
    con.execute(collector.SCHEMA)
    row=collector.capture_once(con,tmp_path,timeout=1,commit="abc")
    assert row["result"]=="ok" and row["matches"]==1
    entry=con.execute("SELECT raw_path,raw_sha256,match_count FROM captures").fetchone()
    assert gzip.open(tmp_path/entry[0],"rb").read()==body
    assert row["sha256"]==entry[1] and entry[2]==1
    con.close()
