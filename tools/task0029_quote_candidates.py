"""Conservative, read-only canonical quote candidate stream from frozen official captures.

This is an observed quote CANDIDATE stream, not executable price evidence.
"""
import argparse, collections, datetime as dt, gzip, hashlib, json, sqlite3
from pathlib import Path
from tools.task0028_timeline_gate import POOLS, price_vector, provider_time, parse_time, valid_vector

def transition(last, row, observed, pool, match):
    """Classify next observation relative to last accepted state.
    Never accept a provider-time rewind or conflicting same-timestamp quote.
    """
    stamp=provider_time(row)
    if not valid_vector(row,pool):return "invalid_odds",None
    if stamp is None or observed is None:return "missing_time",None
    if stamp>observed+dt.timedelta(minutes=2):return "future_provider_time",None
    if str(match.get("matchStatus"))!="Selling" or str(match.get("sellStatus"))!="1":
        return "match_not_selling",None
    pools={str(p.get("poolCode","")).lower():p for p in match.get("poolList",[]) if isinstance(p,dict)}
    entry=pools.get(pool)
    if entry is None or str(entry.get("poolStatus"))!="Selling":return "pool_not_selling",None
    if any(str(v) not in ("0","0.0","false","False","") for k,v in row.items() if k.endswith("f")):
        return "flagged",None
    vec=price_vector(row)
    # Also preserve handicap: price under -1 handicap is distinct from price under 0.
    handicap=str(row.get("goalLine",""))
    candidate=(stamp,vec,handicap)
    if last is None:return "initial",candidate
    prior_time,prior_vec,prior_handicap=last
    if stamp<prior_time:return "provider_rewind",None
    if stamp==prior_time:
        if (vec,handicap)==(prior_vec,prior_handicap):return "duplicate",None
        return "same_timestamp_conflict",None
    if (vec,handicap)==(prior_vec,prior_handicap):return "timestamp_only",candidate
    return "advance_change",candidate

def replay(roots):
    counters={p:collections.Counter() for p in POOLS}
    accepted={}
    fixtures=set()
    checked=0
    for root in roots:
        root=Path(root)
        con=sqlite3.connect("file:"+str((root/"official.sqlite3").resolve()).replace("\\","/")+"?mode=ro",uri=True)
        try:
            for cid,seen,status,sha,rel in con.execute("select capture_id,observed_at_utc,result,raw_sha256,raw_path from captures order by capture_id"):
                if not rel:continue
                raw=gzip.open(root/rel,"rb").read()
                if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("hash mismatch")
                checked+=1
                if status!="ok":continue
                observed=parse_time(seen)
                data=json.loads(raw)
                for group in data["value"]["matchInfoList"]:
                    for match in group["subMatchList"]:
                        mid=str(match["matchId"]);fixtures.add(mid)
                        for pool in POOLS:
                            row=match.get(pool)
                            if not isinstance(row,dict) or not row:continue
                            key=(mid,pool)
                            label,new_state=transition(accepted.get(key),row,observed,pool,match)
                            counters[pool][label]+=1
                            if new_state is not None:accepted[key]=new_state
        finally:con.close()
    return {"fixtures":len(fixtures),"raw_verified":checked,"pool_counts":{p:dict(c) for p,c in counters.items()},
            "accepted_fixture_pool_states":len(accepted),"outcome_join":"NO_VERIFIED_SCORES",
            "warning":"Conservative canonical observed quote candidates, NOT executable orders, no odds availability guarantee."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,action="append",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    results=replay(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(results,ensure_ascii=False))
if __name__=="__main__":main()
