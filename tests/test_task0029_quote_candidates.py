import datetime as dt
from tools.task0029_quote_candidates import transition

OBS=dt.datetime(2026,10,18,8,0,tzinfo=dt.timezone.utc)
MATCH={"matchStatus":"Selling","sellStatus":1,"poolList":[{"poolCode":"HAD","poolStatus":"Selling"}]}
def row(when="15:00:00",h="2.10",hf="0"):
 return {"h":h,"d":"3.20","a":"3.40","hf":hf,"updateDate":"2026-10-18","updateTime":when}

def test_initial_and_duplicate():
 label,state=transition(None,row(),OBS,"had",MATCH)
 assert label=="initial"
 assert transition(state,row(),OBS,"had",MATCH)[0]=="duplicate"

def test_same_timestamp_conflict_and_rewind():
 _,state=transition(None,row(),OBS,"had",MATCH)
 assert transition(state,row(h="2.20"),OBS,"had",MATCH)[0]=="same_timestamp_conflict"
 assert transition(state,row(when="14:00:00",h="2.20"),OBS,"had",MATCH)[0]=="provider_rewind"

def test_advance_and_bad_status():
 _,state=transition(None,row(),OBS,"had",MATCH)
 assert transition(state,row(when="16:00:00",h="2.20"),OBS,"had",MATCH)[0]=="advance_change"
 assert transition(None,row(hf="1"),OBS,"had",MATCH)[0]=="flagged"
 assert transition(None,row(),OBS,"had",{**MATCH,"matchStatus":"Closed"})[0]=="match_not_selling"
