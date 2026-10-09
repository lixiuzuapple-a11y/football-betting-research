"""TASK-0015 read-only five-pool raw reconstruction; no prices/single flags inferred.
Run: python tools/task0015_reconstruct.py --db ledger.sqlite3 --raw raw/ --out-dir /tmp/output
Detailed records stay outside Git; SHA summaries may be committed.
"""
import argparse
import collections
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

POOLS=("HAD","HHAD","TTG","CRS","HAFU")
FIELDS={
"HAD":("h","d","a"),"HHAD":("h","d","a"),
"TTG":tuple("s"+str(i) for i in range(8)),
"CRS":("s00s00","s00s01","s00s02","s00s03","s00s04","s00s05",
"s01s00","s01s01","s01s02","s01s03","s01s04","s01s05",
"s02s00","s02s01","s02s02","s02s03","s02s04","s02s05",
"s03s00","s03s01","s03s02","s03s03","s04s00","s04s01",
"s04s02","s05s00","s05s01","s05s02","s1sh","s1sd","s1sa"),
"HAFU":("hh","hd","ha","dh","dd","da","ah","ad","aa")
}

def reconstruct(db,raw,out_dir):
    con=sqlite3.connect("file:"+db.resolve().as_posix()+"?mode=ro&immutable=1",uri=True)
    rows=con.execute("""SELECT capture_id,response_received_at,raw_sha256,raw_file_path,
        request_url,http_status FROM captures WHERE source='official_sporttery'
        AND capture_kind='regular' AND raw_file_path IS NOT NULL ORDER BY capture_id""").fetchall()
    out_dir.mkdir(parents=True,exist_ok=True)
    output=out_dir/"official_pool_states.ndjson"
    count=collections.Counter();unique={p:set() for p in POOLS}
    distinct_matches=set();missing=collections.Counter();nonempty=0;empty=0
    with output.open("w",encoding="utf-8") as f:
      for cap_id,received,sha,rel,url,status in rows:
        body=gzip.open(raw/rel,"rb").read()
        if hashlib.sha256(body).hexdigest()!=sha:
            raise ValueError("raw hash mismatch capture="+str(cap_id))
        x=json.loads(body)
        matches=[m for g in (x.get("value",{}).get("matchInfoList") or [])
                   for m in (g.get("subMatchList") or [])]
        if matches:nonempty+=1
        else:empty+=1
        for m in matches:
          mid=str(m.get("matchId"));distinct_matches.add(mid)
          perms={z.get("poolCode"):z for z in (m.get("poolList") or [])}
          for pool in POOLS:
            q=m.get(pool.lower());a=perms.get(pool)
            if not isinstance(q,dict) or not isinstance(a,dict):
                missing[pool]+=1;continue
            odds={k:q.get(k) for k in FIELDS[pool]}
            flags={k:q.get(k+"f") for k in FIELDS[pool]}
            rec={"capture_id":cap_id,"observed_at":received,"raw_sha256":sha,
                 "match_id":mid,"match_num":m.get("matchNumStr"),
                 "kickoff_date":m.get("matchDate"),"kickoff_time":m.get("matchTime"),
                 "pool":pool,"line":q.get("goalLine"),
                 "provider_update_date":q.get("updateDate"),
                 "provider_update_time":q.get("updateTime"),
                 "pool_status":a.get("poolStatus"),"betting_single":a.get("bettingSingle"),
                 "betting_allup":a.get("bettingAllup"),"close_date":a.get("poolCloseDate"),
                 "close_time":a.get("poolCloseTime"),"odds":odds,"odds_flags":flags}
            f.write(json.dumps(rec,ensure_ascii=False,sort_keys=True)+"\n")
            count[pool]+=1
            unique[pool].add((mid,str(q.get("updateDate")),str(q.get("updateTime"))))
    data={"official_regular_captures_with_raw":len(rows),"nonempty_captures":nonempty,
          "empty_captures":empty,"distinct_matches":len(distinct_matches),
          "records_by_pool":dict(count),"missing_pool_objects":dict(missing),
          "distinct_match_provider_clocks":{p:len(v) for p,v in unique.items()},
          "detailed_file":str(output),"detailed_sha256":hashlib.sha256(output.read_bytes()).hexdigest()}
    (out_dir/"summary.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    return data

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--raw",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(reconstruct(a.db,a.raw,a.out_dir),indent=2))
