"""Extract original Chinese team labels with verified SHA, from original frozen captures.

Only required for independently human-reviewed cup match identity aliases.
Raw captures remain read-only and off GitHub.
"""
import argparse,gzip,hashlib,json,sqlite3
from pathlib import Path

def collect(roots,ids):
    found={}
    for root in roots:
        db=sqlite3.connect("file:"+str((root/"official.sqlite3").resolve()).replace("\\","/")+"?mode=ro",uri=True)
        for (path,sha) in db.execute("select raw_path, raw_sha256 from captures where result='ok'"):
            if len(found)==len(ids):break
            raw=gzip.open(root/path,"rb").read()
            if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("Original frozen raw hash changed "+path)
            for group in json.loads(raw).get("value",{}).get("matchInfoList",[]):
                for m in group.get("subMatchList",[]):
                    mid=str(m.get("matchId",""))
                    if mid in ids and mid not in found:
                        found[mid]={"official_h_zh":m["homeTeamAllName"],"official_a_zh":m["awayTeamAllName"],
                                    "official_hid":str(m["homeTeamId"]),"official_aid":str(m["awayTeamId"]),
                                    "official_hcode":m["homeTeamAbbEnName"],"official_acode":m["awayTeamAbbEnName"],
                                    "raw_sha256":sha,"raw_path":path,"snapshot":root.name}
        db.close()
        if len(found)==len(ids):break
    if len(found)!=len(ids):raise ValueError(f"Only found {len(found)}/{len(ids)} official teams")
    return found

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",action="append",type=Path,required=True)
    ap.add_argument("--cup-inventory",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    opt=ap.parse_args()
    ids={str(m["mid"]) for m in json.loads(opt.cup_inventory.read_text(encoding="utf-8"))}
    d=collect(opt.root,ids)
    opt.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("OFFICIAL_SHA_CHECKED_TEAM_LABELS",len(d))
if __name__=="__main__":main()
