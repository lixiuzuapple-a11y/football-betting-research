"""TASK-0024 independent monitor with terminal success and free-disk gates."""
import argparse,datetime as dt,json,shutil,sqlite3,subprocess
from contextlib import closing
from pathlib import Path

def check(root,service,max_rounds,now=None):
 now=now or dt.datetime.now(dt.timezone.utc)
 def prop(p):
  return subprocess.run(["systemctl","show",service,"-p",p,"--value"],capture_output=True,text=True,check=False).stdout.strip()
 state=prop("ActiveState"); result=prop("Result")
 item={"at":now.isoformat(),"service":service,"active":state,"unit_result":result,"status":"FAIL"}
 try:
  free=shutil.disk_usage(root).free
  with closing(sqlite3.connect(f"file:{(root/'official.sqlite3')}?mode=ro",uri=True,timeout=5)) as c:
   integrity=c.execute("pragma quick_check").fetchone()[0]
   n=c.execute("select count(*) from captures").fetchone()[0]
   last=c.execute("select observed_at_utc,result,match_count from captures order by capture_id desc limit 1").fetchone()
  item.update({"captures":n,"integrity":integrity,"disk_free_bytes":free})
  if last:
   age=(now-dt.datetime.fromisoformat(last[0])).total_seconds()
   item.update({"lag_seconds":round(age,2),"last_result":last[1],"match_count":last[2]})
  if state=="inactive" and result=="success" and n>=max_rounds and integrity=="ok" and last and last[1]=="ok":
   item["status"]="COMPLETED"
  elif state=="active" and integrity=="ok" and free>=2*1024**3 and last and last[1]=="ok" and last[2]>0 and -30<=age<=180:
   item["status"]="OK"
  else:item["reason"]="unit/age/response/disk/integrity gate"
 except (OSError,ValueError,sqlite3.Error) as e:item["reason"]=type(e).__name__+":"+str(e)[:120]
 return item

if __name__=="__main__":
 p=argparse.ArgumentParser()
 for flag in ("root","service","log"):p.add_argument("--"+flag,required=True)
 p.add_argument("--max-rounds",required=True,type=int)
 a=p.parse_args();r=check(Path(a.root),a.service,a.max_rounds)
 Path(a.log).parent.mkdir(parents=True,exist_ok=True)
 with open(a.log,"a",encoding="utf8") as f:f.write(json.dumps(r,sort_keys=True)+"\n")
 print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r["status"] in ("OK","COMPLETED") else 2)
