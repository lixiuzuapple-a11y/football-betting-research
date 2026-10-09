"""TASK-0013 read-only source/odds-field availability census."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import argparse

def analyze(path):
    totals=Counter()
    availability=defaultdict(Counter)
    fields=("PSH","PSD","PSA","PSCH","PSCD","PSCA")
    with path.open(newline="",encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            source=row.get("src","").strip()
            totals[source]+=1
            for group,triplet in (("opening",fields[:3]),("closing",fields[3:])):
                if all(row.get(k,"").strip() for k in triplet):
                    availability[source][group]+=1
    return {"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "total":sum(totals.values()),"by_source":{
            k:{"rows":v,"opening_complete":availability[k]["opening"],
               "closing_complete":availability[k]["closing"]} for k,v in sorted(totals.items())}}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    out=analyze(a.input)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))
