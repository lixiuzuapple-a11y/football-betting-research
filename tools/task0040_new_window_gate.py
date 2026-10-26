"""TASK0040: immutable-raw new-period quote gate (research only).

Only original pre-kickoff source bytes are input to quote parsing.
Uses existing TASK0031 strict official HAD criteria (flags, statuses and time).
Do NOT import future scores, historical label files, or rerun prior cohorts.
A local UTC receive timestamp is not independently attested; publish hashed
manifest in git before kickoff as an additional tamper-evidence milestone.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,math
from collections import Counter
from pathlib import Path
from tools.task0031_actual_scoring import quote,parse

UTC=dt.timezone.utc

def _parse_utc(text):
    date=parse(text)
    if date is None or date.utcoffset()!=dt.timedelta(0):
        raise ValueError("capture metadata timestamps must explicitly be UTC")
    return date

def validate_source(manifest_path:Path, *, require_now_before_kickoff=False):
    manifest_path=Path(manifest_path)
    man=json.loads(manifest_path.read_text(encoding="utf-8"))
    if man.get("http_status")!=200:raise ValueError("not HTTP 200")
    start=_parse_utc(man["request_started_at_utc"])
    end=_parse_utc(man["response_received_at_utc"])
    if not start<=end or (end-start)>dt.timedelta(seconds=60):
        raise ValueError("invalid request/response time interval")
    name=man["raw_filename"]
    if Path(name).name!=name or not name.startswith("sporttery-") or not name.endswith(".json"):
        raise ValueError("raw file path traversal/noncanonical name")
    raw=(manifest_path.parent/name).read_bytes()
    if len(raw)!=man["raw_bytes"]:raise ValueError("raw byte count differs")
    if hashlib.sha256(raw).hexdigest()!=man["sha256"]:
        raise ValueError("raw source sha mismatch")
    doc=json.loads(raw)
    if doc.get("success") is not True or doc.get("errorCode") not in (0,"0",None):
        raise ValueError("provider returned invalid response")
    groups=doc["value"]["matchInfoList"]
    matches=[m for g in groups for m in g["subMatchList"]]
    if len(matches)!=man["fixture_count"] or len(groups)!=man["group_count"]:
        raise ValueError("original fixture/group count differs from manifest")
    if len(set(str(m["matchId"]) for m in matches))!=len(matches):
        raise ValueError("duplicate match ID in original source")
    if require_now_before_kickoff and end>dt.datetime.now(UTC):
        raise ValueError("future fabricated capture timestamp")
    return man,matches,start,end

def classify_one(match,start,end):
    kickoff=parse(str(match.get("matchDate",""))+"T"+str(match.get("matchTime","")))
    if kickoff is None:raise ValueError("kickoff missing or malformed")
    numeric=quote(match,end.isoformat(),"numeric")
    strict=quote(match,end.isoformat(),"strict")
    reasons=[]
    if end>=kickoff:reasons.append("at_or_after_kickoff")
    had=match.get("had")
    if not isinstance(had,dict):reasons.append("missing_had")
    elif strict is None:
        try:
            odds=[float(had[x]) for x in ("h","d","a")]
            if not all(math.isfinite(x) and x>1 for x in odds):reasons.append("invalid_HAD_prices")
        except (KeyError,ValueError,TypeError):reasons.append("invalid_HAD_prices")
        if any(str(had.get(x,"0"))!="0" for x in ("hf","df","af")):
            reasons.append("nonzero_HAD_flags")
        if str(match.get("matchStatus"))!="Selling" or str(match.get("sellStatus"))!="1":
            reasons.append("match_not_selling")
        pools=[p for p in match.get("poolList",[]) if p.get("poolCode")=="HAD"]
        if not pools or pools[0].get("poolStatus")!="Selling":
            reasons.append("HAD_pool_not_selling")
        if not reasons:reasons.append("timestamps_or_unclassified")
    if strict and (strict["observed"]!=end or strict["provider"]>end+dt.timedelta(minutes=2)):
        raise ValueError("strict timestamp inconsistencies")
    # No result, predicted Y, or bookmaker ROI should occur in this record.
    r={"matchId":str(match["matchId"]),
       "league":match.get("leagueAbbName"),"home_code":match.get("homeTeamAbbEnName"),
       "away_code":match.get("awayTeamAbbEnName"),
       "official_home_team_id":str(match.get("homeTeamId")),
       "official_away_team_id":str(match.get("awayTeamId")),
       "kickoff_bjt":kickoff.isoformat(),
       "observed_at_utc":end.isoformat(),
       "hours_before_kickoff_at_receipt":round((kickoff-end).total_seconds()/3600,3),
       "numeric_had_pre_kickoff":numeric is not None,
       "strict_had_pre_kickoff":strict is not None,
       "rejection_reasons":reasons}
    if strict:
        if not start<strict["kickoff"]:raise ValueError("capture request cannot start post kickoff")
        r["frozen_had_odds"]=strict["odds"]
        r["frozen_had_fair_market_probabilities"]=strict["p"]
        r["provider_had_updated_at_bjt"]=strict["provider"].isoformat()
        r["provider_quote_age_hours"]=round((end-strict["provider"]).total_seconds()/3600,3)
        r["overround"]=round(sum(1/v for v in strict["odds"])-1,6)
    return r

def run(manifest_path:Path):
    man,matches,start,end=validate_source(manifest_path,require_now_before_kickoff=False)
    rows=[classify_one(m,start,end) for m in matches]
    stat=Counter(reason for r in rows for reason in r["rejection_reasons"])
    # Anchor source manifest provenance, separate from source raw byte digest.
    manifest_sha=hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()
    res={"type":"EVLAB_TASK0040_NEW_PREKICKOFF_WINDOW",
         "dataset_period":"2026-10-26",
         "raw_sha256":man["sha256"],"manifest_sha256":manifest_sha,
         "raw_bytes":man["raw_bytes"],"source_url":man["url"],
         "request_started_at_utc":start.isoformat(),
         "response_received_at_utc":end.isoformat(),
         "fixture_total":len(rows),
         "strict_had_accepted":sum(r["strict_had_pre_kickoff"] for r in rows),
         "numeric_had_accepted":sum(r["numeric_had_pre_kickoff"] for r in rows),
         "rejected_strict_reasons":dict(sorted(stat.items())),
         "matches":rows,
         "score_evaluation_status":"NOT_STARTED_PRE_MATCH",
         "forecast_status":"NONE_FROZEN_DO_NOT_INVENT",
         "no_result_join":True,
         "no_executable_odds_claim":True,
         "caveats":[
           "Local observed receipt clock plus source raw bytes; external timestamp authority not attested.",
           "Provider updated-at is not the observer timestamp; stale source quotes may be present.",
           "Single sample is not a working recurring collector.",
           "This audit never imports a match result or evaluates predictions."
         ]}
    return res

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    v=ap.parse_args()
    result=run(v.manifest)
    v.out.parent.mkdir(parents=True,exist_ok=True)
    v.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:r for k,r in result.items() if k!="matches"},ensure_ascii=False))
    for z in result["matches"]:
        print(json.dumps({k:val for k,val in z.items() if k not in ("frozen_had_fair_market_probabilities",)},ensure_ascii=False))
if __name__=="__main__":main()
