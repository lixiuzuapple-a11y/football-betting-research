"""TASK-0021 independent collector health monitor; one-shot, invoked by systemd timer."""
import argparse,datetime as dt,json,sqlite3,subprocess
from pathlib import Path

def health(root:Path,service:str,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    state=subprocess.run(["systemctl","is-active",service],capture_output=True,text=True,check=False).stdout.strip()
    row={"at":now.isoformat(),"service":service,"active":state,"status":"FAIL"}
    try:
        db=root/"official.sqlite3"
        with sqlite3.connect(f"file:{db}?mode=ro",uri=True,timeout=5) as con:
            integrity=con.execute("PRAGMA quick_check").fetchone()[0]
            x=con.execute("select capture_id,observed_at_utc,result,match_count from captures order by capture_id desc limit 1").fetchone()
        row["integrity"]=integrity
        if x:
            row.update({"capture_id":x[0],"observed_at_utc":x[1],"last_result":x[2],"match_count":x[3]})
            lag=(now-dt.datetime.fromisoformat(x[1])).total_seconds()
            row["lag_seconds"]=round(lag,2)
        if state=="active" and integrity=="ok" and x and x[2]=="ok" and x[3]>0 and -30<=lag<=180:
            row["status"]="OK"
        else:
            row["reason"]="inactive/stale/bad-capture/integrity"
    except (OSError,ValueError,sqlite3.Error) as exc:
        row["reason"]=type(exc).__name__+":"+str(exc)[:160]
    return row

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
    p.add_argument("--service",required=True);p.add_argument("--log",type=Path,required=True)
    a=p.parse_args();r=health(a.root,a.service);a.log.parent.mkdir(parents=True,exist_ok=True)
    with a.log.open("a",encoding="utf-8") as out:out.write(json.dumps(r,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r["status"]=="OK" else 2)
