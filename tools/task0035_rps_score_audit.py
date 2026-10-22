"""TASK0035 supplemental scoring audit on previously frozen TASK0034 predictions.

Research diagnostic only: adds RPS without refitting or changing selections.
RPS uses the predeclared 1X2 ordinal convention home < draw < away,
with 2 cumulative thresholds and normalization by K-1=2.
"""
import argparse,collections,json,math,random
from pathlib import Path

def rps3(probs,outcome):
    if len(probs)!=3 or not all(math.isfinite(v) and v>=0 for v in probs) or abs(sum(probs)-1)>1e-8:
        raise ValueError("invalid three-outcome probability")
    if outcome not in (0,1,2):
        raise ValueError("invalid outcome class")
    return ((probs[0] - (1 if outcome==0 else 0))**2
            + (probs[0]+probs[1] - (1 if outcome<=1 else 0))**2)/2

def audit(records,seed=20261022,repetitions=5000):
    if not records:raise ValueError("no records")
    rows=[]
    for r in records:
        model=rps3(r["independent"],r["y"])
        market=rps3(r["market"],r["y"])
        rows.append({"matchId":r["matchId"],"date":r["day"],"rps_model":model,
                     "rps_market":market,"rps_model_minus_market":model-market})
    avg=lambda k,seq=rows:sum(z[k] for z in seq)/len(seq)
    days=collections.defaultdict(list)
    for row in rows:days[row["date"]].append(row)
    dates=sorted(days)
    rng=random.Random(seed);boot=[]
    for _ in range(repetitions):
        sample=[x for _ in dates for x in days[rng.choice(dates)]]
        boot.append(avg("rps_model_minus_market",sample))
    boot.sort()
    return {"n":len(rows),"days":len(dates),
            "model_rps":avg("rps_model"),"market_rps":avg("rps_market"),
            "delta_rps":avg("rps_model_minus_market"),
            "day_cluster_bootstrap95":[boot[int(.025*repetitions)],boot[int(.975*repetitions)-1]],
            "scoring_convention":"3-class ordinal RPS cumulative H,D,A divided by K-1=2; additional proper score, not sole standard.",
            "per_match":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--frozen-predictions",type=Path,required=True)
    p.add_argument("--cutoff-predictions",type=Path)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    frozen=json.loads(x.frozen_predictions.read_text(encoding="utf-8"))
    result={"primary":audit(frozen["rows"]),
            "frozen_upstream_model":frozen["upstream_original"],
            "primary_old_metrics":{"independent":frozen["independent"],"market":frozen["market"]},
            "no_training_or_model_refit":True}
    if x.cutoff_predictions:
        cutoff=json.loads(x.cutoff_predictions.read_text(encoding="utf-8"))
        result["cutoff60"]=audit(cutoff["rows"])
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:({i:v for i,v in val.items() if i!="per_match"} if k in ("primary","cutoff60") else val)
                      for k,val in result.items()},ensure_ascii=False))
if __name__=="__main__":
    main()
