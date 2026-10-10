"""TASK-0021 health checker qualification tests."""
import datetime as dt
import sqlite3
from types import SimpleNamespace
from tools import task0021_health as h

def make_db(root, when, result="ok", count=67):
    c=sqlite3.connect(root/"official.sqlite3")
    c.execute("create table captures(capture_id integer,observed_at_utc text,result text,match_count integer)")
    c.execute("insert into captures values(1,?,?,?)",(when,result,count))
    c.commit();c.close()

def test_healthy_and_stale(monkeypatch,tmp_path):
    monkeypatch.setattr(h.subprocess,"run",lambda *args,**kw:SimpleNamespace(stdout="active\n"))
    now=dt.datetime(2026,10,10,4,0,tzinfo=dt.timezone.utc)
    make_db(tmp_path,dt.datetime(2026,10,10,3,59,tzinfo=dt.timezone.utc).isoformat())
    assert h.health(tmp_path,"test.service",now)["status"]=="OK"
    later=now+dt.timedelta(minutes=5)
    assert h.health(tmp_path,"test.service",later)["status"]=="FAIL"

def test_inactive_service(monkeypatch,tmp_path):
    monkeypatch.setattr(h.subprocess,"run",lambda *args,**kw:SimpleNamespace(stdout="failed\n"))
    now=dt.datetime(2026,10,10,4,0,tzinfo=dt.timezone.utc)
    make_db(tmp_path,now.isoformat())
    assert h.health(tmp_path,"test.service",now)["status"]=="FAIL"
