"""One-shot official result provenance & strict fixture-ID reconciliation.
Saves raw official responses outside Git; never invents scores or settlement.
"""
import argparse,collections,datetime as dt,gzip,hashlib,json,sqlite3,time,urllib.parse,urllib.request
from pathlib import Path
BASE="https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry"
def source_index(roots):
    ids={}
    counts=collections.Counter()
    for root in map(Path,roots):
        c=sqlite3.connect("file:"+str((root/"official.sqlite3").resolve()).replace("\\","/")+"?mode=ro",uri=True)
        if c.execute("pragma integrity_check").fetchone()[0]!="ok":raise ValueError("broken SQLite")
        for cid,observed,status,sha,path in c.execute("select capture_id,observed_at_utc,result,raw_sha256,raw_path from captures order by capture_id"):
            if status!="ok":continue
            raw=gzip.open(root/path,"rb").read()
            if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("bad SHA")
            counts["checked"]+=1
            for grp in json.loads(raw)["value"]["matchInfoList"]:
                for match in grp["subMatchList"]:
                    mid=str(match["matchId"])
                    key={field:str(match.get(field,"")) for field in ("matchId","businessDate","matchDate","homeTeamId","awayTeamId","homeTeamAllName","awayTeamAllName")}
                    if mid in ids and any(ids[mid][k]!=key[k] for k in ("homeTeamId","awayTeamId","businessDate")):raise ValueError("identity changed "+mid)
                    ids[mid]=key
        c.close()
    return ids,counts
def get(date,page):
    query=urllib.parse.urlencode({"matchBeginDate":date,"matchEndDate":date,"leagueId":"","pageSize":100,"pageNo":page,"isFix":0,"matchPage":1,"pcOrWap":1})
    url=BASE+"?"+query
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.sporttery.cn/jc/zqsgkj/"})
    with urllib.request.urlopen(req,timeout=25) as resp:return url,resp.read(),resp.status
def score(text):
    text=str(text or "")
    if not text or ":" not in text:return None
    l,r=text.split(":",1)
    if not l.isdecimal() or not r.isdecimal():return None
    return [int(l),int(r)]
def reconcile(index,rows):
    found={};conflict=[];ambiguous=[];verified=[]
    for row in rows:
        mid=str(row.get("matchId",""))
        if mid not in index:continue
        meta=index[mid]
        if mid in found:
            if (row.get("sectionsNo999"),row.get("homeTeamId"),row.get("awayTeamId"))!=(found[mid].get("sectionsNo999"),found[mid].get("homeTeamId"),found[mid].get("awayTeamId")):
                conflict.append(mid)
            continue
        found[mid]=row
        if (str(row.get("homeTeamId",""))!=meta["homeTeamId"] or str(row.get("awayTeamId",""))!=meta["awayTeamId"] or str(row.get("matchDate",""))!=meta["matchDate"][:10]):
            conflict.append(mid);continue
        full=score(row.get("sectionsNo999"))
        if full is None:
            ambiguous.append(mid);continue
        if str(row.get("matchResultStatus","")) not in ("2",):
            ambiguous.append(mid);continue
        verified.append({"matchId":mid,"score":full,"homeTeamId":meta["homeTeamId"],"awayTeamId":meta["awayTeamId"],"matchDate":row.get("matchDate"),"sectionsNo999":row.get("sectionsNo999"),"matchResultStatus":row.get("matchResultStatus"),"source":"sporttery_official_result_api"})
    return {"found_ids":len(found),"identity_conflicts":sorted(set(conflict)),"no_verified_score_or_status":sorted(set(ambiguous)),"verified_scores":[v for v in verified if v["matchId"] not in conflict],"unmatched":sorted(index.keys()-found.keys())}
def main():
    a=argparse.ArgumentParser();a.add_argument("--root",action="append",required=True);a.add_argument("--out",required=True,type=Path);v=a.parse_args()
    index,c=source_index(v.root)
    v.out.mkdir(parents=True,exist_ok=True)
    dates=sorted({m["matchDate"][:10] for m in index.values() if len(m["matchDate"])>=10})
    fetched=[];rows=[];errors=[]
    for day in dates:
        for page in range(1,16):
            try:u,b,status=get(day,page);o=json.loads(b)
            except Exception as e:
                errors.append({"day":day,"page":page,"error":str(e)});break
            if str(o.get("errorCode"))!="0":
                errors.append({"day":day,"page":page,"errorCode":o.get("errorCode")});break
            val=o.get("value") or {};part=val.get("matchResult") or []
            p=v.out/("official-"+day+"-p"+str(page)+".json")
            p.write_bytes(b)
            fetched.append({"date":day,"page":page,"http":status,"sha256":hashlib.sha256(b).hexdigest(),"relative_path":p.name,"rows":len(part),"total":val.get("total")})
            rows.extend(part)
            if not part or len(part)>=int(val.get("total",len(part))) or page*100>=int(val.get("total",0)):break
    joined=reconcile(index,rows)
    summary={"fixture_count":len(index),"source_payloads":c["checked"],"dates":dates,"raw_api_responses":fetched,"request_errors":errors,"official_total_rows":len(rows),"found_ids":joined["found_ids"],"identity_conflicts":joined["identity_conflicts"],"no_verified_score_or_status":joined["no_verified_score_or_status"],"verified_score_count":len(joined["verified_scores"]),"unmatched_count":len(joined["unmatched"]),"unmatched":joined["unmatched"],"note":"Official score matched by ID and team identity. Need independent QA before downstream model label acceptance."}
    (v.out/"JOIN_EVIDENCE.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    (v.out/"VERIFIED_SCORE_CANDIDATES.json").write_text(json.dumps(joined["verified_scores"],ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ("fixture_count","source_payloads","dates","raw_api_responses","request_errors","official_total_rows","found_ids","identity_conflicts","verified_score_count","unmatched_count")},ensure_ascii=False,default=lambda x:len(x) if isinstance(x,list) else str(x)))
if __name__=="__main__":main()
