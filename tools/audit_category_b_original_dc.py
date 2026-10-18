"""Stage B: run upstream callumfm/dixon-coles 0.1.0 unchanged via isolated venv.
Requires: numpy and installed upstream package in sandbox; project core unaffected.
Preceding full season only, held-out current-season test. No odds in DC fit/predict.
"""
import argparse,csv,datetime as dt,math,json,random,collections
from pathlib import Path

def load(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        result=[]
        for row in csv.DictReader(f):
            try:
                h,a=int(row["FTHG"]),int(row["FTAG"])
                day=dt.datetime.strptime(row["Date"],"%d/%m/%Y").date()
                if h<0 or a<0:continue
            except (TypeError,KeyError,ValueError):continue
            result.append((day,row["HomeTeam"],row["AwayTeam"],h,a,row))
        return sorted(result,key=lambda x:x[0])

def probabilities(m):
    p=[float(m["home_win"]),float(m["draw"]),float(m["away_win"])]
    if not all(math.isfinite(x) and x>=0 for x in p):raise ValueError("bad model probabilities")
    if not (0.999<=sum(p)<=1.001):raise ValueError("un-normalized original model probabilities")
    return [x/sum(p) for x in p]

def market_price(row):
    try:
        odds=[float(row[k]) for k in ("AvgH","AvgD","AvgA")]
        if not all(math.isfinite(x) and x>1 for x in odds):return None
        inv=[1/o for o in odds];return [x/sum(inv) for x in inv]
    except (KeyError,TypeError,ValueError):return None

def metric(rows,key):
    if not rows:return None
    n=len(rows);ll=sum(-math.log(max(r[key][r["y"]],1e-15)) for r in rows)/n
    b=sum(sum((r[key][i]-(i==r["y"]))**2 for i in range(3)) for r in rows)/n
    hits=sum(max(range(3),key=lambda i:r[key][i])==r["y"] for r in rows)/n
    return {"n":n,"log_loss":ll,"brier_sum":b,"accuracy":hits}

def trial(data_dir):
    import numpy as np
    import dixon_coles as dc
    training=load(Path(data_dir)/"E0-2526.csv")
    testing=load(Path(data_dir)/"E0-2627.csv")
    if not training or not testing or max(r[0] for r in training)>=min(r[0] for r in testing):
        raise ValueError("training/test date overlap")
    # Defaults pinned: lambda0=3 xi=.005 xg_weight=.5 but no xG supplied, K independent.
    model=dc.DixonColesModel(seed=42)
    model.fit(
        home_teams=np.array([r[1] for r in training]),
        away_teams=np.array([r[2] for r in training]),
        home_goals=np.array([r[3] for r in training],dtype="int64"),
        away_goals=np.array([r[4] for r in training],dtype="int64"),
        dates=np.array([str(r[0]) for r in training],dtype="datetime64[D]"))
    results=[]
    for day,hteam,ateam,hg,ag,row in testing:
        mp=market_price(row)
        if mp is None:continue
        p=probabilities(model.predict(hteam,ateam))
        y=0 if hg>ag else 1 if hg==ag else 2
        results.append({"day":str(day),"home":hteam,"away":ateam,"y":y,"independent":p,"market":mp})
    a=metric(results,"independent");b=metric(results,"market")
    difference=a["log_loss"]-b["log_loss"]
    rng=random.Random(20261018);group=collections.defaultdict(list)
    for x in results:group[x["day"]].append(x)
    days=sorted(group)
    boot=[]
    for _ in range(3000):
        rr=[r for _ in days for r in group[rng.choice(days)]]
        boot.append(metric(rr,"independent")["log_loss"]-metric(rr,"market")["log_loss"])
    boot.sort()
    return {"upstream_project":"callumfm/dixon-coles","upstream_head":"dea06c6e4b38085d6a4b84186cb9ead321a73ce4","upstream_package_version":"0.1.0",
            "train_rows":len(training),"heldout_rows":len(testing),"matched_test_rows":len(results),
            "model":{"params":"upstream defaults (lambda0=3, seed42, xi=.005) no xG inputs, no odds features","metrics":a},
            "market":{"source":"Football-Data AvgH/AvgD/AvgA, retrospective CSV benchmark","metrics":b},
            "logloss_model_minus_market":difference,"day_cluster_bootstrap95":[boot[75],boot[2924]],
            "records":results}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();z=trial(a.data)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in z.items() if k!="records"},ensure_ascii=False))
if __name__=="__main__":main()
