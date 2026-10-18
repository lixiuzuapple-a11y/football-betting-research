"""Empirical frozen official capture timeline audit. Never interpret observed odds as executable."""
import argparse,collections,datetime as dt,gzip,hashlib,json,sqlite3
from pathlib import Path

POOLS=("had","hhad","ttg","crs","hafu")
EXCLUDE={"updateDate","updateTime","goalLineValue"}
def parse_time(value):
    if not value:return None
    try:return dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    except (ValueError,TypeError):return None
def provider_time(row):
    a,b=row.get("updateDate"),row.get("updateTime")
    if not a or not b:return None
    return parse_time(str(a)+"T"+str(b)+"+08:00")
def price_vector(row):
    # Immutable hashable selection: genuine prices, not status/flags, timestamps, or handicaps.
    return tuple(sorted((k,str(v)) for k,v in row.items() if k not in EXCLUDE and not k.endswith("f") and k not in ("goalLine","id") and isinstance(v,(int,float,str)) and str(v).strip()!=""))
def valid_vector(row,pool):
    odds=price_vector(row)
    expected={"had":("h","d","a"),"hhad":("h","d","a"),"ttg":tuple("s"+str(i) for i in range(8)),"hafu":("hh","hd","ha","dh","dd","da","ah","ad","aa")}
    keys={k for k,v in odds}
    required=expected.get(pool)
    if required and not set(required)<=keys:return False
    try:return all(float(v)>1 for k,v in odds)
    except ValueError:return False
def evaluate(roots):
    fixtures=set()
    stats={p:collections.Counter() for p in POOLS}
    last={}
    identity={}
    result=collections.Counter()
    obs=collections.Counter()
    verified_payloads=0
    for root in roots:
        root=Path(root)
        conn=sqlite3.connect("file:"+str((root/"official.sqlite3").resolve()).replace("\\","/")+"?mode=ro",uri=True)
        if conn.execute("pragma integrity_check").fetchone()[0]!="ok":raise RuntimeError("corrupt database")
        for cid,observed_at,status,sha,path in conn.execute("select capture_id,observed_at_utc,result,raw_sha256,raw_path from captures order by capture_id"):
            result[status]+=1
            if not path:continue
            raw=gzip.open(root/path,"rb").read()
            if hashlib.sha256(raw).hexdigest()!=sha:raise RuntimeError("SHA mismatch "+str(cid))
            verified_payloads+=1
            if status!="ok":continue
            observed=parse_time(observed_at)
            payload=json.loads(raw)
            for group in payload["value"]["matchInfoList"]:
                for m in group["subMatchList"]:
                    mid=str(m["matchId"]);fixtures.add(mid);obs[mid]+=1
                    identity_key=tuple(str(m.get(x)) for x in ("homeTeamId","awayTeamId","businessDate"))
                    if mid in identity and identity[mid]!=identity_key:raise RuntimeError("fixture identity changed "+mid)
                    identity[mid]=identity_key
                    for pool in POOLS:
                        row=m.get(pool)
                        if not isinstance(row,dict) or not row:continue
                        st=stats[pool];st["observations"]+=1
                        vec=price_vector(row);stamp=provider_time(row)
                        if not valid_vector(row,pool):st["invalid_odds"]+=1
                        else:st["valid_odds"]+=1
                        if stamp is None:st["missing_provider_time"]+=1
                        elif observed:
                            delay=(observed-stamp).total_seconds()
                            if delay < -120:st["future_provider_time"]+=1
                            if delay > 3600:st["older_than_1h"]+=1
                            if delay > 21600:st["older_than_6h"]+=1
                        flags=tuple(sorted((k,str(v)) for k,v in row.items() if k.endswith("f")))
                        if any(v not in ("0","0.0","False","false","") for k,v in flags):st["nonzero_flags"]+=1
                        key=mid,pool
                        prev=last.get(key)
                        if prev:
                            old_vec,old_stamp,old_flags=prev
                            if vec!=old_vec:
                                st["price_transitions"]+=1
                                if stamp==old_stamp:st["price_changed_same_timestamp"]+=1
                                elif stamp and old_stamp and stamp<old_stamp:st["price_changed_timestamp_rewind"]+=1
                                elif stamp and old_stamp and stamp>old_stamp:st["price_changed_timestamp_advance"]+=1
                            if stamp and old_stamp and stamp<old_stamp:st["timestamp_rewinds"]+=1
                            if flags!=old_flags:st["flag_transitions"]+=1
                            if vec==old_vec and flags==old_flags and stamp==old_stamp:st["identical_consecutive"]+=1
                        last[key]=(vec,stamp,flags)
        conn.close()
    return {"roots":[str(p) for p in roots],"verified_payloads":verified_payloads,"captures":dict(result),"fixtures":len(fixtures),"fixture_observations":sum(obs.values()),"pools":{k:dict(v) for k,v in stats.items()},"outcomes_verified":0,"scope":"Observed snapshots only. No executable odds or outcome assertions."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",action="append",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    data=evaluate(a.root);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(data,ensure_ascii=False))
if __name__=="__main__":main()
