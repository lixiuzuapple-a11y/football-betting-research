"""Pre-registered D01-B prospective lead-lag analysis helpers."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from football_betting.matching.teams import (
    ReferenceFixture,
    SportteryFixture,
    TeamNameMap,
    match_fixture,
)
from football_betting.odds.implied import devig_from_odds

BEIJING = timezone(timedelta(hours=8))
SIDES = ("H", "D", "A")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None:
        raise ValueError(f"naive timestamp is not allowed: {value}")
    return stamp


def parse_tuple(value: str) -> tuple[float, float, float]:
    raw = json.loads(value)
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        raise ValueError(f"expected 1X2 triple, got {raw!r}")
    return (float(raw[0]), float(raw[1]), float(raw[2]))


def batch_stratum(size: int) -> str:
    if size < 1:
        raise ValueError("batch size must be positive")
    if size == 1:
        return "1"
    if size <= 5:
        return "2-5"
    if size <= 20:
        return "6-20"
    return ">20"


def executable_had(
    *,
    pool_status: str | None,
    betting_single: int | None,
    betting_allup: int | None,
    close_date: str | None,
    close_time: str | None,
    observed_at: datetime,
) -> bool | None:
    """Strict primary executability rule from TASK-0007 §7.4."""
    if pool_status is None or pool_status.strip().casefold() != "selling":
        return False if pool_status is not None else None
    if betting_single != 1 and betting_allup != 1:
        if betting_single is None and betting_allup is None:
            return None
        return False

    if close_date and close_time:
        close_stamp: datetime | None = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                close_stamp = datetime.strptime(
                    f"{close_date} {close_time}", fmt
                ).replace(tzinfo=BEIJING)
                break
            except ValueError:
                continue
        if close_stamp is None:
            return None
        if observed_at > close_stamp:
            return False
    elif bool(close_date) != bool(close_time):
        return None
    return True


def observed_stale(
    baseline_odds: tuple[float, float, float] | None,
    baseline_provider_time: str | None,
    confirmation_odds: tuple[float, float, float] | None,
    confirmation_provider_time: str | None,
) -> bool | None:
    if (
        baseline_odds is None
        or confirmation_odds is None
        or baseline_provider_time is None
        or confirmation_provider_time is None
    ):
        return None
    return (
        baseline_odds == confirmation_odds
        and baseline_provider_time == confirmation_provider_time
    )


def proxy_metrics(
    previous_odds: tuple[float, float, float],
    current_odds: tuple[float, float, float],
    sporttery_odds: tuple[float, float, float],
) -> list[dict[str, float | str]]:
    prev = devig_from_odds(dict(zip(SIDES, previous_odds, strict=True)))
    curr = devig_from_odds(dict(zip(SIDES, current_odds, strict=True)))
    rows: list[dict[str, float | str]] = []
    for side, jc_odds in zip(SIDES, sporttery_odds, strict=True):
        delta = curr[side] - prev[side]
        if delta <= 0:
            continue
        rows.append(
            {
                "side": side,
                "q_previous": prev[side],
                "q_current": curr[side],
                "delta_q": delta,
                "sporttery_odds": jc_odds,
                "proxy_implied_ev": curr[side] * jc_odds - 1.0,
                "change_induced_ev_gain": delta * jc_odds,
            }
        )
    return rows


@dataclass(frozen=True, slots=True)
class IdentitySummary:
    reference_events: int
    sporttery_matches: int
    matched_reference_events: int
    unmatched_reference_events: int
    ambiguous_reference_identities: int
    ambiguous_sporttery_identities: int


def _open_ro(path: str | Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _unique_reference_fixtures(
    con: sqlite3.Connection,
) -> tuple[list[ReferenceFixture], int]:
    grouped: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for row in con.execute(
        """SELECT event_id, home, away, kickoff_utc
           FROM betexplorer_facts
           WHERE home IS NOT NULL AND away IS NOT NULL AND kickoff_utc IS NOT NULL"""
    ):
        grouped[row["event_id"]].add((row["home"], row["away"], row["kickoff_utc"]))
    fixtures: list[ReferenceFixture] = []
    ambiguous = 0
    for event_id, identities in grouped.items():
        if len(identities) != 1:
            ambiguous += 1
            continue
        home, away, kickoff = next(iter(identities))
        stamp = parse_time(kickoff)
        if stamp is not None:
            fixtures.append(ReferenceFixture(event_id, home, away, stamp))
    return fixtures, ambiguous


def _unique_sporttery_fixtures(
    con: sqlite3.Connection,
) -> tuple[list[SportteryFixture], int]:
    grouped: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for row in con.execute(
        """SELECT match_id, home, away, kickoff_local
           FROM sporttery_facts
           WHERE match_id IS NOT NULL AND home IS NOT NULL
             AND away IS NOT NULL AND kickoff_local IS NOT NULL"""
    ):
        grouped[row["match_id"]].add((row["home"], row["away"], row["kickoff_local"]))
    fixtures: list[SportteryFixture] = []
    ambiguous = 0
    for match_id, identities in grouped.items():
        if len(identities) != 1:
            ambiguous += 1
            continue
        home, away, kickoff = next(iter(identities))
        stamp = parse_time(kickoff)
        if stamp is not None:
            fixtures.append(SportteryFixture(match_id, home, away, stamp))
    return fixtures, ambiguous


def build_crosswalk(
    con: sqlite3.Connection,
    team_map: TeamNameMap,
) -> tuple[dict[str, str], IdentitySummary, list[dict[str, Any]]]:
    refs, ref_ambiguous = _unique_reference_fixtures(con)
    sport, sp_ambiguous = _unique_sporttery_fixtures(con)
    crosswalk: dict[str, str] = {}
    diagnostics: list[dict[str, Any]] = []
    for ref in refs:
        matched = match_fixture(ref, sport, team_map)
        if matched is not None:
            crosswalk[ref.event_id] = matched.match_id
            diagnostics.append(
                {
                    "event_id": ref.event_id,
                    "home": ref.home,
                    "away": ref.away,
                    "kickoff_utc": ref.kickoff_utc.isoformat(),
                    "match_id": matched.match_id,
                    "kickoff_delta_seconds": matched.kickoff_delta_seconds,
                    "status": "matched",
                }
            )
        else:
            diagnostics.append(
                {
                    "event_id": ref.event_id,
                    "home": ref.home,
                    "away": ref.away,
                    "kickoff_utc": ref.kickoff_utc.isoformat(),
                    "match_id": None,
                    "kickoff_delta_seconds": None,
                    "status": "unmatched",
                }
            )
    summary = IdentitySummary(
        reference_events=len(refs),
        sporttery_matches=len(sport),
        matched_reference_events=len(crosswalk),
        unmatched_reference_events=len(refs) - len(crosswalk),
        ambiguous_reference_identities=ref_ambiguous,
        ambiguous_sporttery_identities=sp_ambiguous,
    )
    return crosswalk, summary, diagnostics


def _sporttery_observations(
    con: sqlite3.Connection,
) -> dict[str, list[sqlite3.Row]]:
    by_match: dict[str, list[sqlite3.Row]] = defaultdict(list)
    sql = """SELECT sf.*, c.response_received_at AS capture_received_at,
                    c.capture_kind, c.failure_class
             FROM sporttery_facts sf
             JOIN captures c ON c.capture_id = sf.capture_id
             WHERE c.source='official_sporttery' AND c.failure_class IS NULL
             ORDER BY c.response_received_at"""
    for row in con.execute(sql):
        if row["match_id"]:
            by_match[row["match_id"]].append(row)
    return by_match


def _had_tuple(row: sqlite3.Row | None) -> tuple[float, float, float] | None:
    if row is None or any(row[key] is None for key in ("had_h", "had_d", "had_a")):
        return None
    return (float(row["had_h"]), float(row["had_d"]), float(row["had_a"]))


def _reference_persistence(
    con: sqlite3.Connection,
    *,
    event_id: str,
    variant: str | None,
    current_time: datetime,
    previous_tuple: tuple[float, float, float],
    current_tuple: tuple[float, float, float],
) -> str:
    row = con.execute(
        """SELECT home_odds, draw_odds, away_odds
           FROM betexplorer_facts
           WHERE event_id=? AND source_variant IS ? AND response_received_at>?
           ORDER BY response_received_at, fact_id
           LIMIT 1""",
        (event_id, variant, current_time.isoformat()),
    ).fetchone()
    if row is None:
        return "no_next_observation"
    nxt = (float(row[0]), float(row[1]), float(row[2]))
    if nxt == previous_tuple:
        return "one_step_reversion"
    if nxt == current_tuple:
        return "persists_next_observation"
    return "moves_again"


def _persistence_seconds(
    observations: list[sqlite3.Row],
    *,
    start: datetime,
    baseline_odds: tuple[float, float, float],
    provider_time: str,
    kickoff: datetime | None,
    dataset_end: datetime,
) -> tuple[float, str]:
    horizon_candidates = [dataset_end]
    if kickoff is not None:
        horizon_candidates.append(kickoff)
    horizon = min(horizon_candidates)
    for row in observations:
        observed = parse_time(row["capture_received_at"])
        if observed is None or observed <= start:
            continue
        if observed > horizon:
            break
        odds = _had_tuple(row)
        executable = executable_had(
            pool_status=row["had_pool_status"],
            betting_single=row["had_betting_single"],
            betting_allup=row["had_betting_allup"],
            close_date=row["had_close_date"],
            close_time=row["had_close_time"],
            observed_at=observed,
        )
        if (
            odds != baseline_odds
            or row["provider_had_updated_at"] != provider_time
            or executable is False
        ):
            return (observed - start).total_seconds(), "ended"
    return max(0.0, (horizon - start).total_seconds()), "right_censored"


def analyze(
    db_path: str | Path,
    team_map_path: str | Path,
    output_dir: str | Path,
    *,
    identity_only: bool = False,
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with closing(_open_ro(db_path)) as con:
        team_map = TeamNameMap(team_map_path)
        crosswalk, identity, diagnostics = build_crosswalk(con, team_map)
        (out / "mapping_summary.json").write_text(
            json.dumps(asdict(identity), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with (out / "mapping_diagnostics.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            fieldnames = list(diagnostics[0]) if diagnostics else ["status"]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(diagnostics)

        if identity_only:
            return {"identity": asdict(identity)}

        sport_by_match = _sporttery_observations(con)
        dataset_end = parse_time(
            con.execute("SELECT MAX(response_received_at) FROM captures").fetchone()[0]
        )
        if dataset_end is None:
            raise RuntimeError("dataset has no captures")

        batch_sizes: dict[int, int] = {}
        for row in con.execute(
            """SELECT confirmation_capture_id, COUNT(*) n
               FROM reference_changes
               WHERE confirmation_capture_id IS NOT NULL
               GROUP BY confirmation_capture_id"""
        ):
            batch_sizes[int(row["confirmation_capture_id"])] = int(row["n"])
        batch_values = sorted(batch_sizes.values())
        batch_capture_strata = Counter(batch_stratum(size) for size in batch_values)
        batch_median = None
        if batch_values:
            mid = len(batch_values) // 2
            if len(batch_values) % 2:
                batch_median = float(batch_values[mid])
            else:
                batch_median = (batch_values[mid - 1] + batch_values[mid]) / 2.0

        confirmation_facts: dict[tuple[int, str], sqlite3.Row] = {}
        for row in con.execute(
            """SELECT sf.*, c.response_received_at AS capture_received_at
               FROM sporttery_facts sf
               JOIN captures c ON c.capture_id=sf.capture_id
               WHERE c.capture_kind='change_confirmation'
                 AND c.source='official_sporttery'
                 AND c.failure_class IS NULL"""
        ):
            confirmation_facts[(int(row["capture_id"]), row["match_id"])] = row

        candidates: list[dict[str, Any]] = []
        rows_total = 0
        unlinked_rows = 0
        matched_rows = 0
        analyzable = 0
        stale_rows = 0
        executable_rows = 0
        primary_rows = 0
        primary_fixture_ids: set[str] = set()
        matched_fixture_ids: set[str] = set()
        changed_event_ids: set[str] = set()
        changed_days: set[str] = set()
        primary_days: set[str] = set()
        variant_counts: Counter[str] = Counter()
        threshold_fixtures: dict[str, set[str]] = {
            ">0": set(),
            ">=0.02": set(),
            ">=0.05": set(),
            ">=0.10": set(),
        }
        threshold_rows: Counter[str] = Counter()
        threshold_quality_rows: dict[str, Counter[str]] = {
            label: Counter() for label in threshold_fixtures
        }
        threshold_quality_fixtures: dict[str, dict[str, set[str]]] = {
            label: {"batch_1": set(), "batch_le_5": set()}
            for label in threshold_fixtures
        }
        batch_change_rows: Counter[str] = Counter()
        primary_batch_rows: Counter[str] = Counter()
        ref_persistence: Counter[str] = Counter()
        primary_ref_persistence: Counter[str] = Counter()

        for change in con.execute("SELECT * FROM reference_changes ORDER BY change_id"):
            rows_total += 1
            event_id = change["event_id"]
            changed_event_ids.add(event_id)
            variant_counts[str(change["source_variant"] or "<none>")] += 1

            curr_time = parse_time(change["current_response_received_at"])
            prev_time = parse_time(change["previous_response_received_at"])
            if curr_time is not None:
                changed_days.add(curr_time.date().isoformat())

            confirmation_id = change["confirmation_capture_id"]
            if confirmation_id is None:
                unlinked_rows += 1
                continue
            batch_size = batch_sizes.get(int(confirmation_id), 0)
            if batch_size < 1:
                unlinked_rows += 1
                continue
            stratum = batch_stratum(batch_size)
            batch_change_rows[stratum] += 1

            match_id = crosswalk.get(event_id)
            if match_id is None:
                continue
            matched_rows += 1
            matched_fixture_ids.add(match_id)
            if prev_time is None or curr_time is None:
                continue

            previous_tuple = parse_tuple(change["previous_tuple"])
            current_tuple = parse_tuple(change["current_tuple"])
            ref_state = _reference_persistence(
                con,
                event_id=event_id,
                variant=change["source_variant"],
                current_time=curr_time,
                previous_tuple=previous_tuple,
                current_tuple=current_tuple,
            )
            ref_persistence[ref_state] += 1

            baseline = None
            for row in sport_by_match.get(match_id, []):
                observed = parse_time(row["capture_received_at"])
                if (
                    observed is not None
                    and observed <= prev_time
                    and row["capture_kind"] == "regular"
                ):
                    baseline = row
                elif observed is not None and observed > prev_time:
                    break

            confirmation = confirmation_facts.get((int(confirmation_id), match_id))
            if baseline is None or confirmation is None:
                continue
            confirm_time = parse_time(confirmation["capture_received_at"])
            if confirm_time is None or confirm_time < curr_time:
                continue

            baseline_odds = _had_tuple(baseline)
            confirm_odds = _had_tuple(confirmation)
            stale = observed_stale(
                baseline_odds,
                baseline["provider_had_updated_at"],
                confirm_odds,
                confirmation["provider_had_updated_at"],
            )
            exec_state = executable_had(
                pool_status=confirmation["had_pool_status"],
                betting_single=confirmation["had_betting_single"],
                betting_allup=confirmation["had_betting_allup"],
                close_date=confirmation["had_close_date"],
                close_time=confirmation["had_close_time"],
                observed_at=confirm_time,
            )
            analyzable += 1
            if stale is True:
                stale_rows += 1
            if exec_state is True:
                executable_rows += 1
            if stale is not True or exec_state is not True or confirm_odds is None:
                continue

            primary_rows += 1
            primary_fixture_ids.add(match_id)
            primary_days.add(curr_time.date().isoformat())
            primary_batch_rows[stratum] += 1
            primary_ref_persistence[ref_state] += 1

            observations = sport_by_match.get(match_id, [])
            kickoff = (
                parse_time(observations[0]["kickoff_local"]) if observations else None
            )
            persistence_s, persistence_status = _persistence_seconds(
                observations,
                start=curr_time,
                baseline_odds=confirm_odds,
                provider_time=confirmation["provider_had_updated_at"],
                kickoff=kickoff,
                dataset_end=dataset_end,
            )
            metrics = proxy_metrics(previous_tuple, current_tuple, confirm_odds)
            max_ev = max(
                (float(metric["proxy_implied_ev"]) for metric in metrics),
                default=None,
            )
            predicates = {
                ">0": lambda x: x > 0,
                ">=0.02": lambda x: x >= 0.02,
                ">=0.05": lambda x: x >= 0.05,
                ">=0.10": lambda x: x >= 0.10,
            }
            for label, predicate in predicates.items():
                if not any(
                    predicate(float(metric["proxy_implied_ev"])) for metric in metrics
                ):
                    continue
                threshold_rows[label] += 1
                threshold_fixtures[label].add(match_id)
                if batch_size == 1:
                    threshold_quality_rows[label]["batch_1"] += 1
                    threshold_quality_fixtures[label]["batch_1"].add(match_id)
                if batch_size <= 5:
                    threshold_quality_rows[label]["batch_le_5"] += 1
                    threshold_quality_fixtures[label]["batch_le_5"].add(match_id)

            candidates.append(
                {
                    "change_id": int(change["change_id"]),
                    "event_id": event_id,
                    "match_id": match_id,
                    "source_variant": change["source_variant"],
                    "change_interval_lower": change["change_interval_lower"],
                    "change_interval_upper": change["change_interval_upper"],
                    "change_interval_seconds": (curr_time - prev_time).total_seconds(),
                    "confirmation_capture_id": int(confirmation_id),
                    "confirmation_delay_seconds": (confirm_time - curr_time).total_seconds(),
                    "batch_size": batch_size,
                    "batch_stratum": stratum,
                    "reference_persistence": ref_state,
                    "previous_reference_odds": json.dumps(previous_tuple),
                    "current_reference_odds": json.dumps(current_tuple),
                    "baseline_had": json.dumps(baseline_odds),
                    "confirmation_had": json.dumps(confirm_odds),
                    "provider_had_updated_at": confirmation["provider_had_updated_at"],
                    "confirmation_received_at": confirmation["capture_received_at"],
                    "had_pool_status": confirmation["had_pool_status"],
                    "had_betting_single": confirmation["had_betting_single"],
                    "had_betting_allup": confirmation["had_betting_allup"],
                    "max_proxy_implied_ev": max_ev,
                    "metrics_json": json.dumps(metrics, sort_keys=True),
                    "persistence_seconds": persistence_s,
                    "persistence_status": persistence_status,
                }
            )

        fieldnames = list(candidates[0]) if candidates else [
            "change_id",
            "event_id",
            "match_id",
            "max_proxy_implied_ev",
        ]
        with (out / "candidates.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates)

        summary: dict[str, Any] = {
            "identity": asdict(identity),
            "reference_change_rows": rows_total,
            "unlinked_reference_change_rows": unlinked_rows,
            "distinct_changed_event_ids": len(changed_event_ids),
            "distinct_changed_calendar_days": len(changed_days),
            "reference_change_source_variants": dict(sorted(variant_counts.items())),
            "matched_change_rows": matched_rows,
            "distinct_matched_sporttery_matches": len(matched_fixture_ids),
            "analyzable_change_rows": analyzable,
            "observed_stale_rows": stale_rows,
            "executable_rows": executable_rows,
            "primary_candidate_rows": primary_rows,
            "primary_candidate_fixtures": len(primary_fixture_ids),
            "primary_candidate_calendar_days": len(primary_days),
            "batch_size_summary": {
                "confirmation_captures": len(batch_values),
                "min": min(batch_values) if batch_values else None,
                "median": batch_median,
                "max": max(batch_values) if batch_values else None,
                "confirmation_capture_strata": dict(sorted(batch_capture_strata.items())),
            },
            "batch_strata_change_rows": dict(sorted(batch_change_rows.items())),
            "primary_candidate_batch_strata": dict(sorted(primary_batch_rows.items())),
            "reference_persistence": dict(sorted(ref_persistence.items())),
            "primary_reference_persistence": dict(
                sorted(primary_ref_persistence.items())
            ),
            "proxy_ev_threshold_rows": dict(threshold_rows),
            "proxy_ev_threshold_distinct_fixtures": {
                key: len(value) for key, value in threshold_fixtures.items()
            },
            "proxy_ev_threshold_quality_rows": {
                label: dict(counter)
                for label, counter in threshold_quality_rows.items()
            },
            "proxy_ev_threshold_quality_distinct_fixtures": {
                label: {
                    quality: len(fixtures)
                    for quality, fixtures in quality_map.items()
                }
                for label, quality_map in threshold_quality_fixtures.items()
            },
        }
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TASK-0007 D01-B prospective analysis")
    parser.add_argument("--db", required=True)
    parser.add_argument("--team-map", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--identity-only", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = analyze(
        args.db,
        args.team_map,
        args.output_dir,
        identity_only=args.identity_only,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
