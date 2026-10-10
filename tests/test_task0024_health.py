import datetime as dt,sqlite3
from types import SimpleNamespace
from tools import task0024_health as m

def test_completed_and_premature(monkeypatch,tmp_path):
 c=sqlite3.connect(tmp_path/"official.sqlite3")
 c.execute("create table captures(capture_id integer primary key,observed_at_utc text,result text,match_count integer)")
 c.execute("insert into captures(observed_at_utc,result,match_count) values('2026-10-10T00:00:00+00:00','ok',67)");c.commit();c.close()
 monkeypatch.setattr(m.subprocess,"run",lambda argv,**kw:SimpleNamespace(stdout="inactive\n" if "ActiveState" in argv else "success\n"))
 now=dt.datetime(2026,10,11,tzinfo=dt.timezone.utc)
 assert m.check(tmp_path,"unit",1,now)["status"]=="COMPLETED"
 assert m.check(tmp_path,"unit",2,now)["status"]=="FAIL"
 monkeypatch.setattr(m.subprocess,"run",lambda argv,**kw:SimpleNamespace(stdout="failed\n" if "ActiveState" in argv else "exit-code\n"))
 assert m.check(tmp_path,"unit",1,now)["status"]=="FAIL"
