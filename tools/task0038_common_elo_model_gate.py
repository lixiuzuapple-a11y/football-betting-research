"""TASK0038 evidence-limited common-scale 1X2 diagnostic.

Frozen research-only baseline: 2025-07-01 to 2026-07-05 outcomes, including
domestic and all inter-league cup fixtures, pooled Elo initialized 1500,
K=20, home bonus=50 Elo, Davidson draw multiplier=0.7, no fit/tuning on
Sporttery October fixtures and no odds input. This is an empirical control
for cross-league comparability, not a competitive/prospective trading model.

ESPN/official identities were approved and frozen in TASK0037 before any
model/market scoring. Third party source rights NOT proven for production.
"""
import argparse,collections,datetime as dt,hashlib,json,math,random
from pathlib import Path
from tools.task0038_teams import HF_TEAM_BRIDGE

CUTOFF=dt.datetime(2026,7,5)
TRAIN_START=dt.datetime(2025,7,1)
K=20.0
HOME_ADV=50.0
DRAW_WEIGHT=.7
INIT=1500.0

def dav_probs(h,a,adv=HOME_ADV,draw_weight=DRAW_WEIGHT):
    hw=10**((h-a+adv)/400)
    dw=draw_weight*math.sqrt(hw)
    den=hw+1+dw
    return [hw/den,dw/den,1/den]

def elo_update(h,a,gh,ga):
    p=dav_probs(h,a)
    target=1 if gh>ga else .5 if gh==ga else 0
    expected=p[0]+p[1]/2
    delta=K*(target-expected)
    return h+delta,a-delta

def key_score(utc,h,a,gh,ga):
    return utc,h,a,gh,ga

class DSU:
    def __init__(self):self.p={}
    def find(self,x):
        if x not in self.p:self.p[x]=x
        if self.p[x]!=x:self.p[x]=self.find(self.p[x])
        return self.p[x]
    def union(self,a,b):
        x,y=self.find(a),self.find(b)
        if x!=y:self.p[y]=x

def metrics(rows,side):
    if not rows:return None
    eps=1e-15
    ll=sum(-math.log(max(eps,r[side][r["y"]])) for r in rows)/len(rows)
    brier=sum(sum((v-(i==r["y"]))**2 for i,v in enumerate(r[side])) for r in rows)/len(rows)
    rps=sum(((r[side][0]-(r["y"]==0))**2+
                (r[side][0]+r[side][1]-(r["y"]<=1))**2)/2 for r in rows)/len(rows)
    accuracy=sum(max(range(3),key=lambda j:r[side][j])==r["y"] for r in rows)/len(rows)
    return {"n":len(rows),"logloss":ll,"brier3":brier,"rps":rps,"accuracy":accuracy}

def boot_ci(rows,seed=20261023,draws=4000):
    rng=random.Random(seed)
    groups=collections.defaultdict(list)
    for r in rows:groups[r["day"]].append(r)
    days=sorted(groups)
    if not days:return None
    vals=[]
    for _ in range(draws):
        sample=[x for day in days for x in groups[rng.choice(days)]]
        vals.append(metrics(sample,"model")["logloss"]-metrics(sample,"market")["logloss"])
    vals.sort()
    return [vals[int(draws*.025)],vals[int(draws*.975)-1]]

def audit(history_dir,cup_path,had_path):
    import duckdb
    source=Path(history_dir)
    manifest=json.loads((source/"hf_manifest.json").read_text(encoding="utf-8"))
    for meta in manifest:
        f=source/meta["file"]
        if hashlib.sha256(f.read_bytes()).hexdigest()!=meta["sha256"]:
            raise ValueError("Historical dataset raw source SHA mismatch: "+str(f))
    data_path=str((source/"fixtures.parquet").resolve()).replace("\\","/")
    team_path=str((source/"teams.parquet").resolve()).replace("\\","/")
    conn=duckdb.connect()
    # Model team IDs do not come from string similarity at prediction time.
    teamrows=dict(conn.execute(f"SELECT id,name FROM read_parquet('{team_path}')").fetchall())
    if len(HF_TEAM_BRIDGE)!=70:raise ValueError("Unapproved team crosswalk")
    for name,mapping in HF_TEAM_BRIDGE.items():
        if teamrows.get(mapping["id"])!=mapping["hf_name"]:
            raise ValueError("HF source ID/name mismatch: "+name)
    obs=conn.execute(f"""SELECT id,date_utc,league_id,home_team_id,away_team_id,goals_home,goals_away
        FROM read_parquet('{data_path}')
        WHERE is_played=true AND date_utc>=timestamp '2025-07-01' AND date_utc<timestamp '2026-07-05'
        AND goals_home IS NOT NULL AND goals_away IS NOT NULL
        ORDER BY date_utc,id""").fetchall()
    groups=collections.defaultdict(list)
    for row in obs:
        rowid,when,league,h,a,gh,ga=row
        if h==a:raise ValueError("same team in historical fixture")
        groups[(when,h,a)].append((rowid,when,league,h,a,gh,ga))
    conflicts=[k for k,z in groups.items() if len(set((t[5],t[6]) for t in z))!=1]
    if conflicts:raise ValueError("Conflicting historical scores in duplicate records")
    # Source records from cross-listed leagues are the SAME football match;
    # choose deterministic lowest original row ID, not an arbitrary score.
    train=sorted((min(z,key=lambda r:r[0]) for z in groups.values()),key=lambda r:(r[1],r[0]))
    elo=collections.defaultdict(lambda:INIT)
    graph=DSU();played=collections.Counter()
    # For simultaneous matches use the pre-time Elo scores of both teams.
    index=0
    while index<len(train):
        end=index+1
        while end<len(train) and train[end][1]==train[index][1]:end+=1
        updates=collections.defaultdict(float)
        for _,when,lg,h,a,gh,ga in train[index:end]:
            if not (TRAIN_START<=when<CUTOFF):raise ValueError("Training date outside as-of period")
            p=dav_probs(elo[h],elo[a])
            target=1 if gh>ga else .5 if gh==ga else 0
            shift=K*(target-p[0]-p[1]/2)
            updates[h]+=shift;updates[a]-=shift
            graph.union(h,a)
            played[h]+=1;played[a]+=1
        for team,change in updates.items():elo[team]+=change
        index=end
    cup=json.loads(Path(cup_path).read_text(encoding="utf-8"))
    if cup["new_unique_cup_identity"]!=35 or len(cup["accepted"])!=35:
        raise ValueError("Cup identity not frozen")
    quotes={str(x["matchId"]):x for x in json.loads(Path(had_path).read_text(encoding="utf-8"))["policies"]["strict"]["rows_for_bootstrap"]}
    if len(quotes)!=126:raise ValueError("Strict HAD baseline changed")
    details=[];comparable=[]
    for z in cup["accepted"]:
        mid=z["matchId"]
        h_name,a_name=z["ESPN_names"]
        h,a=HF_TEAM_BRIDGE[h_name]["id"],HF_TEAM_BRIDGE[a_name]["id"]
        related=graph.find(h)==graph.find(a)
        n_h,n_a=played[h],played[a]
        before=(n_h>=5 and n_a>=5)
        accepted=related and before and mid in quotes
        row={"matchId":mid,"league":z["league"],"day":z["kickoff_utc"][:10],
             "home":h_name,"away":a_name,"hf_home":h,"hf_away":a,
             "prior_home_games":n_h,"prior_away_games":n_a,
             "common_graph_component":related,"both_prior5":before,
             "strict_had":mid in quotes,"comparable":accepted}
        if accepted:
            q=quotes[mid]
            if abs(sum(q["p"])-1)>1e-8:raise ValueError("Market baseline not normalized")
            o=z["official_score"]
            y=0 if o[0]>o[1] else 2 if o[0]<o[1] else 1
            if q["y"]!=y:raise ValueError("Frozen official score vs market label changed "+mid)
            row["model"]=dav_probs(elo[h],elo[a])
            row["market"]=q["p"];row["y"]=y
            comparable.append(row)
        details.append(row)
    # Derived values depend only on odds AFTER pre-game Elo fully finished.
    meta={"history_raw_rows":len(obs),"unique_training_matches":len(train),
          "exact_duplicate_training_rows":len(obs)-len(train),
          "conflicting_duplicate_scores":len(conflicts),
          "train_start":"2025-07-01","train_end_exclusive":"2026-07-05",
          "source_published":"2026-07-05T01:23:18Z","model":"fixed pooled 2025/26 Elo/Davidson 1X2",
          "hyperparams":{"initial_elo":INIT,"K":K,"home_advantage":HOME_ADV,"draw_weight":DRAW_WEIGHT},
          "outcome_freeze":True,"training_uses_any_2026_oct_results":False,
          "training_uses_market_odds":False,"train_edges_across_competitions":True,
          "cup_new_identity":len(details),"modelable_connected_and_history":sum(z["common_graph_component"] and z["both_prior5"] for z in details),
          "not_connected":[z["matchId"] for z in details if not z["common_graph_component"]],
          "with_strict_had":sum(z["strict_had"] for z in details),
          "paired_samples":len(comparable),
          "by_league":dict(collections.Counter(z["league"] for z in comparable)),
          "model_metrics":metrics(comparable,"model"),"market_metrics":metrics(comparable,"market"),
          "paired_logloss_delta":metrics(comparable,"model")["logloss"]-metrics(comparable,"market")["logloss"] if comparable else None,
          "day_clusters":len(set(z["day"] for z in comparable)),
          "day_cluster_bootstrap95":boot_ci(comparable),
          "details":details}
    return meta

def main():
    a=argparse.ArgumentParser()
    for name in ("history","cups","quotes","out"):
        a.add_argument("--"+name,type=Path,required=True)
    args=a.parse_args()
    v=audit(args.history,args.cups,args.quotes)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:z for k,z in v.items() if k!="details"},ensure_ascii=False))
    for r in v["details"]:
        if not r["comparable"]:print("REJECT",r["matchId"],r["league"],"connected",r["common_graph_component"],"prior5",r["both_prior5"],"market",r["strict_had"])
if __name__=="__main__":main()
