"""TASK-0020 source payload replay and fixture/pool quote reversion audit."""
import argparse,collections,datetime as dt,json,sqlite3
from pathlib import Path

def run(db,detail):
 con=sqlite3.connect("file:"+db.resolve().as_posix()+"?mode=ro&immutable=1",uri=True)
 captures=con.execute("""SELECT capture_id,raw_sha256 FROM captures
 WHERE source='official_sporttery' AND capture_kind='regular' ORDER BY capture_id""").fetchall()
 hashes={cid:sha for cid,sha in captures}
 first={};seen={};replays=0;new=0;previous=None;consecutive=0
 for cid,sha in captures:
  if sha in seen:
   replays+=1
   if previous!=sha:nonconsecutive=1
   else:nonconsecutive=0
   new+=nonconsecutive
  else:seen[sha]=cid
  if previous==sha:consecutive+=1
  previous=sha
 counts=collections.Counter();last={};state_history=collections.defaultdict(list)
 replay_reversal=0;reversions=0;reverse_events=collections.Counter()
 for line in detail.open(encoding="utf-8"):
  d=json.loads(line);k=(d["match_id"],d["pool"])
  state=json.dumps([d["line"],d["odds"],d["odds_flags"]],sort_keys=True)
  if k in last and last[k]==state:continue
  if k in last:
   counts["price_transitions"]+=1
   if hashes.get(d["capture_id"]) in seen and seen[hashes[d["capture_id"]]]<d["capture_id"]:
    counts["change_with_prior_payload_hash"]+=1
  hist=state_history[k]
  if len(hist)>=2 and hist[-2]==state:
   reversions+=1;reverse_events[d["pool"]]+=1
   if hashes.get(d["capture_id"]) in seen and seen[hashes[d["capture_id"]]]<d["capture_id"]:
    replay_reversal+=1
  hist.append(state);last[k]=state
 return {"regular_captures":len(captures),"unique_payload_hashes":len(seen),
         "repeat_payload_captures":replays,"consecutive_identical_payloads":consecutive,
         "nonconsecutive_prior_hash_returns":new,
         "quote_changes":counts["price_transitions"],"reversions":reversions,
         "reversions_coincident_with_prior_full_payload_hash":replay_reversal,
         "change_with_prior_full_payload_hash":counts["change_with_prior_payload_hash"],
         "reversion_by_pool":dict(reverse_events)}

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--db",type=Path,required=True);p.add_argument("--detail",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
 a=p.parse_args();result=run(a.db,a.detail);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
