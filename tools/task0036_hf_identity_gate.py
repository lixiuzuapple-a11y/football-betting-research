"""TASK0036: additional league identity bridge, NO score-based join.

Offline audit of frozen source files from HuggingFace snapshot and ESPN public
match calendars. Requires duckdb in isolated E-drive venv, not in EV-Lab core.
Do not distribute source parquet from E-drive.
"""
from __future__ import annotations
import argparse,collections,datetime as dt,hashlib,json,unicodedata
from pathlib import Path

# Manually checked against Sporttery original code/name, public ESPN code/team
# ID and the actual provider-sourced football dataset teams file.
SCOPE={
    "瑞超":("Allsvenskan","Sweden"),
    "荷甲":("Eredivisie","Netherlands"),
    "美职":("MLS","USA")
}
ABBR={
    "瑞超":{"MJB":"MJA","DGF":"DEG","MAM":"MAL","KAL":"KFF"},
    "荷甲":{"FEY":"FEY","AZZ":"AZ","FTT":"FOR","FCT":"TWE",
            "UTR":"UTR","WII":"WIL","FCZ":"PEC","CBU":"CAM",
            "HEE":"HEE","EXE":"EXC","TLT":"TEL","FCG":"GRO",
            "AJX":"AJA","GAE":"GAE"},
    "美职":{"SLC":"STL","LAG":"LA","VWT":"VAN","NER":"NE","CHF":"CHI"}
}
# Explicit named alias only, never a fuzzy or outcome-derived name map.
NAME_TO_HF={
 "Mjällby AIF":"Mjallby","Degerfors IF":"Degerfors",
 "Malmö FF":"Malmo FF","Kalmar FF":"Kalmar",
 "Feyenoord Rotterdam":"Feyenoord","FC Utrecht":"Utrecht",
 "PEC Zwolle":"Zwolle","SC Cambuur":"Cambuur",
 "Ajax Amsterdam":"Ajax","FC Groningen":"Groningen",
 "FC Twente":"Twente","FC Heerenveen":"Heerenveen",
 "St. Louis CITY SC":"St. Louis City",
 "LA Galaxy":"Los Angeles Galaxy",
 "Vancouver Whitecaps":"Vancouver Whitecaps",
 "Chicago Fire FC":"Chicago Fire"
}

def norm(s):
    return ''.join(x for x in unicodedata.normalize("NFKD",s.lower()) if ord(x)<128 and x.isalnum())

def sporttery_codes(league,home,away):
    mapping=ABBR.get(league,{})
    if home not in mapping or away not in mapping:return None
    if mapping[home]==mapping[away]:raise ValueError("same mapped team")
    return mapping[home],mapping[away]

def normalize_named(name):
    return NAME_TO_HF.get(name,name)

def name_pair_matches(espn_home,espn_away,hf_home,hf_away):
    return norm(normalize_named(espn_home))==norm(hf_home) and norm(normalize_named(espn_away))==norm(hf_away)

def main_audit(data_dir,roots,old_bridge_path,scores_path,quotes_path):
    import duckdb
    from tools.audit_category_a_data_sources import fixture_metadata
    P=Path(data_dir)
    manifest=json.loads((P/"hf_manifest.json").read_text(encoding="utf-8"))
    for row in manifest:
        f=P/row["file"]
        if hashlib.sha256(f.read_bytes()).hexdigest()!=row["sha256"]:
            raise ValueError("source checksum invalid "+str(f))
    def parq(name):return str((P/(name+".parquet")).resolve()).replace("\\","/")
    db=duckdb.connect()
    leagues=db.execute(f"SELECT id,name,country FROM read_parquet('{parq('leagues')}')").fetchall()
    ids={(n,c):i for i,n,c in leagues}
    expected={k:ids[v] for k,v in SCOPE.items()}
    fixtures=db.execute(f"""SELECT f.id, f.date_utc, f.league_id, f.home_team_id, f.away_team_id,
         h.name AS hname,a.name AS aname, f.api_football_id, f.is_played FROM read_parquet('{parq('fixtures')}') f
         JOIN read_parquet('{parq('teams')}') h ON f.home_team_id=h.id
         JOIN read_parquet('{parq('teams')}') a ON f.away_team_id=a.id
         WHERE f.date_utc >= '2026-10-09' AND f.date_utc < '2026-10-21' """).fetchall()
    if sum(1 for r in fixtures if r[8])!=0:raise ValueError("2026 October HF snapshot unexpectedly has labels; data changed")
    hf=collections.defaultdict(list)
    for row in fixtures:hf[(row[1],row[2])].append(row)
    p=P/"ESPN"
    probes=json.loads((p/"ESPN_PROBES.json").read_text(encoding="utf-8"))
    events=collections.defaultdict(list)
    for entry in probes:
        if entry.get("status")!=200:continue
        raw=(p/entry["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry["sha256"]:
            raise ValueError("ESPN source checksum invalid "+entry["file"])
        for event in json.loads(raw).get("events",[]):
            try:
                sides={c["homeAway"]:c["team"] for c in event["competitions"][0]["competitors"]}
                t=dt.datetime.fromisoformat(event["date"].replace("Z","+00:00")).replace(tzinfo=None)
                key=(entry["league"],t,sides["home"]["abbreviation"],sides["away"]["abbreviation"])
                if not any(x["id"]==event["id"] for x in events[key]):
                    events[key].append({"id":event["id"],"home":sides["home"],"away":sides["away"]})
            except (KeyError,ValueError,IndexError):pass
    old=json.loads(Path(old_bridge_path).read_text(encoding="utf-8"))
    known={x["matchId"] for x in old["joined_fixtures"]}
    official=fixture_metadata(roots)
    if len(official)!=169 or len(known)!=76:raise ValueError("changed frozen cohort baseline")
    scored={str(z["matchId"]):z["score"] for z in json.loads(Path(scores_path).read_text(encoding="utf-8"))}
    quotes={str(z["matchId"]) for z in json.loads(Path(quotes_path).read_text(encoding="utf-8"))["policies"]["strict"]["rows_for_bootstrap"]}
    accepted=[];rejected=[]
    for fid,m in official.items():
        league=m["leagueAbbName"]
        if fid in known or league not in SCOPE:continue
        codepair=sporttery_codes(league,m["homeTeamAbbEnName"],m["awayTeamAbbEnName"])
        utc=dt.datetime.fromisoformat(m["matchDate"]+"T"+m["matchTime"])-dt.timedelta(hours=8)
        if not codepair:
            rejected.append({"mid":fid,"league":league,"reason":"no_manual_both_team_aliases"})
            continue
        espn=events.get((league,utc,*codepair),[])
        if len(espn)!=1:
            rejected.append({"mid":fid,"league":league,"reason":"no_unique_ESPN_both_team_id_and_time","n":len(espn)})
            continue
        e=espn[0];hf_candidates=hf.get((utc,expected[league]),[])
        confirmed=[z for z in hf_candidates if name_pair_matches(e["home"].get("displayName",""),e["away"].get("displayName",""),z[5],z[6])]
        if len(confirmed)!=1:
            rejected.append({"mid":fid,"league":league,"reason":"no_unique_HF_both_names_and_time","n":len(confirmed),
                             "ESPN":[e["home"].get("displayName"),e["away"].get("displayName")],"HF_samedate":len(hf_candidates)})
            continue
        h=confirmed[0]
        accepted.append({"matchId":fid,"league":league,"utc":utc.isoformat(),"ESPN_id":str(e["id"]),
                         "ESPN_home_id":str(e["home"]["id"]),"ESPN_away_id":str(e["away"]["id"]),
                         "HF_fixture_id":h[0],"HF_home_id":h[3],"HF_away_id":h[4],
                         "home_name":h[5],"away_name":h[6],
                         "official_home_id":m["homeTeamId"],"official_away_id":m["awayTeamId"],
                         "has_official_score":fid in scored,"has_frozen_strict_HAD":fid in quotes})
    if len({x["matchId"] for x in accepted})!=len(accepted):raise ValueError("duplicate bridge")
    hist_stats={}
    for league in SCOPE:
        lid=expected[league]
        stats=db.execute(f"""select count(*), count(distinct date_utc::date),
         min(date_utc), max(date_utc) from read_parquet('{parq('fixtures')}')
         where league_id=? and is_played=true and date_utc < timestamp '2026-07-05'
         and date_utc >= timestamp '2025-07-01' and goals_home is not null and goals_away is not null""",[lid]).fetchone()
        hist_stats[league]={"goals_history_since_2025_07_before_dataset_release":stats[0],
                            "distinct_dates":stats[1],"first":str(stats[2]),"last":str(stats[3])}
    # Frozen-publisher-date gate: per-team played history available by July 2026.
    count_rows=db.execute(f"""SELECT team_id,count(*) n FROM (
       SELECT home_team_id AS team_id FROM read_parquet('{parq('fixtures')}')
        WHERE is_played=true AND date_utc>=timestamp '2025-07-01'
          AND date_utc<timestamp '2026-07-05' AND goals_home IS NOT NULL AND goals_away IS NOT NULL
       UNION ALL
       SELECT away_team_id AS team_id FROM read_parquet('{parq('fixtures')}')
        WHERE is_played=true AND date_utc>=timestamp '2025-07-01'
          AND date_utc<timestamp '2026-07-05' AND goals_home IS NOT NULL AND goals_away IS NOT NULL
    ) GROUP BY team_id""").fetchall()
    played_by_team=dict(count_rows)
    for row in accepted:
        row["prior_asof_publication_home_games"]=played_by_team.get(row["HF_home_id"],0)
        row["prior_asof_publication_away_games"]=played_by_team.get(row["HF_away_id"],0)
        row["both_prior_at_least_5"]=min(row["prior_asof_publication_home_games"],
                                        row["prior_asof_publication_away_games"])>=5
    result={"baseline_unique_sporttery":len(official),"already_covered_0034":len(known),
            "not_covered_0034":len(official)-len(known),"old_six_leagues_unsupported":89,
            "HF_fixture_rows":db.execute(f"select count(*) from read_parquet('{parq('fixtures')}')").fetchone()[0],
            "HF_2026_oct_fixture_rows":len(fixtures),"HF_2026_oct_played":sum(bool(z[8]) for z in fixtures),
            "HF_pre2026_10_release_date":"2026-07-05","ESPN_raw_probe_files":sum(x.get("status")==200 for x in probes),
            "scoped_leagues":list(SCOPE),
            "strict_new_bridge":len(accepted),"bridge_both_prior5":sum(x["both_prior_at_least_5"] for x in accepted),"new_bridge_with_verified_score":sum(x["has_official_score"] for x in accepted),
            "new_bridge_with_frozen_HAD":sum(x["has_frozen_strict_HAD"] for x in accepted),
            "historical_prior_2025_26":hist_stats,"accepted":accepted,"rejected":rejected,
            "protocol":"Sporttery exact league+UTC kickoff+manual BOTH official team aliases to independent ESPN stable team IDs; then exact ESPN two-team names vs HF two-team names in same league and kickoff; scores/odds not used to join.",
            "rights_warning":"CC-BY 4.0 assertion from compiled HF publisher does not independently establish upstream API-Football proprietary redistribution rights; research gate only, no redistribution or production feed."}
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--root",type=Path,action="append",required=True)
    parser.add_argument("--baseline",type=Path,required=True)
    parser.add_argument("--scores",type=Path,required=True)
    parser.add_argument("--quotes",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    z=main_audit(a.data,a.root,a.baseline,a.scores,a.quotes)
    a.out.write_text(json.dumps(z,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in z.items() if k not in ("accepted","rejected")},ensure_ascii=False))
    for x in z["accepted"]:print("ACCEPTED",json.dumps(x,ensure_ascii=False))
    print("REJECTED",json.dumps(z["rejected"],ensure_ascii=False))
if __name__=="__main__":main()
