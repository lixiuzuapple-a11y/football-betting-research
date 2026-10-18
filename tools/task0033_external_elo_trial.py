"""Fixed-parameter non-market Elo-ish probability baseline on independent prior results.
Scores: previous seasons only + earlier match dates. NEVER read odds into predictor.
Market implied odds are comparison only, same test fixtures.
"""
import argparse,csv,datetime as dt,json,math,collections
from pathlib import Path
LEAGUES=("E0","E1","D1","SP1","I1","F1")
def valid_rows(path):
 with path.open(encoding="utf-8-sig",newline="") as f:
  for r in csv.DictReader(f):
   try:
    date=dt.datetime.strptime(r["Date"],"%d/%m/%Y").date()
    if not r["FTHG"].isdigit() or not r["FTAG"].isdigit():continue
    outcome=0 if int(r["FTHG"])>int(r["FTAG"]) else 2 if int(r["FTHG"])<int(r["FTAG"]) else 1
    yield date,r["HomeTeam"],r["AwayTeam"],outcome,r
   except (ValueError,KeyError,TypeError):continue
def elo_p(home_rating,away_rating):
 # Fixed before test: draw probability 0.26, home strength boost 65 Elo.
 strength=1/(1+10**(-((home_rating+65)-away_rating)/400))
 return [0.74*strength,0.26,0.74*(1-strength)]
def score(prob,y):
 return -math.log(max(prob[y],1e-15)),sum((prob[i]-(i==y))**2 for i in range(3)),int(max(range(3),key=lambda i:prob[i])==y)
def de_vig(r):
 try:
  odds=[float(r[k]) for k in ("AvgH","AvgD","AvgA")]
  if not all(math.isfinite(x) and x>1 for x in odds):return None
  inv=[1/x for x in odds]; return [x/sum(inv) for x in inv]
 except (ValueError,TypeError,KeyError):return None
def update(ra,rb,y):
 h=1 if y==0 else 0 if y==2 else .5
 expectancy=1/(1+10**(-((ra+65)-rb)/400))
 return ra+20*(h-expectancy),rb+20*((1-h)-(1-expectancy))
def run(directory):
 results=[];details={}
 for league in LEAGUES:
  train=sorted(valid_rows(directory/f"{league}-2526.csv"),key=lambda r:r[0])
  test=sorted(valid_rows(directory/f"{league}-2627.csv"),key=lambda r:r[0])
  ratings=collections.defaultdict(lambda:1500.0);seen=collections.Counter()
  # Same-day batch updates prevent within-day order leakage.
  for series,is_test in ((train,False),(test,True)):
   grouped=collections.defaultdict(list)
   for row in series:grouped[row[0]].append(row)
   for date,group in sorted(grouped.items()):
    predictions=[]
    for _,home,away,y,raw in group:
     p=elo_p(ratings[home],ratings[away]);market=de_vig(raw)
     if is_test and market is not None and seen[home]>=5 and seen[away]>=5:
      predictions.append((home,away,y,p,market))
     else:predictions.append((home,away,y,None,None))
    for home,away,y,p,market in predictions:
     if p is not None:
      li,bi,hi=score(p,y);lm,bm,hm=score(market,y)
      results.append({"league":league,"date":str(date),"independent_loss":li,"market_loss":lm,"independent_brier":bi,"market_brier":bm,"independent_hit":hi,"market_hit":hm})
    # update after all predictions of that date, with fixed pre-day Elo
    updates=collections.defaultdict(list)
    for _,home,away,y,_ in group:
     rh,ra=update(ratings[home],ratings[away],y)
     updates[home].append(rh-ratings[home]);updates[away].append(ra-ratings[away])
     seen[home]+=1;seen[away]+=1
    for team,delta in updates.items():ratings[team]+=sum(delta)
  details[league]={"train_rows":len(train),"test_rows":len(test),"tested_comparable":sum(r["league"]==league for r in results)}
 n=len(results)
 avg=lambda field:sum(x[field] for x in results)/n
 return {"model":"fixed-parameter Elo derived exclusively from prior results; initial 1500 K20 home+65 draw .26; no odds used as predictors","source_directory":str(directory),"league_details":details,"matched_n":n,"independent":{"logloss":avg("independent_loss"),"brier":avg("independent_brier"),"accuracy":avg("independent_hit")},"market":{"logloss":avg("market_loss"),"brier":avg("market_brier"),"accuracy":avg("market_hit")},"difference_independent_minus_market_logloss":avg("independent_loss")-avg("market_loss"),"records":results}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--data",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
 r=run(a.data);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:v for k,v in r.items() if k!="records"}))
if __name__=="__main__":main()
