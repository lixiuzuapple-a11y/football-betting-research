"""Stage TASK0034: frozen offline ESPN->Sporttery->Football-Data identity audit.

No score or odds are used in identity resolution. All source evidence is SHA
checked and both teams plus league plus exact kickoff must agree. No fuzzy
name matching. Count scored/market intersection AFTER freezing identity bridge.
"""
import argparse,collections,csv,hashlib,json
from pathlib import Path
from tools.task0034_espn_bridge import fixture_metadata,espn_identity,LEAGUES
from tools.task0034_identity_aliases import sporttery_to_espn,espn_to_fd

def evaluate(roots, history, probes, scores, snapshots):
    fixture=fixture_metadata(roots)
    artifact=json.loads((probes/"TASK0034-ESPN-BRIDGE.json").read_text(encoding="utf-8"))
    idx=collections.defaultdict(list)
    for meta in artifact["fetches"]:
        if meta.get("http")!=200:continue
        data=(probes/meta["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest()!=meta["sha256"]:
            raise ValueError("ESPN raw source modified "+meta["path"])
        for event in json.loads(data).get("events",[]):
            try:key=espn_identity(meta["league"],event)
            except (KeyError,ValueError,IndexError):continue
            if not any(str(e["id"])==str(event["id"]) for e in idx[key]):
                idx[key].append(event)
    fd_names={};prior_stats={}
    for league,(_,name) in LEAGUES.items():
        known=set();frequency=collections.Counter()
        for season in ("2526","2627"):
            with (history/(name+"-"+season+".csv")).open(encoding="utf-8-sig",newline="") as f:
                for row in csv.DictReader(f):
                    known.update((row["HomeTeam"],row["AwayTeam"]))
                    if season=="2526" and row.get("FTHG","").isdigit() and row.get("FTAG","").isdigit():
                        frequency[row["HomeTeam"]]+=1
                        frequency[row["AwayTeam"]]+=1
        fd_names[league]=known
        prior_stats[league]=frequency
    joins=[];rejects=[];identity_per_official_team={};identity_per_espn_team={}
    for fid,f in sorted(fixture.items()):
        league=f["leagueAbbName"]
        if league not in LEAGUES:continue
        k=(league,f["matchDate"],f["matchTime"],sporttery_to_espn(league,f["homeTeamAbbEnName"]),
           sporttery_to_espn(league,f["awayTeamAbbEnName"]))
        found=idx.get(k,[])
        if len(found)!=1:
            rejects.append({"matchId":fid,"reason":"no_unique_league_kickoff_and_two_team_code_match",
                            "n_matches":len(found),"key":k})
            continue
        event=found[0]
        teams={co["homeAway"]:co["team"] for co in event["competitions"][0]["competitors"]}
        home=espn_to_fd(league,teams["home"].get("displayName",""),fd_names[league])
        away=espn_to_fd(league,teams["away"].get("displayName",""),fd_names[league])
        if not home or not away or home==away:
            rejects.append({"matchId":fid,"reason":"unmapped_or_ambiguous_football_data_team","key":k,
                            "names":[teams["home"].get("displayName"),teams["away"].get("displayName")]})
            continue
        if any((
            (map_,key,value,map_.get(key))
            for map_,key,value in (
                (identity_per_official_team,(league,f["homeTeamId"]),teams["home"]["id"]),
                (identity_per_official_team,(league,f["awayTeamId"]),teams["away"]["id"]),
                (identity_per_espn_team,(league,str(teams["home"]["id"])),f["homeTeamId"]),
                (identity_per_espn_team,(league,str(teams["away"]["id"])),f["awayTeamId"])
            ) if map_.get(key) not in (None,value)
        )):
            raise ValueError("conflicting inter-source team identity "+fid)
        for official,espn in ((f["homeTeamId"],teams["home"]["id"]),(f["awayTeamId"],teams["away"]["id"])):
            identity_per_official_team[(league,official)]=espn
            identity_per_espn_team[(league,str(espn))]=official
        joins.append({"matchId":fid,"league":league,"day":f["matchDate"],"time":f["matchTime"],
                      "espn_event_id":str(event["id"]),"official_home_team_id":f["homeTeamId"],
                      "official_away_team_id":f["awayTeamId"],
                      "espn_home_team_id":str(teams["home"]["id"]),"espn_away_team_id":str(teams["away"]["id"]),
                      "fd_home":home,"fd_away":away,
                      "last_season_home_games":prior_stats[league][home],
                      "last_season_away_games":prior_stats[league][away],
                      "status":event.get("status",{}).get("type",{}).get("name"),
                      "code_alias_used":k[3]!=f["homeTeamAbbEnName"] or k[4]!=f["awayTeamAbbEnName"]})
    official_scores={str(x["matchId"]):x["score"] for x in json.loads(scores.read_text(encoding="utf-8"))}
    strict={str(x["matchId"]):x for x in
            json.loads(snapshots.read_text(encoding="utf-8"))["policies"]["strict"]["rows_for_bootstrap"]}
    matched_scored=[j for j in joins if j["matchId"] in official_scores]
    matched_had=[j for j in joins if j["matchId"] in strict]
    trainable=[j for j in matched_had if min(j["last_season_home_games"],j["last_season_away_games"])>=5]
    same_identity_count=len(set(j["matchId"] for j in joins))
    if same_identity_count!=len(joins):raise ValueError("duplicate Sporttery match bridge")
    return {"frozen_fixtures":len(fixture),"supported_league_fixtures":sum(f["leagueAbbName"] in LEAGUES for f in fixture.values()),
            "espn_raw_hash_checked":sum(f.get("http")==200 for f in artifact["fetches"]),
            "accepted_identity_bridge_count":len(joins),"strict_code_only_join_count":len(artifact["exact_joins"]),
            "cross_source_team_id_conflicts":0,
            "bridge_and_verified_score":len(matched_scored),"bridge_and_strict_HAD":len(matched_had),
            "bridge_had_and_prior_both_teams_5plus":len(trainable),
            "frozen_score_candidates_total":len(official_scores),"strict_HAD_total":len(strict),
            "joined_fixtures":joins,"rejected":rejects,
            "method":"Exact league + scheduled Beijing kickoff + 2 independently documented team-code aliases and ESPN displayName -> Football-Data team; neither odds nor final scores enter identity selection.",
            "score_and_odds_are_used_only_for_post_identity_coverage":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,action="append",required=True)
    for field in ("history","probes","scores","snapshots","out"):
        p.add_argument("--"+field,type=Path,required=True)
    a=p.parse_args()
    result=evaluate(a.root,a.history,a.probes,a.scores,a.snapshots)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("joined_fixtures","rejected")},ensure_ascii=False))
if __name__=="__main__":main()
