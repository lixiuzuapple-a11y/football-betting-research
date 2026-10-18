from tools.task0032_independent_baseline import evaluate,score

def test_score_proper():
 assert score([.7,.2,.1],0)[2]==1
 assert abs(score([.7,.2,.1],0)[1]-(.3*.3+.2*.2+.1*.1))<1e-12

def test_day_holdout_no_future_leakage():
 rows=[]
 for date,y in [("2026-10-10",0),("2026-10-10",0),("2026-10-11",2),("2026-10-11",2),("2026-10-12",1)]:
  rows.append({"matchId":str(len(rows)),"date":date,"p":[1/3]*3,"y":y})
 out=evaluate(rows,min_prior=1,alpha=1)
 assert out["n"]==3
 assert len(out["daily_forecast_details"])==2
 assert out["daily_forecast_details"][0]["trained_before_day"]==2
 assert abs(out["daily_forecast_details"][0]["independent_p"][0]-.6)<1e-12
 assert out["daily_forecast_details"][1]["trained_before_day"]==4

def test_insufficient_history_no_predictions():
 assert evaluate([{"matchId":"1","date":"2026-10-10","p":[.4,.3,.3],"y":0}],min_prior=20)["n"]==0
