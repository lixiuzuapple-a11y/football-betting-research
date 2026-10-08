from __future__ import annotations

import argparse
import json
import sqlite3
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any

from football_betting.analysis.d01b import (
    SIDES,
    _open_ro,
    build_crosswalk,
    executable_had,
    parse_time,
)
from football_betting.matching.teams import TeamNameMap
from football_betting.odds.implied import devig_from_odds

THRESHOLDS = (0.0, 0.02, 0.05, 0.10)


def edge(ref: tuple[float, float, float], jc: tuple[float, float, float], side: str) -> float:
    p = devig_from_odds(dict(zip(SIDES, ref, strict=True)))
    return p[side] * jc[SIDES.index(side)] - 1.0


def qualifies(value: float, threshold: float) -> bool:
    return value > 0.0 if threshold == 0.0 else value >= threshold


def tkey(threshold: float) -> str:
    return "gt0" if threshold == 0.0 else f"ge{int(threshold*100)}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--team-map", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with closing(_open_ro(args.db)) as con:
        crosswalk, identity, _ = build_crosswalk(con, TeamNameMap(args.team_map))
        reverse = {m: e for e, m in crosswalk.items()}

        captures: dict[str, dict[str, sqlite3.Row]] = defaultdict(dict)
        for row in con.execute(
            """SELECT * FROM captures
               WHERE capture_kind='regular' AND failure_class IS NULL
               ORDER BY capture_id"""
        ):
            if row["source"] in {"official_sporttery", "reference_betexplorer"}:
                captures[str(row["round_id"])][str(row["source"])] = row

        sf_by_capture: dict[int, dict[str, sqlite3.Row]] = defaultdict(dict)
        for row in con.execute("SELECT * FROM sporttery_facts ORDER BY fact_id"):
            if row["match_id"]:
                sf_by_capture[int(row["capture_id"])][str(row["match_id"])] = row

        bf_by_capture: dict[int, dict[str, sqlite3.Row]] = defaultdict(dict)
        future: dict[tuple[str, str], list[tuple[datetime, tuple[float,float,float]]]] = defaultdict(list)
        for row in con.execute(
            """SELECT * FROM betexplorer_facts
               WHERE home_odds IS NOT NULL AND draw_odds IS NOT NULL AND away_odds IS NOT NULL
               ORDER BY response_received_at, fact_id"""
        ):
            bf_by_capture[int(row["capture_id"])][str(row["event_id"])] = row
            stamp = parse_time(row["response_received_at"])
            if stamp is not None:
                future[(str(row["event_id"]), str(row["source_variant"] or "<none>"))].append(
                    (stamp, (float(row["home_odds"]),float(row["draw_odds"]),float(row["away_odds"])))
                )

        observations: list[dict[str, Any]] = []
        paired_rounds = 0
        for round_id, pair in captures.items():
            sp = pair.get("official_sporttery")
            be = pair.get("reference_betexplorer")
            if sp is None or be is None:
                continue
            paired_rounds += 1
            if sp["round_seq"] is None:
                continue
            observed = parse_time(be["response_received_at"])
            if observed is None:
                continue
            variant = str(be["source_variant"] or "<none>")
            srows = sf_by_capture.get(int(sp["capture_id"]), {})
            brows = bf_by_capture.get(int(be["capture_id"]), {})
            for match_id, event_id in reverse.items():
                sf = srows.get(match_id)
                bf = brows.get(event_id)
                if sf is None or bf is None:
                    continue
                kickoff = parse_time(bf["kickoff_utc"])
                if kickoff is None or observed >= kickoff:
                    continue
                vals=(sf["had_h"],sf["had_d"],sf["had_a"],bf["home_odds"],bf["draw_odds"],bf["away_odds"])
                if any(v is None for v in vals):
                    continue
                if executable_had(
                    pool_status=sf["had_pool_status"],
                    betting_single=sf["had_betting_single"],
                    betting_allup=sf["had_betting_allup"],
                    close_date=sf["had_close_date"],
                    close_time=sf["had_close_time"],
                    observed_at=observed,
                ) is not True:
                    continue
                jc=(float(sf["had_h"]),float(sf["had_d"]),float(sf["had_a"]))
                ref=(float(bf["home_odds"]),float(bf["draw_odds"]),float(bf["away_odds"]))
                p=devig_from_odds(dict(zip(SIDES,ref,strict=True)))
                for idx,side in enumerate(SIDES):
                    observations.append({
                        "round_seq":int(sp["round_seq"]),
                        "match_id":match_id,
                        "event_id":event_id,
                        "side":side,
                        "variant":variant,
                        "observed_at":observed,
                        "kickoff":kickoff,
                        "sporttery_price":jc[idx],
                        "edge":p[side]*jc[idx]-1.0,
                    })

        threshold_summary={}
        for threshold in THRESHOLDS:
            pos=[r for r in observations if qualifies(r["edge"],threshold)]
            grouped: dict[tuple[str,str,str],list[dict[str,Any]]] = defaultdict(list)
            for r in pos:
                grouped[(r["match_id"],r["side"],r["variant"])].append(r)
            episodes=0
            for items in grouped.values():
                seq=sorted({int(r["round_seq"]) for r in items})
                if not seq:
                    continue
                episodes += 1
                episodes += sum(b != a+1 for a,b in zip(seq,seq[1:]))
            threshold_summary[tkey(threshold)]={
                "rows":len(pos),
                "fixtures":len({r["match_id"] for r in pos}),
                "fixture_selection_pairs":len({(r["match_id"],r["side"]) for r in pos}),
                "episodes":episodes,
            }

        per_fs_variant: dict[tuple[str,str],dict[str,list[float]]] = defaultdict(lambda: defaultdict(list))
        for r in observations:
            per_fs_variant[(r["match_id"],r["side"])][r["variant"]].append(r["edge"])
        sign_flip=0
        all_multi=0
        variant_presence_inconsistent=0
        for variants in per_fs_variant.values():
            if len(variants)<2:
                continue
            all_multi += 1
            meds=[median(v) for v in variants.values()]
            if min(meds)<0<max(meds):
                sign_flip += 1
            presence=[any(x>0 for x in vals) for vals in variants.values()]
            if any(presence) and not all(presence):
                variant_presence_inconsistent += 1

        forward_summary={}
        positives=[r for r in observations if r["edge"]>0]
        for label,minutes in (("next",None),("5m",5),("30m",30),("60m",60)):
            c=Counter()
            for r in positives:
                seq=future.get((r["event_id"],r["variant"]),[])
                if not seq:
                    c["censored"]+=1; continue
                if minutes is None:
                    probe=(r["observed_at"],(float("inf"),)*3)
                    idx=bisect_right(seq,probe)
                else:
                    target=r["observed_at"]+timedelta(minutes=minutes)
                    probe=(target,(float("-inf"),)*3)
                    idx=bisect_left(seq,probe)
                if idx>=len(seq) or seq[idx][0]>=r["kickoff"]:
                    c["censored"]+=1; continue
                future_edge=edge(seq[idx][1], (r["sporttery_price"],)*3, r["side"])
                if future_edge < r["edge"]-1e-12: c["reduces_residual"]+=1
                elif future_edge > r["edge"]+1e-12: c["increases_residual"]+=1
                else: c["unchanged"]+=1
            forward_summary[label]=dict(c)

        result={
            "identity":identity.__dict__ if hasattr(identity,"__dict__") else {
                k:getattr(identity,k) for k in identity.__slots__
            },
            "paired_rounds":paired_rounds,
            "observation_rows":len(observations),
            "fixtures":len({r["match_id"] for r in observations}),
            "fixture_selection_pairs":len({(r["match_id"],r["side"]) for r in observations}),
            "thresholds":threshold_summary,
            "variant_count":len({r["variant"] for r in observations}),
            "multi_variant_fixture_sides":all_multi,
            "median_sign_flip_fixture_sides":sign_flip,
            "positive_presence_inconsistent_fixture_sides":variant_presence_inconsistent,
            "forward_reference":forward_summary,
        }
        Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2,sort_keys=True))


if __name__ == "__main__":
    main()
