"""TASK0034 post-hoc timing robustness: require actual pre-kickoff observed >=60m lead.
Never refit independent model; only restrict selected observed HAD quotes.
"""
import argparse,collections,datetime as dt,gzip,hashlib,json,sqlite3
from pathlib import Path
from tools.task0031_actual_scoring import quote
from tools.audit_category_b_original_dc import metric
from tools.task0034_original_dc_vs_sporttery import paired_cluster_ci

def rescore(roots,earlier_results,cutoff=60):
    fixed={r["matchId"]:r for r in earlier_results["rows"]}
    best={}
    for root in roots:
        root=Path(root)
        db=sqlite3.connect("file:"+str((root/"official.sqlite3").resolve()).replace("\\","/")+"?mode=ro",uri=True)
        for cid,at,status,sha,path in db.execute("select capture_id,observed_at_utc,result,raw_sha256,raw_path from captures order by capture_id"):
            if status!="ok":continue
            raw=gzip.open(root/path,"rb").read()
            if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("frozen data mismatch")
            for group in json.loads(raw)["value"]["matchInfoList"]:
                for m in group["subMatchList"]:
                    mid=str(m["matchId"])
                    if mid not in fixed:continue
                    candidate=quote(m,at,"strict")
                    if candidate is None:continue
                    delta=(candidate["kickoff"]-candidate["observed"]).total_seconds()/60
                    if delta<cutoff:continue
                    old=best.get(mid)
                    if old is None or (candidate["observed"],candidate["provider"])>(old["observed"],old["provider"]):
                        best[mid]=candidate
        db.close()
    rows=[]
    for mid,p in best.items():
        old=fixed[mid]
        rows.append({**old,"market":p["p"],"observed_lead_min":(p["kickoff"]-p["observed"]).total_seconds()/60})
    return {"primary_34":len(fixed),"cutoff_min":cutoff,"filtered_n":len(rows),
            "excluded_without_quote_as_of_cutoff":sorted(fixed.keys()-best.keys()),
            "independent_metrics":metric(rows,"independent") if rows else None,
            "market_metrics":metric(rows,"market") if rows else None,
            "paired_delta_logloss":(metric(rows,"independent")["log_loss"]-metric(rows,"market")["log_loss"]) if rows else None,
            "day_cluster_ci":paired_cluster_ci(rows) if rows else None,
            "rows":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",action="append",type=Path,required=True)
    p.add_argument("--primary",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--cutoff",type=int,default=60)
    a=p.parse_args()
    x=rescore(a.root,json.loads(a.primary.read_text(encoding="utf-8")),a.cutoff)
    a.out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in x.items() if k not in ("rows","excluded_without_quote_as_of_cutoff")},ensure_ascii=False))
if __name__=="__main__":main()
