"""Read-only, explicitly pre-kickoff 1X2 market baseline diagnostic on frozen official captures."""
import argparse,collections,datetime as dt,gzip,hashlib,json,math,sqlite3,statistics
from pathlib import Path
TZ=dt.timezone(dt.timedelta(hours=8))
def parse(s):
 try:
  d=dt.datetime.fromisoformat(str(s).replace("Z","+00:00"))
  return d if d.tzinfo else d.replace(tzinfo=TZ)
 except (ValueError,TypeError):return None
def quote(match,arrival,policy):
 had=match.get("had")
 if not isinstance(had,dict):return None
 try:
  odds=[float(had[k]) for k in ("h","d","a")]
 except (ValueError,KeyError,TypeError):return None
 if not all(math.isfinite(x) and x>1 for x in odds):return None
 kickoff=parse(str(match.get("matchDate",""))+"T"+str(match.get("matchTime","")))
 observed=parse(arrival)
 provider=parse(str(had.get("updateDate",""))+"T"+str(had.get("updateTime","")))
 if not kickoff or not observed or not provider:return None
 if observed>=kickoff or provider>observed+dt.timedelta(minutes=2):return None
 if policy=="strict":
  if str(match.get("matchStatus"))!="Selling" or str(match.get("sellStatus"))!="1":return None
  pool=next((p for p in match.get("poolList",[]) if str(p.get("poolCode","")).upper()=="HAD"),None)
  if not pool or str(pool.get("poolStatus"))!="Selling":return None
  if any(str(had.get(k,"0"))!="0" for k in ("hf","df","af")):return None
 inv=[1/o for o in odds];total=sum(inv)
 return {"p":[x/total for x in inv],"observed":observed,"provider":provider,"kickoff":kickoff,"odds":odds}
def metric(rows):
 if not rows:return None
 n=len(rows);correct=0;ll=0;brier=0;ll_u=0;brier_u=0
 sums=[0,0,0];out=[0,0,0]
 for r in rows:
  p=r["p"];y=r["y"];sums=[sums[i]+p[i] for i in range(3)];out[y]+=1
  correct+=int(max(range(3),key=lambda i:p[i])==y)
  ll-=math.log(max(p[y],1e-15));brier+=sum((p[i]-int(i==y))**2 for i in range(3))
  ll_u+=math.log(3);brier_u+=2/3
 return {"n":n,"accuracy":correct/n,"logloss":ll/n,"brier_sum":brier/n,"uniform_logloss":ll_u/n,"uniform_brier_sum":brier_u/n,"predicted_mean":[v/n for v in sums],"actual_frequency":[v/n for v in out]}
def run(roots,labels):
 labels={str(x["matchId"]):x for x in labels}
 best={policy:{} for policy in ("strict","numeric")}
 seen=set();examined=0
 for root in roots:
  root=Path(root);db=sqlite3.connect("file:"+str((root/"official.sqlite3").resolve()).replace("\\","/")+"?mode=ro",uri=True)
  for cid,at,status,sha,path in db.execute("select capture_id,observed_at_utc,result,raw_sha256,raw_path from captures order by capture_id"):
   if status!="ok":continue
   raw=gzip.open(root/path,"rb").read()
   if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("hash mismatch")
   for group in json.loads(raw)["value"]["matchInfoList"]:
    for m in group["subMatchList"]:
     mid=str(m["matchId"])
     if mid not in labels:continue
     seen.add(mid);examined+=1
     for policy in best:
      q=quote(m,at,policy)
      if q is None:continue
      old=best[policy].get(mid)
      if old is None or (q["observed"],q["provider"])>(old["observed"],old["provider"]):
       best[policy][mid]=q
  db.close()
 evaluations={}
 for policy,selected in best.items():
  rows=[];perdate=collections.defaultdict(list);lag=[]
  for mid,q in selected.items():
   score=labels[mid]["score"];y=0 if score[0]>score[1] else 2 if score[0]<score[1] else 1
   item={"mid":mid,"p":q["p"],"y":y,"date":q["kickoff"].date().isoformat()}
   rows.append(item);perdate[item["date"]].append(item);lag.append((q["kickoff"]-q["observed"]).total_seconds()/60)
  evaluations[policy]={"scores":metric(rows),"coverage":len(rows)/len(labels),"per_kickoff_day":{date:metric(entries) for date,entries in sorted(perdate.items())},"lag_minutes_min_median_max":[min(lag),statistics.median(lag),max(lag)] if lag else [],"excluded_match_ids":sorted(labels.keys()-selected.keys()),"rows_for_bootstrap":[{"matchId":r["mid"],"p":r["p"],"y":r["y"],"date":r["date"]} for r in rows]}
 return {"label_total":len(labels),"label_match_ids_seen":len(seen),"labelled_observations":examined,"policies":evaluations,"warnings":["Retrospective descriptive scoring only; selection depends on recorded arrival and provider time, not actual accepted betting orders.","Uniform baseline is no-information; sample actual frequency is hindsight and not used as prediction.","Potential UTC+08 kickoff time assumption must be checked against published specification."]}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,action="append",required=True);p.add_argument("--labels",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();r=run(a.root,json.loads(a.labels.read_text(encoding="utf-8")));a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="policies"}|{"policies":{k:{n:val for n,val in v.items() if n not in ("rows_for_bootstrap","excluded_match_ids","per_kickoff_day")} for k,v in r["policies"].items()}},ensure_ascii=False))
if __name__=="__main__":main()
