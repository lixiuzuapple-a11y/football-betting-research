from tools.task0030_official_result_evidence import score,reconcile

def test_score_strict():
 assert score("2:1")==[2,1]
 assert score("0:0")==[0,0]
 for s in ("无效场次","",None,"2:","2-1","-1:1"):
  assert score(s) is None

def test_status_and_identity_must_match():
 idx={"11":{"matchId":"11","matchDate":"2026-10-11","homeTeamId":"10","awayTeamId":"20","businessDate":"2026-10-11"}}
 row={"matchId":11,"matchDate":"2026-10-11","homeTeamId":10,"awayTeamId":20,"sectionsNo999":"2:1","matchResultStatus":"2"}
 assert len(reconcile(idx,[row])["verified_scores"])==1
 assert len(reconcile(idx,[{**row,"matchResultStatus":"1"}])["verified_scores"])==0
 assert len(reconcile(idx,[{**row,"homeTeamId":21}])["identity_conflicts"])==1
 assert len(reconcile(idx,[{**row,"matchDate":"2026-10-12"}])["identity_conflicts"])==1

def test_duplicates_conflict():
 idx={"11":{"matchId":"11","matchDate":"2026-10-11","homeTeamId":"10","awayTeamId":"20","businessDate":"2026-10-11"}}
 row={"matchId":11,"matchDate":"2026-10-11","homeTeamId":10,"awayTeamId":20,"sectionsNo999":"2:1","matchResultStatus":"2"}
 j=reconcile(idx,[row,{**row,"sectionsNo999":"1:1"}])
 assert j["identity_conflicts"]==["11"]
 assert len(j["verified_scores"])==0
