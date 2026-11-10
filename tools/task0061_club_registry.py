"""Build an as-of, expandable 14-league EV-Lab identity and review registry.

The HF historical team ID is a *local source key*, not a universal real-world
club ID. Original SHA-pinned 143 official IDs are the only production-approved
cross-platform links. All other HF rows are candidates, NEVER auto-promoted.
Results, bookmaker prices and current-team season assumptions are not read.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from tools.task0043_prospective_multimodel_freeze import (
    ELIGIBLE_LEAGUES, EXPECTED_BRIDGE_SHA, EXPECTED_HISTORY_MANIFEST,
    frozen_team_bridge, verified_extended_team_bridge,
)

SOURCE_URL = "https://huggingface.co/datasets/v-eatpizzanot/soccer-dataset"
TRAINING_END_EXCLUSIVE = "2026-07-05"
TYPE_MARKER = re.compile(
    r"(?:^|[\s_.-])(?:u(?:17|18|19|20|21|23)|ii|b|reserves?|women|ladies|feminin[aoe]|女子|女足)(?:$|[\s_.-])",
    re.I,
)
MASTER_COLS = (
    "canonical_team_id", "hf_team_id", "hf_name", "hf_fd_name",
    "hf_api_football_id", "official_team_id", "official_name_zh",
    "mapping_status", "mapping_version", "identity_evidence_sha256",
    "identity_evidence_witness_count", "wikidata_qid_unverified",
    "team_type_from_source_name", "team_type_review_status",
    "historical_approved_league_count", "historic_league_ids",
    "training_source", "frozen_history_manifest_sha256",
)
MEMBER_COLS = (
    "league_zh", "league_hf_id", "league_hf_name", "league_country",
    "canonical_team_id", "hf_team_id", "hf_name", "hf_fd_name",
    "hf_api_football_id", "official_team_id", "official_name_zh",
    "mapping_status", "team_type_from_source_name",
    "historic_completed_league_matches", "last_historical_kickoff_utc",
    "asof_training_end_exclusive_utc", "identity_evidence_sha256",
    "training_source",
)
ALIAS_COLS = (
    "canonical_team_id", "source_system", "source_field",
    "exact_raw_alias", "alias_approval_status", "candidate_hf_id",
    "potential_collision_count", "source_url", "review_reason",
)
SUMMARY_COLS = (
    "league_zh", "league_hf_id", "league_hf_name", "country",
    "historical_unique_hf_clubs", "already_official_verified_clubs",
    "hf_only_unverified_clubs", "historical_completed_matches",
    "asof_training_end_exclusive_utc", "scope_note",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, cols: tuple, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as dest:
        out = csv.DictWriter(dest, fieldnames=cols, extrasaction="raise",
                             lineterminator="\n")
        out.writeheader()
        for row in rows:
            out.writerow(row)


def build(history: Path, identity: Path, extension: Path):
    import duckdb

    if sha256(history / "hf_manifest.json") != EXPECTED_HISTORY_MANIFEST:
        raise ValueError("HF manifest SHA mismatch")
    manifest = json.loads((history / "hf_manifest.json").read_text(encoding="utf-8"))
    for row in manifest:
        if sha256(history / row["file"]) != row["sha256"]:
            raise ValueError("HF parquet source SHA mismatch")
    old, old_sha = frozen_team_bridge(identity)
    mapping, meta = verified_extended_team_bridge(identity, extension)
    if old_sha != EXPECTED_BRIDGE_SHA or len(old) != 70 or len(mapping) != 143:
        raise ValueError("published identity baseline changed")
    incremental = json.loads(extension.read_text(encoding="utf-8"))
    new_by_id = {str(z["official_id"]): z for z in incremental["additions"]}
    approved_by_hf = {}
    for official, (hid, zh) in mapping.items():
        if int(hid) in approved_by_hf:
            raise ValueError("one HF team assigned multiple official IDs")
        approved_by_hf[int(hid)] = {
            "id": official, "zh": zh,
            "version": "TASK0037_ORIGINAL_70" if official in old else
            "TASK0060_ADDITIVE_73",
            "witnesses": len(new_by_id[official]["witnesses"])
            if official in new_by_id else 1,
            "sha": old_sha if official in old else meta["identity_extension_sha256"],
        }

    q = duckdb.connect()
    try:
        leagues = {
            int(id): (name, country)
            for id, name, country in q.execute(
                "SELECT id,name,country FROM read_parquet(?)",
                [str(history / "leagues.parquet")],
            ).fetchall()
        }
        for name, (lid, en, country) in ELIGIBLE_LEAGUES.items():
            if leagues.get(lid) != (en, country):
                raise ValueError("source league ID/name/country differs from exact catalog")
        hf_teams = {
            int(tid): {
                "name": name, "fd_name": fd or "",
                "api_football_id": str(api) if api is not None else "",
            }
            for tid, name, api, fd in q.execute(
                "SELECT id,name,api_football_id,fd_name FROM read_parquet(?)",
                [str(history / "teams.parquet")],
            ).fetchall()
        }
        raw = q.execute(
            "WITH side AS ("
            " SELECT league_id,home_team_id team_id,date_utc FROM read_parquet(?)"
            " WHERE is_played=true AND date_utc<?"
            " UNION ALL "
            " SELECT league_id,away_team_id team_id,date_utc FROM read_parquet(?)"
            " WHERE is_played=true AND date_utc<?"
            ") SELECT league_id,team_id,COUNT(*) n,MAX(date_utc) most_recent "
            "FROM side WHERE league_id IN (1,2,5,7,9,10,11,12,13,14,19,21,23,38)"
            " GROUP BY league_id,team_id ORDER BY league_id,team_id",
            [str(history / "fixtures.parquet"), TRAINING_END_EXCLUSIVE,
             str(history / "fixtures.parquet"), TRAINING_END_EXCLUSIVE],
        ).fetchall()
    finally:
        q.close()

    memberships = collections.defaultdict(list)
    counts = collections.Counter()
    for lid, hid, n, last in raw:
        lid, hid = int(lid), int(hid)
        if hid not in hf_teams or not isinstance(n, int) or n < 1:
            raise ValueError("historic membership without HF club/played match")
        memberships[hid].append((lid, n, last))
        counts[lid] += n
    if len(counts) != 14:
        raise ValueError("not all approved leagues have source historical matches")
    # Approved HF teams not in the historical 14-league cohort still appear
    # in the canonical master, with zero membership rows: NEVER infer league.
    team_ids = sorted(set(memberships) | set(approved_by_hf))
    master, members, aliases, by_lid = [], [], [], collections.defaultdict(list)
    for hid in team_ids:
        data = hf_teams.get(hid)
        if data is None:
            raise ValueError("approved source HF team ID absent from HF teams.parquet")
        approved = approved_by_hf.get(hid)
        team_name = data["name"]
        source_type = ("REVIEW_NON_FIRST_TEAM_MARKER" if TYPE_MARKER.search(team_name)
                       or TYPE_MARKER.search(data["fd_name"])
                       else "SOURCE_TYPE_UNSPECIFIED")
        status = "VERIFIED_PUBLISHED" if approved else "HF_HISTORY_ONLY_UNVERIFIED"
        canonical = f"evlab:hf:{hid}"
        base = {
            "canonical_team_id": canonical, "hf_team_id": hid,
            "hf_name": team_name, "hf_fd_name": data["fd_name"],
            "hf_api_football_id": data["api_football_id"],
            "official_team_id": approved["id"] if approved else "",
            "official_name_zh": approved["zh"] if approved else "",
            "mapping_status": status,
        }
        member_ids = sorted(lid for lid, _, _ in memberships.get(hid, ()))
        master.append({
            **base, "mapping_version": approved["version"] if approved else "",
            "identity_evidence_sha256": approved["sha"] if approved else "",
            "identity_evidence_witness_count": approved["witnesses"] if approved else 0,
            "wikidata_qid_unverified": "",
            "team_type_from_source_name": source_type,
            "team_type_review_status": (
                "PENDING_TEAM_TYPE_REVIEW" if source_type.startswith("REVIEW") else
                "NOT_INDEPENDENTLY_CLASSIFIED"),
            "historical_approved_league_count": len(member_ids),
            "historic_league_ids": ";".join(map(str, member_ids)),
            "training_source": SOURCE_URL,
            "frozen_history_manifest_sha256": EXPECTED_HISTORY_MANIFEST,
        })
        for lid, count, last in memberships.get(hid, []):
            en, country = leagues[lid]
            zh = next(name for name, item in ELIGIBLE_LEAGUES.items()
                      if item[0] == lid)
            member = {
                "league_zh": zh, "league_hf_id": lid,
                "league_hf_name": en, "league_country": country,
                **base, "team_type_from_source_name": source_type,
                "historic_completed_league_matches": count,
                "last_historical_kickoff_utc": last.isoformat() + "Z",
                "asof_training_end_exclusive_utc": TRAINING_END_EXCLUSIVE+"T00:00:00Z",
                "identity_evidence_sha256": approved["sha"] if approved else "",
                "training_source": SOURCE_URL,
            }
            members.append(member)
            by_lid[lid].append(member)
        # HF name and FD name are *source-local* proposals, not verified
        # international bookmaker or Chinese platform alias mappings.
        for field in ("name", "fd_name"):
            rawalias = data[field]
            if rawalias and (field == "name" or rawalias != team_name):
                aliases.append({
                    "canonical_team_id": canonical,
                    "source_system": "frozen_HF_historical",
                    "source_field": field,
                    "exact_raw_alias": rawalias,
                    "alias_approval_status": "SOURCE_ONLY_NOT_CROSS_PROVIDER_APPROVED",
                    "candidate_hf_id": hid,
                    "potential_collision_count": 0,
                    "source_url": SOURCE_URL,
                    "review_reason": "Requires independent stable fixture+home/away+UTC and hard type proof",
                })
    alias_counts = collections.Counter(x["exact_raw_alias"].casefold() for x in aliases)
    for x in aliases:
        x["potential_collision_count"] = alias_counts[x["exact_raw_alias"].casefold()]

    summary = []
    for name, (lid, en, country) in ELIGIBLE_LEAGUES.items():
        count = len(by_lid[lid])
        verified = sum(x["mapping_status"] == "VERIFIED_PUBLISHED"
                       for x in by_lid[lid])
        summary.append({
            "league_zh": name, "league_hf_id": lid,
            "league_hf_name": en, "country": country,
            "historical_unique_hf_clubs": count,
            "already_official_verified_clubs": verified,
            "hf_only_unverified_clubs": count - verified,
            "historical_completed_matches": counts[lid] // 2,
            "asof_training_end_exclusive_utc": TRAINING_END_EXCLUSIVE+"T00:00:00Z",
            "scope_note": "Historical distinct clubs, NOT the 2026/27 active roster",
        })
    if sum(x["historical_unique_hf_clubs"] for x in summary) != len(members):
        raise ValueError("summary and source memberships differ")
    if len({x["canonical_team_id"] for x in master}) != len(master):
        raise ValueError("nonunique canonical keys")
    if sum(bool(x["official_team_id"]) for x in master) != 143:
        raise ValueError("original published 143 official IDs not preserved")
    return {
        "master": master, "members": members, "aliases": aliases, "summary": summary,
        "source_metadata": {
            "task": "TASK0061",
            "scope": "14_LEAGUE_HISTORICAL_CANDIDATES_ONLY_NO_AUTO_APPROVAL",
            "history_manifest_sha256": EXPECTED_HISTORY_MANIFEST,
            "original_bridge_sha256": EXPECTED_BRIDGE_SHA,
            "new_identity_extension_sha256": meta["identity_extension_sha256"],
            "approved_leagues": len(ELIGIBLE_LEAGUES),
            "published_verified_club_keys": 143,
            "master_distinct_hf_keys": len(master),
            "league_membership_rows": len(members),
            "unverified_master_clubs": sum(
                x["mapping_status"] != "VERIFIED_PUBLISHED" for x in master),
            "source_local_alias_rows": len(aliases),
            "never_auto_accept_by_similarity": True,
            "not_current_2026_27_roster": True,
            "no_market_or_result_input": True,
        },
    }


def write_all(data: dict, out_dir: Path):
    files = [
        ("team_master.csv", MASTER_COLS, data["master"]),
        ("league_team_crosswalk.csv", MEMBER_COLS, data["members"]),
        ("alias_candidates.csv", ALIAS_COLS, data["aliases"]),
        ("league_summary.csv", SUMMARY_COLS, data["summary"]),
    ]
    receipts = {}
    for name, cols, rows in files:
        path = out_dir / name
        write_csv(path, cols, rows)
        receipts[name] = {"sha256": sha256(path), "rows": len(rows)}
    manifest = {**data["source_metadata"], "files": receipts}
    with (out_dir / "registry_manifest.json").open("x", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for k in ("history", "identity", "extension", "out-dir"):
        parser.add_argument("--"+k, dest=k.replace("-", "_"),
                            type=Path, required=True)
    opts = parser.parse_args()
    manifest = write_all(
        build(opts.history, opts.identity, opts.extension), opts.out_dir
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
