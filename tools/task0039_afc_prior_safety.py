"""TASK0039: external Asian interleague history / source-entity safety gate.

Source ESPN 2025,2026 yearly AFC completed fixture payloads SHA frozen to E drive.
No sportsbetting execution. Train un-tuned, fixed Elo+D probabilities for research
only; source IDs are manually anchored to prior official + HF team namespace.
Crucial: quarantine CSV-only HF rows because exact HF team IDs are reused across
unrelated domestic countries in the same season (demonstrated on prior code).
"""
from __future__ import annotations
import argparse,collections,datetime as dt,hashlib,json,math,random
from pathlib import Path
from tools.task0038_common_elo_model_gate import K,HOME_ADV,DRAW_WEIGHT,INIT,metrics,dav_probs,DSU
from tools.task0038_teams import HF_TEAM_BRIDGE

# Stable ESPN team IDs, separately checked HF team IDs/names and correct country.
# FC Nasaf / Al-Shorta SC are deliberately UNMAPPED (no vetted HF team match).
# Do not use same displayName "Al Ahli" for Bahrain 100005580; Jeddah=922.
ESPN_AFC_TO_HF={
"8371":(1537,"Sharjah FC"),"7129":(1546,"Al-Gharafa"),
"7134":(1532,"Al Wahda FC"),"2276":(935,"Al-Ittihad FC"),
"8346":(922,"Al-Ahli Jeddah"),"7135":(1550,"Al Sadd"),
"11143":(1588,"Melbourne City"),"7114":(494,"Sanfrecce Hiroshima"),
"131373":(1513,"Gangwon FC"),"977":(805,"Shanghai Shenhua"),
"22167":(4385,"Machida Zelvia"),"6972":(1510,"FC Seoul"),
"7138":(6028,"Buriram United"),"17689":(5980,"Johor Darul Takzim FC"),
"790":(1528,"Shabab Al Ahli Dubai"),"15107":(1574,"Tractor Sazi"),
"929":(933,"Al-Hilal Saudi FC"),"12008":(1548,"Al-Duhail SC"),
"7120":(1505,"Ulsan Hyundai FC"),"21355":(825,"Chengdu Rongcheng"),
"15515":(824,"Shanghai Port"),"7477":(493,"Vissel Kobe")
}
SKIP_ESPN_AFC_IDS={"8217":"FC Nasaf","9655":"Al-Shorta SC"}
OFFICIAL_TARGET_AFC=6
SOURCE_CUTOFF=dt.datetime(2026,7,5)
FIRST_TRAIN=dt.datetime(2025,7,1)

def parse_espn_prior(folder):
    manifest=json.loads((folder/"ESPN-AFC-MANIFEST.json").read_text(encoding="utf-8"))
    events={}
    for origin in manifest["sources"]:
        path=folder/("ESPN-AFC-RAW-"+origin["year"]+".json")
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=origin["response_sha256"]:
            raise ValueError("ESPN prior source SHA mismatch "+str(path))
        j=json.loads(raw)
        if len(j["events"])!=origin["n_raw"]:raise ValueError("ESPN count changed")
        for event in j["events"]:
            t=dt.datetime.fromisoformat(event["date"].replace("Z","+00:00")).replace(tzinfo=None)
            if not FIRST_TRAIN<=t<SOURCE_CUTOFF:continue
            status=event.get("status",{}).get("type",{})
            if status.get("name")!="STATUS_FULL_TIME" or status.get("shortDetail")!="FT":continue
            sides={c["homeAway"]:c for c in event["competitions"][0]["competitors"]}
            if any(sides[h].get("score") is None for h in ("home","away")):
                raise ValueError("final game without score")
            z={"espn_id":str(event["id"]),"utc":t,
                "espn_hid":str(sides["home"]["team"]["id"]),
                "espn_aid":str(sides["away"]["team"]["id"]),
                "gh":int(sides["home"]["score"]),"ga":int(sides["away"]["score"])}
            if z["espn_id"] in events and z!=events[z["espn_id"]]:
                raise ValueError("ESPN event changed between calendar queries")
            events[z["espn_id"]]=z
    return sorted(events.values(),key=lambda z:(z["utc"],z["espn_id"])),len(manifest["sources"])

def distrust_country_mismatches(rows,tracked,minimum=5):
    """Report multi-country IDs, not a free-standing club resolver."""
    by=collections.defaultdict(collections.Counter)
    for h,a,country,*unused in rows:
        if country=="World":continue
        normalized=country.strip().casefold().replace("-", " ")
        if normalized=="uae":normalized="united arab emirates"
        by[h][normalized]+=1;by[a][normalized]+=1
    return {str(tid):dict(n) for tid in sorted(tracked) for n in [by[tid]]
            if len([cnt for cnt in n.values() if cnt>=minimum])>1}

def fit_chronological(train,targets):
    """Simultaneous kickoffs must not leak updates from each other."""
    items=sorted(train,key=lambda z:(z[0],z[1],z[2]))
    graph=DSU();elo=collections.defaultdict(lambda:INIT)
    played=collections.Counter()
    pos=0
    while pos<len(items):
        end=pos+1
        while end<len(items) and items[end][0]==items[pos][0]:end+=1
        updates=collections.defaultdict(float)
        for when,h,a,gh,ga in items[pos:end]:
            if not FIRST_TRAIN<=when<SOURCE_CUTOFF:raise ValueError("future/old data")
            prob=dav_probs(elo[h],elo[a])
            y=1 if gh>ga else .5 if gh==ga else 0
            change=K*(y-prob[0]-prob[1]/2)
            updates[h]+=change;updates[a]-=change
            graph.union(h,a);played[h]+=1;played[a]+=1
        for tid,step in updates.items():elo[tid]+=step
        pos=end
    return graph,elo,played

def audit(history,espn_dir,cups,market):
    import duckdb
    folder=Path(history)
    hf_manifest=json.loads((folder/"hf_manifest.json").read_text(encoding="utf-8"))
    for row in hf_manifest:
        payload=(folder/row["file"]).read_bytes()
        if hashlib.sha256(payload).hexdigest()!=row["sha256"]:
            raise ValueError("HF source sha mismatch "+row["file"])
    sq=lambda x:str((folder/(x+".parquet")).resolve()).replace("\\","/")
    d=duckdb.connect()
    team_names=dict(d.execute(f"SELECT id,name FROM read_parquet('{sq('teams')}')").fetchall())
    for _,(tid,name) in ESPN_AFC_TO_HF.items():
        if team_names.get(tid)!=name:raise ValueError("AFC historical ID no match to HF team name")
    if len(set(t for t,_ in ESPN_AFC_TO_HF.values()))!=len(ESPN_AFC_TO_HF):
        raise ValueError("two ESPN clubs use one HF id")
    if HF_TEAM_BRIDGE["Al Ahli"]!={"id":922,"hf_name":"Al-Ahli Jeddah"}:
        raise ValueError("Saudi vs Bahrain club still confused")
    for desc,z in HF_TEAM_BRIDGE.items():
        if team_names.get(z["id"])!=z["hf_name"]:raise ValueError("Stage38 team id mismatch "+desc)
    # Read all history once; all output relies on frozen raw data, not fresh API.
    obs=d.execute(f"""SELECT f.date_utc,f.home_team_id,f.away_team_id,f.goals_home,f.goals_away,
                       f.in_csv,f.in_pq,l.country, f.id
        FROM read_parquet('{sq('fixtures')}') f
        JOIN read_parquet('{sq('leagues')}') l on l.id=f.league_id
        WHERE f.is_played=true AND f.goals_home IS NOT NULL AND f.goals_away IS NOT NULL
          AND f.date_utc >= timestamp '2025-07-01' AND f.date_utc < timestamp '2026-07-05'
        ORDER BY f.date_utc,f.id""").fetchall()
    # Mandatory source integrity BEFORE training.
    domestic=[(h,a,country) for when,h,a,gh,ga,csv,pq,country,rid in obs]
    impacted=distrust_country_mismatches(domestic,{v["id"] for v in HF_TEAM_BRIDGE.values()})
    # A source-limited sensitivity cohort, NOT independent assertion that in_pq is correct.
    prefiltered=[r for r in obs if not (r[5] is True and r[6] is False)]
    # Explicit globally detected unrelated cross-country HF team collision.
    # ID 1051 occurs in both Uruguay and New Zealand domestic fixtures.
    quarantined_ids={1051}
    filtered=[r for r in prefiltered if r[1] not in quarantined_ids and r[2] not in quarantined_ids]
    global_tracked={r[1] for r in obs}|{r[2] for r in obs}
    global_collisions_before=distrust_country_mismatches(domestic,global_tracked)
    global_collisions_after=distrust_country_mismatches([(r[1],r[2],r[7]) for r in filtered],global_tracked)
    # A sufficient safety gate for this diagnostic, not a licence or identity guarantee.
    if global_collisions_after:raise ValueError("unresolved five-game global cross-country ID collisions")
    scoped=distrust_country_mismatches([(r[1],r[2],r[7]) for r in filtered],
                                         {v["id"] for v in HF_TEAM_BRIDGE.values()})
    def unique_history(recs):
        groups=collections.defaultdict(list)
        for r in recs:
            when,h,a,gh,ga,*unused=r
            if h==a:raise ValueError("self-match")
            groups[(when,h,a)].append((gh,ga))
        if any(len(set(p))!=1 for p in groups.values()):
            raise ValueError("HF duplicate conflicting result")
        return [(when,h,a,*scores[0]) for (when,h,a),scores in groups.items()]
    source_prior,rawfiles=parse_espn_prior(Path(espn_dir))
    merged_afc=[];rejected=[]
    for z in source_prior:
        home=ESPN_AFC_TO_HF.get(z["espn_hid"])
        away=ESPN_AFC_TO_HF.get(z["espn_aid"])
        if home is None or away is None:
            rejected.append(z["espn_id"]);continue
        merged_afc.append((z["utc"],home[0],away[0],z["gh"],z["ga"]))
    # ESPN prior source has no crossprovider historic match ID from HF; detect
    # exact same kickoff/teams before merge, rather than double-counting.
    first=unique_history(filtered)
    known={(t,h,a):(gh,ga) for t,h,a,gh,ga in first}
    new=[]
    already=[]
    for t,h,a,gh,ga in merged_afc:
        if (t,h,a) in known:
            if known[(t,h,a)]!=(gh,ga):raise ValueError("ESPN/HF actual score conflict")
            already.append((t,h,a))
        else:new.append((t,h,a,gh,ga))
    combined=first+new
    graph0,elo0,played0=fit_chronological(first,[])
    graph,elo,played=fit_chronological(combined,[])
    cup=json.loads(Path(cups).read_text(encoding="utf-8"))
    rows=[r for r in cup["accepted"] if r["league"]=="亚冠精英"]
    if len(rows)!=OFFICIAL_TARGET_AFC:raise ValueError("Frozen AFC six changed")
    odds={str(z["matchId"]):z for z in json.loads(Path(market).read_text(encoding="utf-8"))["policies"]["strict"]["rows_for_bootstrap"]}
    if len(odds)!=126:raise ValueError("Frozen market baseline count")
    details=[];pairs=[]
    for z in rows:
        mid=z["matchId"];home,away=z["ESPN_names"]
        h=HF_TEAM_BRIDGE[home]["id"];a=HF_TEAM_BRIDGE[away]["id"]
        record={"matchId":mid,"names":[home,away],"hf_ids":[h,a],
                "prior_games":[played[h],played[a]],"prior_connected_before_AFC":graph0.find(h)==graph0.find(a),
                "prior_connected_after_AFC":graph.find(h)==graph.find(a),
                "has_strict_HAD":mid in odds,"has_verified_result":z["has_official_score"]}
        if record["prior_connected_after_AFC"] and min(record["prior_games"])>=5 and mid in odds:
            actual=z["official_score"]
            y=0 if actual[0]>actual[1] else 2 if actual[0]<actual[1] else 1
            if odds[mid]["y"]!=y:raise ValueError("Scored cup differs from market label")
            record.update({"model":dav_probs(elo[h],elo[a]),"market":odds[mid]["p"],"y":y,"day":z["kickoff_utc"][:10]})
            pairs.append(record)
        details.append(record)
    # Independent data-provenance sensitivity only: compare previous UEFA /
    # Libertadores set under this more restrictive historical source gate.
    # Not a new forward model or directly combinable with the five AFC games.
    sensitivity=[]
    for z in cup["accepted"]:
        if z["league"]=="亚冠精英":continue
        mid=z["matchId"]
        home,away=z["ESPN_names"]
        h,a=HF_TEAM_BRIDGE[home]["id"],HF_TEAM_BRIDGE[away]["id"]
        if mid not in odds or min(played[h],played[a])<5 or graph.find(h)!=graph.find(a):
            continue
        actual=z["official_score"]
        y=0 if actual[0]>actual[1] else 2 if actual[0]<actual[1] else 1
        if odds[mid]["y"]!=y:raise ValueError("cup label mismatch on provenance sensitivity")
        sensitivity.append({"matchId":mid,"day":z["kickoff_utc"][:10],"y":y,
                            "model":dav_probs(elo[h],elo[a]),"market":odds[mid]["p"]})
    return {"input_source":"HF July frozen + ESPN AFC 2025/2026 yearly scoreboard events",
        "HF_raw_history":len(obs),"HF_filtered_history":len(filtered),
        "HF_csv_only_quarantined_rows":len(obs)-len(prefiltered),
        "HF_collision_ID_1051_quarantined_rows":len(prefiltered)-len(filtered),
        "HF_global_5game_country_conflicts_before":len(global_collisions_before),
        "HF_global_5game_country_conflicts_after":len(global_collisions_after),
        "HF_global_conflicts_before_examples":dict(list(global_collisions_before.items())[:12]),
        "HF_team_ID_multiple_domestic_countries_pre_filter":impacted,
        "HF_team_ID_multiple_domestic_countries_post_filter":scoped,
        "hf_unique_training_after_filter":len(first),
        "afc_original_files":rawfiles,"afc_eligible_historical_final":len(source_prior),
        "afc_mapped_both_teams":len(merged_afc),
        "afc_skipped_unverified_hf_club":len(rejected),
        "afc_unmapped_event_ids":rejected,"afc_prior_doublecounted_against_HF":len(already),
        "afc_unique_edges_added":len(new),
        "actual_asof_training_latest_exclusive":"2026-07-05",
        "case_days":len(set(r["kickoff_utc"][:10] for r in rows)),
        "original_cup_AFC_games":len(rows),
        "connected_before":sum(z["prior_connected_before_AFC"] for z in details),
        "connected_after":sum(z["prior_connected_after_AFC"] for z in details),
        "comparable_frozen_HAD_after_AFC":len(pairs),
        "model_metrics":metrics(pairs,"model"),"market_metrics":metrics(pairs,"market"),
        "paired_delta_logloss":metrics(pairs,"model")["logloss"]-metrics(pairs,"market")["logloss"] if pairs else None,
        "prior_27_source_sensitivity_count":len(sensitivity),
        "prior_27_source_sensitivity_ids":[x["matchId"] for x in sensitivity],
        "prior_27_source_sensitivity_model":metrics(sensitivity,"model"),
        "prior_27_source_sensitivity_market":metrics(sensitivity,"market"),
        "policy":"Research-only diagnostic. No tuning, no betting. Date-cluster CI omitted for six matches or fewer.",
        "asof_limitation":"ESPN historical prior results fetched post Oct2026, no contemporaneous publication archive. HF publisher source rights and ID quality unverified.",
        "details":details}

def main():
    a=argparse.ArgumentParser()
    for k in ("history","afc","cups","market","out"):a.add_argument("--"+k,type=Path,required=True)
    arg=a.parse_args()
    z=audit(arg.history,arg.afc,arg.cups,arg.market)
    arg.out.parent.mkdir(parents=True,exist_ok=True)
    arg.out.write_text(json.dumps(z,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in z.items() if k not in ("details","afc_unmapped_event_ids")},ensure_ascii=False))
    for row in z["details"]:print("AFC_RESULT",row)
if __name__=="__main__":main()
