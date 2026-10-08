#!/usr/bin/env python3
"""Independent standard-library audit for TASK-0007.

Deliberately does not import football_betting.analysis.d01b or matching helpers.
It recomputes the preregistered headline counts from the SQLite ledger plus the
versioned identity asset, so agreement is meaningful rather than circular.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BEIJING = timezone(timedelta(hours=8))
SIDES = ("H", "D", "A")


def stamp(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"naive timestamp: {value}")
    return parsed


def odds_tuple(row: sqlite3.Row | None) -> tuple[float, float, float] | None:
    if row is None:
        return None
    values = (row["had_h"], row["had_d"], row["had_a"])
    if any(value is None for value in values):
        return None
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def tuple_json(value: str) -> tuple[float, float, float]:
    raw = json.loads(value)
    return (float(raw[0]), float(raw[1]), float(raw[2]))


def devig(odds: tuple[float, float, float]) -> tuple[float, float, float]:
    raw = tuple(1.0 / value for value in odds)
    total = sum(raw)
    return tuple(value / total for value in raw)  # type: ignore[return-value]


def executable(row: sqlite3.Row, observed: datetime) -> bool:
    if str(row["had_pool_status"] or "").casefold() != "selling":
        return False
    if row["had_betting_single"] != 1 and row["had_betting_allup"] != 1:
        return False
    date_part = row["had_close_date"]
    time_part = row["had_close_time"]
    if bool(date_part) != bool(time_part):
        return False
    if date_part and time_part:
        close = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                close = datetime.strptime(
                    f"{date_part} {time_part}", fmt
                ).replace(tzinfo=BEIJING)
                break
            except ValueError:
                continue
        if close is None or observed > close:
            return False
    return True


def load_exact_identity(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("TASK0007_IDENTITY_ONLY")
    if not isinstance(rows, list):
        raise RuntimeError("TASK0007_IDENTITY_ONLY asset is missing")
    result: dict[str, str] = {}
    for row in rows:
        cn = str(row.get("cn") or "").strip()
        en = str(row.get("en") or "").strip()
        if not cn or not en:
            continue
        if cn in result and result[cn] != en:
            raise RuntimeError(f"ambiguous audit identity for {cn!r}")
        result[cn] = en
    return result


def build_crosswalk(
    con: sqlite3.Connection, identity: dict[str, str]
) -> dict[str, str]:
    sport: dict[str, tuple[str, str, datetime]] = {}
    for row in con.execute(
        """SELECT DISTINCT match_id, home, away, kickoff_local
           FROM sporttery_facts WHERE kickoff_local IS NOT NULL"""
    ):
        kickoff = stamp(row["kickoff_local"])
        if kickoff is None:
            continue
        sport[row["match_id"]] = (row["home"], row["away"], kickoff)

    reference: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for row in con.execute(
        """SELECT DISTINCT event_id, home, away, kickoff_utc
           FROM betexplorer_facts WHERE kickoff_utc IS NOT NULL"""
    ):
        reference[row["event_id"]].add(
            (row["home"], row["away"], row["kickoff_utc"])
        )

    crosswalk: dict[str, str] = {}
    for match_id, (home_cn, away_cn, kickoff) in sport.items():
        home_en = identity.get(home_cn)
        away_en = identity.get(away_cn)
        if not home_en or not away_en:
            continue
        kickoff_utc = kickoff.astimezone(timezone.utc)
        hits: list[str] = []
        for event_id, values in reference.items():
            if len(values) != 1:
                continue
            home, away, ref_kickoff_raw = next(iter(values))
            ref_kickoff = stamp(ref_kickoff_raw)
            if ref_kickoff is None:
                continue
            if (
                home == home_en
                and away == away_en
                and abs((ref_kickoff - kickoff_utc).total_seconds()) <= 900
            ):
                hits.append(event_id)
        if len(hits) == 1:
            event_id = hits[0]
            if event_id in crosswalk and crosswalk[event_id] != match_id:
                raise RuntimeError(f"duplicate event mapping {event_id}")
            crosswalk[event_id] = match_id
    return crosswalk


def batch_label(size: int) -> str:
    if size == 1:
        return "1"
    if size <= 5:
        return "2-5"
    if size <= 20:
        return "6-20"
    return ">20"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--team-map", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    con = sqlite3.connect(f"file:{Path(args.db).resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        identity = load_exact_identity(Path(args.team_map))
        crosswalk = build_crosswalk(con, identity)

        sport: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for row in con.execute(
            """SELECT sf.*, c.response_received_at AS capture_received_at,
                      c.capture_kind
               FROM sporttery_facts sf
               JOIN captures c ON c.capture_id=sf.capture_id
               WHERE c.source='official_sporttery' AND c.failure_class IS NULL
               ORDER BY c.response_received_at"""
        ):
            sport[row["match_id"]].append(row)

        confirmations: dict[tuple[int, str], sqlite3.Row] = {}
        for row in con.execute(
            """SELECT sf.*, c.response_received_at AS capture_received_at
               FROM sporttery_facts sf
               JOIN captures c ON c.capture_id=sf.capture_id
               WHERE c.capture_kind='change_confirmation'
                 AND c.source='official_sporttery'
                 AND c.failure_class IS NULL"""
        ):
            confirmations[(int(row["capture_id"]), row["match_id"])] = row

        batch_sizes = {
            int(row["confirmation_capture_id"]): int(row["n"])
            for row in con.execute(
                """SELECT confirmation_capture_id, COUNT(*) n
                   FROM reference_changes
                   WHERE confirmation_capture_id IS NOT NULL
                   GROUP BY confirmation_capture_id"""
            )
        }

        matched_by_batch: Counter[str] = Counter()
        analyzable_by_batch: Counter[str] = Counter()
        primary_by_batch: Counter[str] = Counter()
        primary_exact_batch: Counter[int] = Counter()
        primary_confirmation_ids: set[int] = set()
        primary_events: set[str] = set()
        primary_matches: set[str] = set()
        primary_days: set[str] = set()
        ref_next: Counter[str] = Counter()
        primary_ref_next: Counter[str] = Counter()

        thresholds = (0.0, 0.02, 0.05, 0.10)
        threshold_rows = Counter()
        threshold_matches: dict[str, set[str]] = {
            str(value): set() for value in thresholds
        }
        threshold_confirmations: dict[str, set[int]] = {
            str(value): set() for value in thresholds
        }

        matched = analyzable = primary = 0
        for change in con.execute(
            "SELECT * FROM reference_changes ORDER BY change_id"
        ):
            event_id = change["event_id"]
            match_id = crosswalk.get(event_id)
            if match_id is None:
                continue
            confirmation_id = change["confirmation_capture_id"]
            if confirmation_id is None:
                continue
            size = batch_sizes[int(confirmation_id)]
            label = batch_label(size)
            matched += 1
            matched_by_batch[label] += 1

            prev_time = stamp(change["previous_response_received_at"])
            curr_time = stamp(change["current_response_received_at"])
            if prev_time is None or curr_time is None:
                continue
            previous = tuple_json(change["previous_tuple"])
            current = tuple_json(change["current_tuple"])

            next_row = con.execute(
                """SELECT home_odds, draw_odds, away_odds
                   FROM betexplorer_facts
                   WHERE event_id=? AND source_variant IS ?
                     AND response_received_at>?
                   ORDER BY response_received_at, fact_id LIMIT 1""",
                (event_id, change["source_variant"], curr_time.isoformat()),
            ).fetchone()
            state = "no_next_observation"
            if next_row is not None:
                next_odds = tuple(float(next_row[i]) for i in range(3))
                if next_odds == previous:
                    state = "one_step_reversion"
                elif next_odds == current:
                    state = "persists_next_observation"
                else:
                    state = "moves_again"
            ref_next[state] += 1

            baseline = None
            for row in sport[match_id]:
                observed = stamp(row["capture_received_at"])
                if (
                    observed is not None
                    and observed <= prev_time
                    and row["capture_kind"] == "regular"
                ):
                    baseline = row
                elif observed is not None and observed > prev_time:
                    break
            confirm = confirmations.get((int(confirmation_id), match_id))
            if baseline is None or confirm is None:
                continue
            confirm_time = stamp(confirm["capture_received_at"])
            if confirm_time is None or confirm_time < curr_time:
                continue
            base_odds = odds_tuple(baseline)
            confirm_odds = odds_tuple(confirm)
            if base_odds is None or confirm_odds is None:
                continue
            if (
                baseline["provider_had_updated_at"] is None
                or confirm["provider_had_updated_at"] is None
            ):
                continue
            analyzable += 1
            analyzable_by_batch[label] += 1

            stale = (
                base_odds == confirm_odds
                and baseline["provider_had_updated_at"]
                == confirm["provider_had_updated_at"]
            )
            if not stale or not executable(confirm, confirm_time):
                continue

            primary += 1
            primary_by_batch[label] += 1
            primary_exact_batch[size] += 1
            primary_confirmation_ids.add(int(confirmation_id))
            primary_events.add(event_id)
            primary_matches.add(match_id)
            primary_days.add(curr_time.date().isoformat())
            primary_ref_next[state] += 1

            q_current = devig(current)
            q_previous = devig(previous)
            evs = [
                q_current[i] * confirm_odds[i] - 1.0
                for i in range(3)
                if q_current[i] - q_previous[i] > 0
            ]
            for threshold in thresholds:
                if any(value > threshold if threshold == 0.0 else value >= threshold for value in evs):
                    key = str(threshold)
                    threshold_rows[key] += 1
                    threshold_matches[key].add(match_id)
                    threshold_confirmations[key].add(int(confirmation_id))

        output: dict[str, Any] = {
            "crosswalk_events": len(crosswalk),
            "matched_change_rows": matched,
            "analyzable_change_rows": analyzable,
            "primary_candidate_rows": primary,
            "primary_candidate_event_ids": len(primary_events),
            "primary_candidate_matches": len(primary_matches),
            "primary_candidate_days": len(primary_days),
            "primary_confirmation_captures": len(primary_confirmation_ids),
            "matched_by_batch_stratum": dict(sorted(matched_by_batch.items())),
            "analyzable_by_batch_stratum": dict(sorted(analyzable_by_batch.items())),
            "primary_by_batch_stratum": dict(sorted(primary_by_batch.items())),
            "primary_exact_batch_sizes": {
                str(key): value for key, value in sorted(primary_exact_batch.items())
            },
            "reference_next_state": dict(sorted(ref_next.items())),
            "primary_reference_next_state": dict(sorted(primary_ref_next.items())),
            "proxy_ev_threshold_rows": dict(threshold_rows),
            "proxy_ev_threshold_matches": {
                key: len(value) for key, value in threshold_matches.items()
            },
            "proxy_ev_threshold_confirmation_captures": {
                key: len(value) for key, value in threshold_confirmations.items()
            },
        }
        Path(args.output).write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(output, indent=2, sort_keys=True))
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
