"""Actual sporttery-market vs ORIGINAL upstream callumfm Dixon-Coles on exact 0034 bridge.

Frozen 2025/26 goals-only season -> Oct 2026 predictions (never bookmaker odds).
Same sporttery fixtures and frozen Sporttery strict HAD de-vigged probabilities.
"""
import argparse,collections,csv,datetime as dt,json,random
from pathlib import Path
from tools.audit_category_b_original_dc import load,probabilities,metric

FILENAMES={"英超":"E0","英冠":"E1","意甲":"I1","法甲":"F1","西甲":"SP1","德甲":"D1"}

def paired_cluster_ci(rows,seed=20261019,repetitions=4000):
    if not rows:return None
    groups=collections.defaultdict(list)
    for r in rows:groups[r["day"]].append(r)
    days=sorted(groups)
    rng=random.Random(seed)
    values=[]
    for i in range(repetitions):
        sample=[x for _ in days for x in groups[rng.choice(days)]]
        values.append(metric(sample,"independent")["log_loss"]-metric(sample,"market")["log_loss"])
    values.sort()
    return [values[int(.025*repetitions)],values[int(.975*repetitions)-1]]

def run(bridge, history, snapshots, scores):
    import numpy as np
    from dixon_coles import DixonColesModel
    refs={str(j["matchId"]):j for j in bridge["joined_fixtures"] if
          min(j["last_season_home_games"],j["last_season_away_games"])>=5}
    q={str(x["matchId"]):x for x in snapshots["policies"]["strict"]["rows_for_bootstrap"]}
    result_by_id={str(r["matchId"]):r for r in scores}
    selected={mid:x for mid,x in refs.items() if mid in q and mid in result_by_id}
    models={};training_stats={};rows=[];failures=[]
    # No official current/future results or bookmaker odds flow into fitting.
    for league in sorted(set(x["league"] for x in selected.values())):
        train=load(history/(FILENAMES[league]+"-2526.csv"))
        if not train:raise RuntimeError("no actual history "+league)
        if max(x[0] for x in train)>=min(dt.date.fromisoformat(m["day"]) for m in selected.values() if m["league"]==league):
            raise ValueError("history not strictly pre-fixture "+league)
        mdl=DixonColesModel(seed=42)
        mdl.fit(
            home_teams=np.array([r[1] for r in train]),
            away_teams=np.array([r[2] for r in train]),
            home_goals=np.array([r[3] for r in train],dtype="int64"),
            away_goals=np.array([r[4] for r in train],dtype="int64"),
            dates=np.array([str(r[0]) for r in train],dtype="datetime64[D]"))
        training_stats[league]={"matches":len(train),"last_training_date":str(max(r[0] for r in train)),
                                "tested_count":sum(j["league"]==league for j in selected.values())}
        models[league]=mdl
    for mid,j in selected.items():
        try:
            prediction=probabilities(models[j["league"]].predict(j["fd_home"],j["fd_away"]))
            market=q[mid]["p"]
            y=q[mid]["y"];sc=result_by_id[mid]["score"]
            independently_verified_y=0 if sc[0]>sc[1] else 2 if sc[0]<sc[1] else 1
            if y!=independently_verified_y:raise ValueError("score / frozen market scoring disagree")
            if abs(sum(market)-1)>1e-8:raise ValueError("market de-vig not normalized")
            rows.append({"matchId":mid,"league":j["league"],"day":j["day"],
                         "fd_home":j["fd_home"],"fd_away":j["fd_away"],
                         "independent":prediction,"market":market,"y":y})
        except Exception as exc:failures.append({"matchId":mid,"error":str(exc)})
    if not rows:raise RuntimeError("no model vs market comparable fixtures")
    indep=metric(rows,"independent");mkt=metric(rows,"market")
    res={"frozen_joined_fixture_count":len(bridge["joined_fixtures"]),
         "frozen_score_candidates":len(scores),"frozen_strict_HAD":len(q),
         "valid_prior_team_history_and_quote":len(selected),"evaluated":len(rows),
         "rejected_during_original_model_predict":failures,"upstream_original":"callumfm/dixon-coles",
         "original_commit":"dea06c6e4b38085d6a4b84186cb9ead321a73ce4",
         "training":"Full prior 2025/26 league score rows only; no market or final 2026/27 results; seed=42 and upstream default parameters.",
         "training_by_league":training_stats,"independent":indep,"market":mkt,
         "paired_delta_logloss_independent_minus_market":indep["log_loss"]-mkt["log_loss"],
         "day_cluster_bootstrap95":paired_cluster_ci(rows),"days":len(set(z["day"] for z in rows)),
         "rows":rows,"warning":"Retrospective small selected subset, not prospective, no trading/EV claim; some Sporttery quotes are near kickoff."}
    return res

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--bridge",type=Path,required=True)
    p.add_argument("--history",type=Path,required=True)
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--scores",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    x=run(json.loads(a.bridge.read_text(encoding="utf-8")),a.history,
          json.loads(a.snapshots.read_text(encoding="utf-8")),
          json.loads(a.scores.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in x.items() if k not in ("rows","rejected_during_original_model_predict")},ensure_ascii=False))
    print("prediction_failures",x["rejected_during_original_model_predict"])
if __name__=="__main__":main()
