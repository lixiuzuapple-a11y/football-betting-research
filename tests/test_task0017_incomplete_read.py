"""Regression test: interrupted HTTP body must be recorded, not crash."""
import http.client
import sqlite3
from tools import task0017_official_only as collector

def test_incomplete_read_is_recorded(monkeypatch, tmp_path):
    def fail(timeout):
        raise http.client.IncompleteRead(b"partial", 900)
    monkeypatch.setattr(collector, "fetch", fail)
    con=sqlite3.connect(tmp_path/"test.sqlite3")
    con.execute(collector.SCHEMA)
    row=collector.capture_once(con,tmp_path,timeout=1,commit="testsha")
    assert row["result"]=="transport_error"
    dbrow=con.execute("select result,error from captures").fetchone()
    assert dbrow[0]=="transport_error"
    assert "IncompleteRead" in dbrow[1]
    con.close()
