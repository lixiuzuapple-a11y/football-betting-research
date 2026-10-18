"""Offline evidence audit for GitHub data-source category A (not a scraper).
Never infer fixture identity from time alone or score a live ESPN event as final.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

CHINA_TZ=dt.timezone(dt.timedelta(hours=8))
FINAL_STATUSES={"STATUS_FULL_TIME","STATUS_FINAL"}

def fixture_metadata(roots):
    fixtures={}
    for root in roots:
        root=Path(root)
        c=sqlite3.connect("file:"+str((root/"official.sqlite3").resolve()).replace("\\","/")+"?mode=ro",uri=True)
        try:
            for (rel,) in c.execute(
                "select raw_path from captures where result='ok' and capture_id % 45=1 order by capture_id"
            ):
                if rel is None:continue
                with gzip.open(root/rel,"rb") as f:response=json.load(f)
                for group in response["value"]["matchInfoList"]:
                    for m in group["subMatchList"]:
                        key=str(m["matchId"])
                        item={k:str(m.get(k,"")) for k in
                            ("matchId","leagueAbbName","matchDate","matchTime",
                             "homeTeamAbbEnName","awayTeamAbbEnName",
                             "homeTeamId","awayTeamId")}
                        if key in fixtures and fixtures[key]!=item:
                            raise ValueError("inconsistent fixture identity "+key)
                        fixtures[key]=item
        finally:
            c.close()
    return fixtures

def _parse_event(event):
    try:
        teams={p["homeAway"]:p for p in event["competitions"][0]["competitors"]}
        home=teams["home"];away=teams["away"]
        tzdate=dt.datetime.fromisoformat(event["date"].replace("Z","+00:00")).astimezone(CHINA_TZ)
        return {"date":tzdate.strftime("%Y-%m-%d"),"time":tzdate.strftime("%H:%M:%S"),
                "abbr_home":str(home["team"]["abbreviation"]),
                "abbr_away":str(away["team"]["abbreviation"]),
                "status":event.get("status",{}).get("type",{}).get("name",""),
                "score_home":str(home.get("score","")),"score_away":str(away.get("score","")),
                "espn_id":str(event["id"])}
    except (KeyError,TypeError,ValueError):
        return None

def exact_matches(fixtures,event):
    """Return strict ID matches. Duplicate/ambiguous mapping is not acceptable."""
    item=_parse_event(event)
    if item is None:return []
    return [fid for fid,f in fixtures.items()
            if f["leagueAbbName"]=="英超"
            and f["matchDate"]==item["date"]
            and f["matchTime"]==item["time"]
            and f["homeTeamAbbEnName"]==item["abbr_home"]
            and f["awayTeamAbbEnName"]==item["abbr_away"]]

def final_score(event):
    parsed=_parse_event(event)
    if parsed is None or parsed["status"] not in FINAL_STATUSES:return None
    h,a=parsed["score_home"],parsed["score_away"]
    if not h.isdecimal() or not a.isdecimal():return None
    return [int(h),int(a)]

def analyze(probe_dir,roots,official_scores):
    probe_dir=Path(probe_dir)
    probes=json.loads((probe_dir/"SOURCE_PROBES.json").read_text(encoding="utf-8"))
    for probe in probes:
        raw=probe_dir/(probe["name"]+".raw")
        if probe.get("status")==200:
            if not raw.exists():raise ValueError("missing probe "+probe["name"])
            if hashlib.sha256(raw.read_bytes()).hexdigest()!=probe["sha256"]:
                raise ValueError("probe checksum changed "+probe["name"])
    fixtures=fixture_metadata(roots)
    labelled={str(z["matchId"]):z["score"] for z in json.loads(Path(official_scores).read_text(encoding="utf-8"))}
    result={"source_probes_ok":sum(x.get("status")==200 for x in probes),
            "source_probes_failed":sum(x.get("status")!=200 for x in probes),
            "fixture_meta_sample_unique":len(fixtures),
            "strict_join":[],"same_day_ambiguous_candidates":0,"scored_agree":0,"scored_conflict":0,
            "rejected_not_finished":0,"unmapped_espn_events":0}
    for day in ("20261010","20261018"):
        events=json.loads((probe_dir/("soccerdata_ESPN_"+day+".raw")).read_bytes())["events"]
        for event in events:
            match_ids=exact_matches(fixtures,event)
            if not match_ids:
                result["unmapped_espn_events"]+=1;continue
            if len(match_ids)!=1:
                result["same_day_ambiguous_candidates"]+=1;continue
            fid=match_ids[0]
            score=final_score(event)
            published=labelled.get(fid)
            check=None
            if score is None:result["rejected_not_finished"]+=1
            elif published is not None:
                check=(score==published)
                if check:result["scored_agree"]+=1
                else:result["scored_conflict"]+=1
            result["strict_join"].append({"official_match_id":fid,"espn_event_id":str(event["id"]),
                "match_status":_parse_event(event)["status"],"ESPN_fulltime":score,
                "Sporttery_verified_score":published,"agreement":check})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,action="append",required=True)
    p.add_argument("--probe-dir",type=Path,required=True)
    p.add_argument("--official-scores",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    r=analyze(args.probe_dir,args.root,args.official_scores)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
