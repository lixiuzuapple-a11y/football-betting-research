"""TASK-0019 descriptive event timing on frozen five-pool states."""
import argparse, collections, datetime as dt, json, statistics
from pathlib import Path
POOLS=("HAD","HHAD","TTG","CRS","HAFU")
def stamp(row):
    try:
        return dt.datetime.strptime(row["provider_update_date"]+" "+row["provider_update_time"],"%Y-%m-%d %H:%M:%S")
    except (TypeError,ValueError): return None
def analyze(file):
    history=collections.defaultdict(list)
    for line in file.open(encoding="utf-8"):
        r=json.loads(line);history[(r["match_id"],r["pool"])].append(r)
    clocks=collections.defaultdict(list)
    totals=collections.Counter()
    perpool=collections.defaultdict(collections.Counter)
    reversal_matches=collections.defaultdict(set)
    for (match,pool), rows in history.items():
        rows.sort(key=lambda x:x["capture_id"])
        prev=None;states=[];laststamp=None
        for r in rows:
            key=(r["line"],tuple(sorted(r["odds"].items())),tuple(sorted(r["odds_flags"].items())))
            if prev==key:continue
            current=stamp(r)
            if prev is not None:
                totals["events"]+=1;perpool[pool]["events"]+=1
                if current is None or laststamp is None: tag="invalid"
                elif current<laststamp: tag="backward"
                elif current==laststamp:tag="unchanged"
                else:tag="forward"
                totals["clock_"+tag]+=1;perpool[pool]["clock_"+tag]+=1
                if current:clocks[(match,pool)].append(current.timestamp())
            states.append(key)
            if len(states)>=3 and states[-1]==states[-3]:
                perpool[pool]["reversions"]+=1;reversal_matches[pool].add(match)
            prev=key;laststamp=current
    pairs={}
    for i,p in enumerate(POOLS):
        for q in POOLS[i+1:]:
            a=b=t=0
            for match in {m for m,pool in clocks}:
                x=clocks.get((match,p),[]);y=clocks.get((match,q),[])
                if len(x)<2 or len(y)<2:continue
                u,v=statistics.median(x),statistics.median(y)
                if u<v:a+=1
                elif u>v:b+=1
                else:t+=1
            pairs[p+"__"+q]={"p_earlier":a,"q_earlier":b,"tied":t,"eligible_fixtures":a+b+t}
    return {"source_rows":sum(map(len,history.values())),"fixture_pool_sequences":len(history),
       "total_events":totals["events"],"all_clocks":dict(totals),
       "by_pool":{p:dict(perpool[p])|{"fixtures_with_reversion":len(reversal_matches[p])} for p in POOLS},
       "pairwise_median_update_order":pairs,
       "caution":"Historical descriptive observed changes only; no causal lead/lag or executable opportunity."}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--detail",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
 a=p.parse_args();result=analyze(a.detail);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
