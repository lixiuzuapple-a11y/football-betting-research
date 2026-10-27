"""TASK0041 read-only capture ledger provenance/status audit.

Checks every SQLite capture SHA against exact gzip raw bytes; classifies with
the *current* reviewed original Sporttery parser without changing old stored
rows, identifying historical 'empty' records that were actually no_offer.
No internet; read-only database; no odds copied to output.
"""
import argparse,collections,datetime as dt,gzip,hashlib,importlib.util,json,sqlite3
from pathlib import Path

def load_capture_module(script):
    spec=importlib.util.spec_from_file_location("evlab_audited_official_capture",script)
    if spec is None or spec.loader is None:raise RuntimeError("cannot load parser")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def audit(root:Path,script:Path):
    classifier=load_capture_module(script)
    conn=sqlite3.connect("file:"+root.joinpath("official.sqlite3").resolve().as_posix()+"?mode=ro",uri=True)
    try:
        if conn.execute("PRAGMA quick_check").fetchone()[0]!="ok":
            raise ValueError("SQLite corruption")
        rows=conn.execute("""SELECT capture_id,observed_at_utc,http_status,result,match_count,raw_sha256,raw_path,raw_length,error,source_commit
                             FROM captures ORDER BY capture_id""").fetchall()
    finally:conn.close()
    if not rows:raise ValueError("no records")
    before=collections.Counter()
    after=collections.Counter()
    http=collections.Counter()
    stamps=[]
    paths={}
    remapped=0
    for cid,at,status,res,n,sha,path,nbytes,error,commit in rows:
        before[res]+=1
        http[str(status)]+=1
        if cid<1 or not commit:raise ValueError("invalid collector metadata")
        t=dt.datetime.fromisoformat(at)
        if not t.tzinfo:raise ValueError("observation lacks tz")
        stamps.append(t)
        if not path or not sha or not nbytes:
            if status==200:raise ValueError("HTTP200 missing source bytes")
            after[res]+=1
            continue
        f=(root/path).resolve()
        if not f.is_relative_to(root.resolve()):raise ValueError("raw path escaped root")
        if f in paths:
            raw=paths[f]
        else:
            raw=gzip.open(f,"rb").read()
            paths[f]=raw
        if hashlib.sha256(raw).hexdigest()!=sha or len(raw)!=nbytes:
            raise ValueError(f"capture {cid} source hash/bytes mismatch")
        if status==200:
            classification,number,_=classifier.classify(raw)
            if number!=n and res not in ("empty","no_offer"):raise ValueError(f"fixture count mismatch {cid}")
            if res=="empty" and classification=="no_offer":remapped+=1
            elif res!=classification:
                raise ValueError(f"mismatched result {cid}: stored={res} current={classification}")
            after[classification]+=1
        else:
            after[res]+=1
    if any(b<a for a,b in zip(stamps,stamps[1:])):
        raise ValueError("observation time moves backward")
    roots=sorted(set(r[-1] for r in rows))
    return {"captures":len(rows),"sqlite_quick_check":"ok",
            "verified_sha_captures":sum(bool(r[5]) for r in rows),
            "raw_distinct_files_hashed":len(paths),"observed_first_utc":stamps[0].isoformat(),
            "observed_last_utc":stamps[-1].isoformat(),
            "original_result_counts":dict(before),"reclassified_by_fixed_parser":dict(after),
            "historical_empty_to_normal_no_offer":remapped,
            "http_status_counts":dict(http),
            "collector_source_commits":roots,
            "last_10_old_results":[r[3] for r in rows[-10:]],
            "evidence":"read-only SQLite rows, every gzip source byte/hash and current code classifier",
            "scope":"Does not claim continuous full-run or new prospects before kickoff."}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",required=True,type=Path)
    a.add_argument("--parser",required=True,type=Path)
    a.add_argument("--out",type=Path)
    v=a.parse_args()
    result=audit(v.root,v.parser)
    if v.out:
        v.out.parent.mkdir(exist_ok=True,parents=True)
        v.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
