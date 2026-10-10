"""TASK-0022: official fixture manifest and strict result join; zero inferred scores."""
import argparse,gzip,hashlib,json,sqlite3
from pathlib import Path

def fixtures(db:Path,raw:Path):
    c=sqlite3.connect(f"file:{db.resolve().as_posix()}?mode=ro",uri=True)
    records={}
    for cap,when,sha,rel in c.execute("select capture_id,observed_at_utc,raw_sha256,raw_path from captures where result='ok' order by capture_id"):
        b=gzip.open(raw/rel,"rb").read()
        if hashlib.sha256(b).hexdigest()!=sha:raise ValueError(f"bad raw hash {cap}")
        doc=json.loads(b)
        for group in doc["value"]["matchInfoList"]:
            for match in group["subMatchList"]:
                mid=str(match["matchId"])
                fields={k:match.get(k) for k in ("matchId","matchNumStr","businessDate","matchDate","matchTime","leagueId","leagueAllName","homeTeamAllName","awayTeamAllName","homeTeamId","awayTeamId")}
                if mid in records:
                    before=records[mid]
                    for key in ("homeTeamId","awayTeamId","businessDate"):
                        if fields[key]!=before[key]:raise ValueError(f"identity instability {mid}: {key}")
                else:records[mid]=fields
    c.close()
    return records

def strict_join(index,results):
    out=[];seen=set()
    for r in results:
        mid=str(r.get("matchId",""))
        if mid in seen:raise ValueError("duplicate result matchId")
        seen.add(mid)
        f=index.get(mid);status="UNMATCHED"
        if f:
            status="MATCHED_IDENTITY_ONLY"
            for k in ("businessDate","homeTeamId","awayTeamId"):
                if r.get(k) is not None and str(r[k])!=str(f[k]):
                    status="CONFLICT";break
            if status=="MATCHED_IDENTITY_ONLY" and not (r.get("sectionsNo999") or r.get("fullTimeScore")):
                status="SCORE_NOT_VERIFIED"
        out.append({"matchId":mid,"status":status})
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument("--db",required=True,type=Path);p.add_argument("--raw",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path);p.add_argument("--results-json",type=Path)
    a=p.parse_args();items=fixtures(a.db,a.raw);o={"fixture_count":len(items),"fixtures":list(items.values()),
        "result_source":"not_provided","results_verified":0}
    if a.results_json:
        r=json.loads(a.results_json.read_text());o["result_source"]="supplied_file_unverified_provenance";o["join"]=strict_join(items,r)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"fixture_count":len(items),"results_verified":0,"out":str(a.out)}))
if __name__=="__main__":main()
