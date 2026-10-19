"""TASK0034 frozen-fixture ESPN source probe, strict join inventory.
No team fuzzy joins, no training, no bookmaker odds as model features.
"""
from __future__ import annotations
import argparse,collections,csv,datetime as dt,hashlib,json,re,urllib.request,unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tools.audit_category_a_data_sources import fixture_metadata,CHINA_TZ

LEAGUES={"英超":("eng.1","E0"),"英冠":("eng.2","E1"),"德甲":("ger.1","D1"),
         "西甲":("esp.1","SP1"),"意甲":("ita.1","I1"),"法甲":("fra.1","F1")}

def identity(fixture):
    return (fixture["leagueAbbName"],fixture["matchDate"],fixture["matchTime"],
            fixture["homeTeamAbbEnName"].upper(),fixture["awayTeamAbbEnName"].upper())

def espn_identity(league,event):
    teams={p.get("homeAway"):p.get("team",{}) for p in event.get("competitions",[{}])[0].get("competitors",[])}
    when=dt.datetime.fromisoformat(event["date"].replace("Z","+00:00")).astimezone(CHINA_TZ)
    return (league,when.strftime("%Y-%m-%d"),when.strftime("%H:%M:%S"),
            str(teams["home"].get("abbreviation","")).upper(),str(teams["away"].get("abbreviation","")).upper())

def load_team_names(folder):
    teams={}
    for league,(_,file) in LEAGUES.items():
        with (folder/(file+"-2627.csv")).open(encoding="utf-8-sig",newline="") as handle:
            rdr=csv.DictReader(handle)
            teams[league]=set(v for row in rdr for v in (row["HomeTeam"],row["AwayTeam"]))
    return teams

def canonical(value):
    value=unicodedata.normalize("NFKD",value)
    return "".join(c for c in value.lower() if ord(c)<128 and c.isalnum())

def gather(roots,history,out,workers=4):
    fixtures=fixture_metadata(roots)
    out.mkdir(parents=True,exist_ok=True)
    requests=set()
    for f in fixtures.values():
        if f["leagueAbbName"] not in LEAGUES:continue
        local=dt.datetime.fromisoformat(f["matchDate"]+"T"+f["matchTime"]).replace(tzinfo=CHINA_TZ)
        utc_day=local.astimezone(dt.timezone.utc).date().isoformat()
        requests.add((f["leagueAbbName"],f["matchDate"]))
        requests.add((f["leagueAbbName"],utc_day))
    requests=sorted(requests)
    def fetch(pair):
        league,date=pair;eid=LEAGUES[league][0]
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{eid}/scoreboard?dates={date.replace('-','')}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 EVLabResearch"}),timeout=22) as response:
                body=response.read()
            parsed=json.loads(body)
            rel=f"espn-{eid}-{date}.json"
            (out/rel).write_bytes(body)
            return {"league":league,"day":date,"http":200,"url":url,"sha256":hashlib.sha256(body).hexdigest(),
                    "path":rel,"n_events":len(parsed.get("events",[]))},parsed.get("events",[])
        except Exception as ex:
            return {"league":league,"day":date,"url":url,"error":type(ex).__name__+": "+str(ex)[:160]},[]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        fetched=list(executor.map(fetch,requests))
    by_key=collections.defaultdict(list)
    names=collections.defaultdict(dict)
    by_time=collections.defaultdict(list)
    all_codes=collections.defaultdict(set)
    for desc,events in fetched:
        league=desc["league"]
        for e in events:
            try:
                eid=espn_identity(league,e)
                if not any(old["id"]==str(e["id"]) for old in by_key[eid]):
                    by_key[eid].append({"id":str(e["id"]),"event":e,"desc":desc})
                by_time[eid[:3]].append(eid)
                for competitor in e["competitions"][0]["competitors"]:
                    team=competitor["team"];code=team["abbreviation"];names[league][code]=team.get("displayName",team.get("name",""))
                    all_codes[league].add(code)
            except (KeyError,IndexError,ValueError):
                pass
    joins=[];miss=[];ambiguous=[]
    for fid,f in fixtures.items():
        if f["leagueAbbName"] not in LEAGUES:continue
        k=identity(f);found=by_key.get(k,[])
        if len(found)==1:
            event=found[0]["event"]
            comps={v["homeAway"]:v["team"] for v in event["competitions"][0]["competitors"]}
            joins.append({"matchId":fid,"league":k[0],"day":k[1],"official_team_ids":[f["homeTeamId"],f["awayTeamId"]],
                          "home_code":k[3],"away_code":k[4],"espn_event_id":str(event["id"]),
                          "espn_home_id":str(comps["home"]["id"]),"espn_away_id":str(comps["away"]["id"]),
                          "espn_home_name":comps["home"].get("displayName"),"espn_away_name":comps["away"].get("displayName")})
        elif len(found)>1:ambiguous.append(fid)
        else:
            miss.append({"matchId":fid,"league":k[0],"day":k[1],"time":k[2],
                         "official_home":k[3],"official_away":k[4],
                         "same_time_espn_pairs":[list(v[3:]) for v in by_time.get(k[:3],[])]})
    csvteams=load_team_names(history)
    team_map=[];unmapped=[]
    for league,code_names in names.items():
        csvnames=csvteams[league]
        for code,display in code_names.items():
            options=[name for name in csvnames if canonical(display)==canonical(name)]
            if len(options)==1:team_map.append({"league":league,"espn_code":code,"espn_name":display,"csv_team":options[0]})
            else:unmapped.append({"league":league,"espn_code":code,"espn_name":display,"candidate_names":options})
    artifact={"fixtures":len(fixtures),"mapped_league_fixtures":sum(f["leagueAbbName"] in LEAGUES for f in fixtures.values()),
              "fetches":[p[0] for p in fetched],"exact_joins":joins,"unjoined":miss,"ambiguous_ids":ambiguous,
              "name_exact_crosswalk":team_map,"name_unmapped":unmapped,"available_external_leagues":LEAGUES}
    (out/"TASK0034-ESPN-BRIDGE.json").write_text(json.dumps(artifact,indent=2,ensure_ascii=False),encoding="utf-8")
    return artifact

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",action="append",type=Path,required=True)
    a.add_argument("--history",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    arg=a.parse_args();z=gather(arg.root,arg.history,arg.out)
    print(json.dumps({"fixtures":z["fixtures"],"mapped_league_fixtures":z["mapped_league_fixtures"],
            "source_days":len(z["fetches"]),"fetch_errors":[f for f in z["fetches"] if f.get("http")!=200],
            "exact_fixture_joins":len(z["exact_joins"]),"ambiguous":len(z["ambiguous_ids"]),
            "name_exact_team_joins":len(z["name_exact_crosswalk"]),"name_unmapped":len(z["name_unmapped"])},ensure_ascii=False))
if __name__=="__main__":main()
