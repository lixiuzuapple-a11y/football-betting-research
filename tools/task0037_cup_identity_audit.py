"""TASK0037: strict source-verified Sporttery/ESPN cup fixture identity audit.

The human-reviewed list was frozen BEFORE accessing post-event score labels.
Required evidence: original source SHA verified by separate raw extractor;
same league, same UTC kickoff, same official Chinese names, unique ESPN
event ID and both provider team IDs/name strings. Scores checked only after.
"""
import argparse,collections,datetime as dt,gzip,hashlib,json
from pathlib import Path
from tools.audit_category_a_data_sources import fixture_metadata
from tools.task0037_reviewed_cup_links import APPROVED

CHAMPIONS={"欧冠":"uefa.champions","欧罗巴":"uefa.europa","欧协联":"uefa.europa.conf",
           "亚冠精英":"afc.champions","解放者杯":"conmebol.libertadores"}

def parse_espn_event(event,league):
    sides={c["homeAway"]:c["team"] for c in event["competitions"][0]["competitors"]}
    when=dt.datetime.fromisoformat(event["date"].replace("Z","+00:00")).replace(tzinfo=None)
    return {"id":str(event["id"]),"league":league,"utc":when,
            "home_id":str(sides["home"]["id"]),"away_id":str(sides["away"]["id"]),
            "home":sides["home"]["displayName"],"away":sides["away"]["displayName"],
            "home_score":event["competitions"][0]["competitors"][[v["homeAway"] for v in event["competitions"][0]["competitors"]].index("home")].get("score"),
            "away_score":event["competitions"][0]["competitors"][[v["homeAway"] for v in event["competitions"][0]["competitors"]].index("away")].get("score"),
            "status":event.get("status",{}).get("type",{}).get("name")}

def index_verified_espn(base):
    rows=json.loads((base/"ESPN_MANIFEST.json").read_text(encoding="utf-8"))
    events={}
    failed=[]
    for desc in rows:
        if desc.get("status")!=200:
            failed.append(desc)
            continue
        raw=(base/desc["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=desc["sha256"]:raise ValueError("ESPN raw mismatch "+desc["file"])
        for event in json.loads(raw).get("events",[]):
            z=parse_espn_event(event,desc["league"])
            prior=events.get((z["league"],z["id"]))
            if prior is not None and prior!=z:raise ValueError("same ESPN event ID conflicting data")
            events[(z["league"],z["id"])]=z
    return events,rows,failed

def official_to_event_match(official,raw_label,approved,event):
    """Pure identity predicate, absolutely no outcomes or market prices."""
    if (official["homeTeamId"],official["awayTeamId"])!=(raw_label["official_hid"],raw_label["official_aid"]):
        return False
    if (official["homeTeamAbbEnName"],official["awayTeamAbbEnName"])!=(raw_label["official_hcode"],raw_label["official_acode"]):
        return False
    if [raw_label["official_h_zh"],raw_label["official_a_zh"]]!=approved["official_chinese"]:
        return False
    if [event["home"],event["away"]]!=approved["espn_display"]:
        return False
    if event["id"]!=approved["event_id"] or event["league"]!=official["leagueAbbName"]:
        return False
    utc=dt.datetime.fromisoformat(official["matchDate"]+"T"+official["matchTime"])-dt.timedelta(hours=8)
    return utc==event["utc"] and event["home_id"]!=event["away_id"]

def run(roots,rawlabels,espnbase,old0034,old0036,scores,quotes):
    official=fixture_metadata(roots)
    if len(official)!=169:raise ValueError("Sporttery fixture cohort changed")
    prior34=json.loads(Path(old0034).read_text(encoding="utf-8"))
    prior36=json.loads(Path(old0036).read_text(encoding="utf-8"))
    prior_ids={x["matchId"] for x in prior34["joined_fixtures"]}|{x["matchId"] for x in prior36["accepted"]}
    if len(prior_ids)!=87:raise ValueError("prior accepted cohort not 87")
    labels=json.loads(Path(rawlabels).read_text(encoding="utf-8"))
    events,manifest,failures=index_verified_espn(Path(espnbase))
    official_scores={str(x["matchId"]):x["score"] for x in json.loads(Path(scores).read_text(encoding="utf-8"))}
    official_had={str(x["matchId"]) for x in json.loads(Path(quotes).read_text(encoding="utf-8"))["policies"]["strict"]["rows_for_bootstrap"]}
    accepted=[];rejected=[];seen_events=set()
    for mid,a in sorted(APPROVED.items()):
        if mid in prior_ids:raise ValueError("double counted previously bridged "+mid)
        if mid not in official or mid not in labels:
            rejected.append({"matchId":mid,"reason":"missing_frozen_original"});continue
        lg=official[mid]["leagueAbbName"]
        if lg not in CHAMPIONS:raise ValueError("out of scope "+mid)
        e=events.get((lg,a["event_id"]))
        if e is None or not official_to_event_match(official[mid],labels[mid],a,e):
            rejected.append({"matchId":mid,"reason":"original-label/team-name/league/kickoff/ESPN mismatch"});continue
        ek=(lg,e["id"])
        if ek in seen_events:raise ValueError("same ESPN fixture mapped more than once")
        seen_events.add(ek)
        score=official_scores.get(mid)
        espn_score=None
        if e["home_score"] is not None and e["away_score"] is not None:
            espn_score=[int(e["home_score"]),int(e["away_score"])]
        accepted.append({"matchId":mid,"league":lg,"kickoff_utc":e["utc"].isoformat(),
          "official_home_id":official[mid]["homeTeamId"],"official_away_id":official[mid]["awayTeamId"],
          "original_zh":a["official_chinese"],"espn_id":e["id"],
          "ESPN_home_id":e["home_id"],"ESPN_away_id":e["away_id"],
          "ESPN_names":a["espn_display"],
          "has_official_score":score is not None,"has_strict_HAD":mid in official_had,
          "official_score":score,"ESPN_score":espn_score,"ESPN_status":e["status"]})
    # Cross-era team-ID consistency uses both previous frozen ledgers, not scores.
    team_maps=collections.defaultdict(set)
    for z in prior34["joined_fixtures"]:
        for a,b in (("official_home_team_id","espn_home_team_id"),("official_away_team_id","espn_away_team_id")):
            team_maps[str(z[a])].add(str(z[b]))
    for z in prior36["accepted"]:
        for a,b in (("official_home_id","ESPN_home_id"),("official_away_id","ESPN_away_id")):
            team_maps[str(z[a])].add(str(z[b]))
    for z in accepted:
        for a,b in (("official_home_id","ESPN_home_id"),("official_away_id","ESPN_away_id")):
            team_maps[str(z[a])].add(str(z[b]))
    conflicts={a:sorted(b) for a,b in team_maps.items() if len(b)>1}
    score_cross=[z for z in accepted if z["has_official_score"]]
    mismatch=[z["matchId"] for z in score_cross if z["ESPN_score"]!=z["official_score"] or z["ESPN_status"] not in ("STATUS_FULL_TIME","STATUS_FINAL")]
    return {"original_unique":169,"prior_strict_bridge":len(prior_ids),"covered_cup_target":len(APPROVED),
       "espn_manifest_requests":len(manifest),"espn_manifest_HTTP200":len(manifest)-len(failures),"source_errors":failures,
       "espn_unique_events":len(events),"new_unique_cup_identity":len(accepted),
       "total_identity_coverage":len(prior_ids)+len(accepted),
       "new_scored":len(score_cross),"new_strict_HAD":sum(z["has_strict_HAD"] for z in accepted),
       "post_identity_score_conflicts":mismatch,"cross_stage_team_id_conflicts":conflicts,
       "accepted":accepted,"rejected":rejected,
       "protocol":"Manually reviewed official original-Chinese team labels & Sporttery team IDs against ESPN independent English names & both stable team IDs; exact league, unique eventID, and UTC kickoff; no score/odds used until identity frozen.",
       "limits":"ESPN schedule was retrieved after matches; this is historical identity linkage, NOT proof sportsbook quote was executable or all historical scores available pre-match."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",action="append",type=Path,required=True)
    for k in ("labels","espn","prior34","prior36","scores","quotes","out"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    z=run(a.root,a.labels,a.espn,a.prior34,a.prior36,a.scores,a.quotes)
    a.out.write_text(json.dumps(z,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in z.items() if k not in ("accepted","rejected")},ensure_ascii=False))
    if z["rejected"]:print("REJECTED",z["rejected"])
    if z["cross_stage_team_id_conflicts"]:print("ID_CONFLICTS",z["cross_stage_team_id_conflicts"])
if __name__=="__main__":main()
