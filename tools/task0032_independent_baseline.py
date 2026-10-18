"""Independent strictly chronological prior-frequency forecast versus market quotes.
No market odds anywhere in the independent predictor. Same-day labels held out.
"""
import argparse, collections, json, math, random
from pathlib import Path

def score(p,y):
    return -math.log(max(p[y],1e-15)),sum((p[i]-(i==y))**2 for i in range(3)),int(max(range(3),key=lambda i:p[i])==y)

def evaluate(rows,min_prior=20,alpha=1.0):
    byday=collections.defaultdict(list)
    for r in rows:byday[r["date"]].append(r)
    prior=[0,0,0]; records=[]; day_details=[]
    for day,rs in sorted(byday.items()):
        training_n=sum(prior)
        if training_n>=min_prior:
            indep=[(n+alpha)/(training_n+3*alpha) for n in prior]
            for r in rs:
                ll_i,b_i,h_i=score(indep,r["y"])
                ll_m,b_m,h_m=score(r["p"],r["y"])
                records.append({"day":day,"mid":r["matchId"],"ll_ind":ll_i,"ll_market":ll_m,
                    "brier_ind":b_i,"brier_market":b_m,"hit_ind":h_i,"hit_market":h_m,
                    "independent_p":indep,"market_p":r["p"]})
            day_details.append({"day":day,"trained_before_day":training_n,"evaluated":len(rs),"independent_p":indep})
        for r in rs:prior[r["y"]]+=1
    n=len(records)
    if n==0:return {"n":0,"day_details":day_details}
    avg=lambda key:sum(r[key] for r in records)/n
    deltas=[r["ll_ind"]-r["ll_market"] for r in records] # positive market better
    # Cluster resampling by date: no pretend fixture independence within same day.
    groups=list({r["day"] for r in records})
    group_rows={d:[r for r in records if r["day"]==d] for d in groups}
    rng=random.Random(20261018)
    boots=[]
    for _ in range(5000):
        sample=[r for i in range(len(groups)) for r in group_rows[groups[rng.randrange(len(groups))]]]
        boots.append(sum(r["ll_ind"]-r["ll_market"] for r in sample)/len(sample))
    boots.sort()
    return {"n":n,"train_min":min_prior,"dirichlet_alpha":alpha,"test_days":len(groups),
        "independent":{"logloss":avg("ll_ind"),"brier":avg("brier_ind"),"accuracy":avg("hit_ind")},
        "market":{"logloss":avg("ll_market"),"brier":avg("brier_market"),"accuracy":avg("hit_market")},
        "delta_logloss_independent_minus_market":sum(deltas)/n,
        "day_cluster_bootstrap95":[boots[125],boots[4874]],
        "daily_forecast_details":day_details,"evaluated_records":records}

def main():
    p=argparse.ArgumentParser();p.add_argument("--scoring",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();x=json.loads(a.scoring.read_text(encoding="utf-8"))
    strict=x["policies"]["strict"]["rows_for_bootstrap"]
    results={"policy":"Strict frozen HAD snapshots; independent rolling class frequency with Dirichlet 1, grouped by kickoff calendar date, no odds used, 20 preceding matches minimum.",
        "strict_available":len(strict),"primary":evaluate(strict,20),
        "sensitivity_min10":evaluate(strict,10),"sensitivity_min30":evaluate(strict,30),
        "scientific_limit":"No team prior rating data: baseline only. No evidence about quality of an independently sourced Elo/Poisson or structured model."}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:({i:v for i,v in result.items() if i not in ("evaluated_records","daily_forecast_details")} if isinstance(result,dict) else result) for k,result in results.items()},ensure_ascii=False))
if __name__=="__main__":main()
