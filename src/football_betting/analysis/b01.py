"""TASK-0008 pre-registered same-time B01 residual analysis."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import asdict
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


def proxy_edges(
    reference_odds: tuple[float, float, float],
    sporttery_odds: tuple[float, float, float],
) -> dict[str, float]:
    probs = devig_from_odds(dict(zip(SIDES, reference_odds, strict=True)))
    return {
        side: probs[side] * jc_odds - 1.0
        for side, jc_odds in zip(SIDES, sporttery_odds, strict=True)
    }


def threshold_key(value: float) -> str:
    return "gt0" if value == 0.0 else f"ge{int(value * 100)}"


def qualifies(edge: float, threshold: float) -> bool:
    return edge > 0.0 if threshold == 0.0 else edge >= threshold


def collapse_episodes(rows: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
    """Collapse consecutive qualifying round_seq values per fixture/side/variant."""
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if qualifies(float(row["proxy_implied_edge"]), threshold):
            grouped[
                (
                    str(row["match_id"]),
                    str(row["side"]),
                    str(row["source_variant"] or "<none>"),
                )
            ].append(row)

    episodes: list[dict[str, Any]] = []
    for (match_id, side, variant), items in grouped.items():
        items.sort(key=lambda x: (int(x["round_seq"]), str(x["observed_at"])))
        current: list[dict[str, Any]] = []
        for item in items:
            if not current or int(item["round_seq"]) == int(current[-1]["round_seq"]) + 1:
                current.append(item)
            else:
                episodes.append(_episode(match_id, side, variant, current, threshold))
                current = [item]
        if current:
            episodes.append(_episode(match_id, side, variant, current, threshold))
    return episodes


def _episode(
    match_id: str,
    side: str,
    variant: str,
    rows: list[dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    start = parse_time(str(rows[0]["observed_at"]))
    end = parse_time(str(rows[-1]["observed_at"]))
    duration = 0.0
    if start is not None and end is not None:
        duration = max(0.0, (end - start).total_seconds())
    return {
        "match_id": match_id,
        "side": side,
        "source_variant": variant,
        "threshold": threshold_key(threshold),
        "start_at": rows[0]["observed_at"],
        "end_at": rows[-1]["observed_at"],
        "duration_seconds": duration,
        "rounds": len(rows),
        "max_edge": max(float(r["proxy_implied_edge"]) for r in rows),
        "median_edge": median(float(r["proxy_implied_edge"]) for r in rows),
    }


def _regular_capture_pairs(con: sqlite3.Connection) -> dict[str, dict[str, sqlite3.Row]]:
    pairs: dict[str, dict[str, sqlite3.Row]] = defaultdict(dict)
    sql = """SELECT * FROM captures
             WHERE capture_kind='regular' AND failure_class IS NULL
             ORDER BY response_received_at, capture_id"""
    for row in con.execute(sql):
        if row["source"] in {"official_sporttery", "reference_betexplorer"}:
            pairs[row["round_id"]][row["source"]] = row
    return pairs


def _sport_facts(con: sqlite3.Connection) -> dict[int, dict[str, sqlite3.Row]]:
    out: dict[int, dict[str, sqlite3.Row]] = defaultdict(dict)
    for row in con.execute("SELECT * FROM sporttery_facts ORDER BY fact_id"):
        if row["match_id"]:
            out[int(row["capture_id"])][str(row["match_id"])] = row
    return out


def _ref_facts(con: sqlite3.Connection) -> dict[int, dict[str, sqlite3.Row]]:
    out: dict[int, dict[str, sqlite3.Row]] = defaultdict(dict)
    for row in con.execute(
        """SELECT * FROM betexplorer_facts
           WHERE home_odds IS NOT NULL AND draw_odds IS NOT NULL AND away_odds IS NOT NULL
           ORDER BY fact_id"""
    ):
        out[int(row["capture_id"])][str(row["event_id"])] = row
    return out


def _future_reference_index(
    con: sqlite3.Connection,
) -> dict[tuple[str, str], list[tuple[datetime, tuple[float, float, float]]]]:
    out: dict[tuple[str, str], list[tuple[datetime, tuple[float, float, float]]]] = defaultdict(list)
    for row in con.execute(
        """SELECT event_id, source_variant, response_received_at,
                  home_odds, draw_odds, away_odds
           FROM betexplorer_facts
           WHERE home_odds IS NOT NULL AND draw_odds IS NOT NULL AND away_odds IS NOT NULL
           ORDER BY response_received_at, fact_id"""
    ):
        stamp = parse_time(row["response_received_at"])
        if stamp is None:
            continue
        out[(str(row["event_id"]), str(row["source_variant"] or "<none>"))].append(
            (
                stamp,
                (float(row["home_odds"]), float(row["draw_odds"]), float(row["away_odds"])),
            )
        )
    return out


def _future_edge(
    observations: list[tuple[datetime, tuple[float, float, float]]],
    *,
    observed_at: datetime,
    target_at: datetime | None,
    kickoff: datetime,
    sporttery_price: float,
    side: str,
) -> float | None:
    candidates = [
        (stamp, odds)
        for stamp, odds in observations
        if stamp > observed_at and stamp < kickoff and (target_at is None or stamp >= target_at)
    ]
    if not candidates:
        return None
    _, odds = candidates[0]
    probs = devig_from_odds(dict(zip(SIDES, odds, strict=True)))
    return probs[side] * sporttery_price - 1.0


def analyze(
    db_path: str | Path,
    team_map_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with closing(_open_ro(db_path)) as con:
        team_map = TeamNameMap(team_map_path)
        crosswalk, identity, _ = build_crosswalk(con, team_map)
        reverse = {match_id: event_id for event_id, match_id in crosswalk.items()}
        capture_pairs = _regular_capture_pairs(con)
        sport = _sport_facts(con)
        refs = _ref_facts(con)
        future_index = _future_reference_index(con)

        observations: list[dict[str, Any]] = []
        accepted_round_pairs = 0
        skipped_nonexec = 0
        skipped_postkickoff = 0
        skipped_missing = 0

        for round_id, pair in capture_pairs.items():
            sp_cap = pair.get("official_sporttery")
            be_cap = pair.get("reference_betexplorer")
            if sp_cap is None or be_cap is None:
                continue
            accepted_round_pairs += 1
            round_seq = sp_cap["round_seq"]
            if round_seq is None:
                continue
            variant = str(be_cap["source_variant"] or "<none>")
            observed = parse_time(be_cap["response_received_at"])
            if observed is None:
                continue
            sp_rows = sport.get(int(sp_cap["capture_id"]), {})
            be_rows = refs.get(int(be_cap["capture_id"]), {})

            for match_id, event_id in reverse.items():
                sf = sp_rows.get(match_id)
                bf = be_rows.get(event_id)
                if sf is None or bf is None:
                    skipped_missing += 1
                    continue
                kickoff = parse_time(bf["kickoff_utc"])
                if kickoff is None or observed >= kickoff:
                    skipped_postkickoff += 1
                    continue
                jc_odds = (sf["had_h"], sf["had_d"], sf["had_a"])
                ref_odds = (bf["home_odds"], bf["draw_odds"], bf["away_odds"])
                if any(v is None for v in jc_odds + ref_odds):
                    skipped_missing += 1
                    continue
                exec_state = executable_had(
                    pool_status=sf["had_pool_status"],
                    betting_single=sf["had_betting_single"],
                    betting_allup=sf["had_betting_allup"],
                    close_date=sf["had_close_date"],
                    close_time=sf["had_close_time"],
                    observed_at=observed,
                )
                if exec_state is not True:
                    skipped_nonexec += 1
                    continue

                jc_tuple = tuple(float(v) for v in jc_odds)
                ref_tuple = tuple(float(v) for v in ref_odds)
                edges = proxy_edges(ref_tuple, jc_tuple)
                for side, jc_price in zip(SIDES, jc_tuple, strict=True):
                    observations.append(
                        {
                            "round_id": round_id,
                            "round_seq": int(round_seq),
                            "event_id": event_id,
                            "match_id": match_id,
                            "side": side,
                            "source_variant": variant,
                            "observed_at": observed.isoformat(),
                            "kickoff_utc": kickoff.isoformat(),
                            "sporttery_odds": jc_price,
                            "reference_h": ref_tuple[0],
                            "reference_d": ref_tuple[1],
                            "reference_a": ref_tuple[2],
                            "proxy_implied_edge": edges[side],
                        }
                    )

        threshold_summary: dict[str, Any] = {}
        all_episodes: list[dict[str, Any]] = []
        for threshold in THRESHOLDS:
            key = threshold_key(threshold)
            positive = [r for r in observations if qualifies(float(r["proxy_implied_edge"]), threshold)]
            episodes = collapse_episodes(observations, threshold)
            all_episodes.extend(episodes)
            fixtures = {str(r["match_id"]) for r in positive}
            fixture_sides = {(str(r["match_id"]), str(r["side"])) for r in positive}
            days = {str(r["observed_at"])[:10] for r in positive}
            by_fixture = Counter(str(r["match_id"]) for r in positive)
            threshold_summary[key] = {
                "rows": len(positive),
                "fixture_selection_pairs": len(fixture_sides),
                "fixtures": len(fixtures),
                "calendar_days": len(days),
                "episodes": len(episodes),
                "median_episode_rounds": median([e["rounds"] for e in episodes]) if episodes else 0,
                "max_episode_rounds": max([e["rounds"] for e in episodes], default=0),
                "top_fixture_rows": by_fixture.most_common(10),
            }

        variants: dict[str, Any] = {}
        for variant in sorted({str(r["source_variant"]) for r in observations}):
            vr = [r for r in observations if r["source_variant"] == variant]
            variants[variant] = {
                "rows": len(vr),
                "fixtures": len({str(r["match_id"]) for r in vr}),
                "positive_gt0": sum(float(r["proxy_implied_edge"]) > 0 for r in vr),
                "ge2": sum(float(r["proxy_implied_edge"]) >= 0.02 for r in vr),
                "ge5": sum(float(r["proxy_implied_edge"]) >= 0.05 for r in vr),
                "ge10": sum(float(r["proxy_implied_edge"]) >= 0.10 for r in vr),
                "median_edge": median(float(r["proxy_implied_edge"]) for r in vr) if vr else None,
            }

        multi_variant_fixture_sides: dict[str, Any] = {}
        fs_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in observations:
            fs_groups[(str(row["match_id"]), str(row["side"]))].append(row)
        for (match_id, side), items in fs_groups.items():
            seen_variants = sorted({str(r["source_variant"]) for r in items})
            if len(seen_variants) < 2:
                continue
            per_variant = {}
            for variant in seen_variants:
                vals = [
                    float(r["proxy_implied_edge"])
                    for r in items
                    if r["source_variant"] == variant
                ]
                per_variant[variant] = {
                    "n": len(vals),
                    "median_edge": median(vals),
                    "positive_share": sum(v > 0 for v in vals) / len(vals),
                }
            multi_variant_fixture_sides[f"{match_id}:{side}"] = per_variant

        forward: dict[str, Counter[str]] = {
            "next": Counter(),
            "5m": Counter(),
            "30m": Counter(),
            "60m": Counter(),
        }
        for row in observations:
            if float(row["proxy_implied_edge"]) <= 0:
                continue
            obs = parse_time(str(row["observed_at"]))
            kickoff = parse_time(str(row["kickoff_utc"]))
            if obs is None or kickoff is None:
                continue
            seq = future_index.get((str(row["event_id"]), str(row["source_variant"])), [])
            current = float(row["proxy_implied_edge"])
            side = str(row["side"])
            for label, minutes in (("next", None), ("5m", 5), ("30m", 30), ("60m", 60)):
                target = None if minutes is None else obs + timedelta(minutes=minutes)
                future_edge = _future_edge(
                    seq,
                    observed_at=obs,
                    target_at=target,
                    kickoff=kickoff,
                    sporttery_price=float(row["sporttery_odds"]),
                    side=side,
                )
                if future_edge is None:
                    forward[label]["censored"] += 1
                elif future_edge < current - 1e-12:
                    forward[label]["reduces_residual"] += 1
                elif future_edge > current + 1e-12:
                    forward[label]["increases_residual"] += 1
                else:
                    forward[label]["unchanged"] += 1

        edges = [float(r["proxy_implied_edge"]) for r in observations]
        summary = {
            "identity": asdict(identity),
            "accepted_regular_round_pairs": accepted_round_pairs,
            "observation_rows": len(observations),
            "fixtures": len({str(r["match_id"]) for r in observations}),
            "fixture_selection_pairs": len({(str(r["match_id"]), str(r["side"])) for r in observations}),
            "variants": variants,
            "multi_variant_fixture_sides": multi_variant_fixture_sides,
            "thresholds": threshold_summary,
            "edge_distribution": {
                "min": min(edges) if edges else None,
                "median": median(edges) if edges else None,
                "max": max(edges) if edges else None,
            },
            "forward_reference": {k: dict(v) for k, v in forward.items()},
            "skipped": {
                "missing_pair_fact": skipped_missing,
                "non_executable": skipped_nonexec,
                "post_kickoff": skipped_postkickoff,
            },
        }

        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if observations:
            with (out / "observations.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(observations[0]))
                writer.writeheader()
                writer.writerows(observations)
        if all_episodes:
            with (out / "episodes.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(all_episodes[0]))
                writer.writeheader()
                writer.writerows(all_episodes)
        return summary
