"""Independent TASK-0018 raw mapping verifier; does not import TASK-0015.

Reads only historical frozen regular raw captures and TASK-0015 bulk NDJSON.
"""
import argparse,collections,gzip,hashlib,json,sqlite3
from pathlib import Path

POOLS=("HAD","HHAD","TTG","CRS","HAFU")
def run(db,raw,detail):
    c=sqlite3.connect("file:"+str(db)+"?mode=ro&immutable=1",uri=True)
    rows=c.execute("select capture_id,raw_file_path,raw_sha256 from captures where source='official_sporttery' and capture_kind='regular' order by capture_id").fetchall()
    expected={}
    all_clocks=collections.defaultdict(set)
    for cap,rel,digest in rows:
        payload=gzip.open(raw/rel,"rb").read()
        if hashlib.sha256(payload).hexdigest()!=digest:raise ValueError("Raw digest mismatch")
        item=json.loads(payload)
        for day in (item.get("value",{}).get("matchInfoList") or []):
            for match in (day.get("subMatchList") or []):
                mid=str(match["matchId"])
                statuses={p["poolCode"]:p for p in (match.get("poolList") or [])}
                for pool in POOLS:
                    quote=match.get(pool.lower());status=statuses.get(pool)
                    if not isinstance(quote,dict) or not isinstance(status,dict):
                        raise ValueError("Missing raw pool")
                    key=(cap,mid,pool)
                    if key in expected:raise ValueError("Duplicate raw pool")
                    expected[key]=(quote,status)
    seen=set();mismatches=collections.Counter();counts=collections.Counter()
    price_changes=collections.Counter();clock_only=collections.Counter()
    last_price={};last_clock={};fixture_sets=collections.defaultdict(set)
    for line in detail.open(encoding="utf-8"):
        row=json.loads(line);key=(row["capture_id"],row["match_id"],row["pool"])
        if key in seen:raise ValueError("Duplicate extracted key")
        seen.add(key);counts[row["pool"]]+=1
        if key not in expected:
            mismatches["missing_from_raw"]+=1;continue
        quote,status=expected[key];pool=row["pool"]
        for name,old in row["odds"].items():
            if old!=quote.get(name):mismatches["odds"]+=1
            if row["odds_flags"][name]!=quote.get(name+"f"):mismatches["odds_flags"]+=1
        for k,target in (("goalLine","line"),("updateDate","provider_update_date"),("updateTime","provider_update_time")):
            if quote.get(k)!=row[target]:mismatches[target]+=1
        for k,target in (("poolStatus","pool_status"),("bettingSingle","betting_single"),
                         ("bettingAllup","betting_allup"),("poolCloseDate","close_date"),("poolCloseTime","close_time")):
            if status.get(k)!=row[target]:mismatches[target]+=1
        pair=(row["match_id"],pool);fixture_sets[pool].add(row["match_id"])
        clock=(row["provider_update_date"],row["provider_update_time"])
        all_clocks[pool].add((row["match_id"],clock))
        # Data are ordered by capture id. Differences from prior capture, not independent events.
        signature=(row["line"],tuple(sorted(row["odds"].items())),tuple(sorted(row["odds_flags"].items())))
        if pair in last_price:
            if signature!=last_price[pair]:price_changes[pool]+=1
            elif clock!=last_clock[pair]:clock_only[pool]+=1
        last_price[pair]=signature;last_clock[pair]=clock
    result={"raw_capture_rows":len(rows),"raw_keys":len(expected),"verified_keys":len(seen),
            "missing_extracted_keys":len(set(expected)-seen),"field_mismatches":dict(mismatches),
            "pool_rows":dict(counts),"fixtures_per_pool":{p:len(fixture_sets[p]) for p in POOLS},
            "distinct_provider_clock_match_pairs":{p:len(all_clocks[p]) for p in POOLS},
            "price_or_flag_transitions_across_observed_states":dict(price_changes),
            "clock_only_transitions":dict(clock_only)}
    result["pass"]=len(expected)==len(seen) and result["missing_extracted_keys"]==0 and not mismatches
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--db",type=Path,required=True)
    p.add_argument("--raw",type=Path,required=True);p.add_argument("--detail",type=Path,required=True)
    a=p.parse_args();v=run(a.db,a.raw,a.detail);print(json.dumps(v,indent=2))
    raise SystemExit(0 if v["pass"] else 1)
