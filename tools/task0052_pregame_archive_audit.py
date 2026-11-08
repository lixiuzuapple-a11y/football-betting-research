"""TASK0052: archival-before-kickoff hash checks of TASK0051's frozen cohort.

This improves evidence but DOES NOT prove independent PIT bookmaker odds.
The snapshot's generated_at is publisher-controlled; archived rows reveal a
prediction pick probability/hash, not the entire book's opening 1X2 vector.
OpenTimestamps Bitcoin attestations are not verified by this utility.

Only permitted off-Git archive data is read; never fetches or places bets.
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

from tools.task0051_market_overlap_audit import (
    associate, daily_paired_bootstrap, load_historical_index, sha256,
)

FIXED_TASK0051_DETAILS_SHA = "7642d1af855de118d2a3e6323020b8e6187ed1d17dbcc095b29350a4c9d30e46"
FIXED_TASK0051_MARKET_SHA = "cfdec6a9559137f52e39822855fc963f55c4a9810736f258ec258752ae9f0883"
PINNED_PROVIDER_REPOSITORY = "tipsaudit/track-record-public"
PINNED_PROVIDER_COMMIT = "a2d6290bd36029b82a36bd749417c0e27222b8e7"
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
HEX16 = re.compile(r"[a-f0-9]{16}\Z")
UTC = dt.timezone.utc


def as_utc(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("snapshot and kickoff must have UTC-aware datetimes")
    return parsed.astimezone(UTC)


def row_matches_archived_identity(market: dict, archived: dict) -> bool:
    """Exact historical provider IDs and pre-match fixture fields; no fuzzy links."""
    return (str(archived.get("id")) == str(market.get("id"))
            and archived.get("kickoff_utc") == market.get("kickoff_utc")
            and archived.get("home") == market.get("home")
            and archived.get("away") == market.get("away")
            and HEX16.fullmatch(str(archived.get("hash", ""))) is not None
            and HEX16.fullmatch(str(market.get("record_hash", ""))) is not None)


def discover_archives(manifest: Path, raw_root: Path, *, manifest_sha: str) -> list[dict]:
    if not HEX64.fullmatch(manifest_sha.lower()) or sha256(manifest) != manifest_sha.lower():
        raise ValueError("provider manifest SHA differs from pinned raw evidence")
    reports = []
    seen = set()
    with manifest.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            when_text = row.get("snapshot_utc", "")
            if not (when_text[:7] == "2026-06" and
                    when_text[8:10].isdigit() and int(when_text[8:10]) >= 20):
                continue
            rel = row.get("ots", "")
            if not rel.startswith("data/track-") or not rel.endswith(".json.ots"):
                raise ValueError("unsafe archive path in provider manifest")
            name = rel[len("data/"):-len(".ots")]
            if name in seen or "/" in name or "\\" in name or ".." in name:
                raise ValueError("duplicate/unsafe archive filename")
            seen.add(name)
            path = raw_root / name
            expected_sha = row.get("sha256", "").lower()
            if not HEX64.fullmatch(expected_sha) or sha256(path) != expected_sha:
                raise ValueError("provider original archive SHA mismatch")
            document = json.loads(path.read_text(encoding="utf-8"))
            generated = as_utc(document["generated_at"])
            if generated.date().isoformat() != when_text[:10]:
                raise ValueError("archive internal generation day differs from filename/manifest")
            observations = document["predictions"]
            if not isinstance(observations, list) or len(observations) != document["count"]:
                raise ValueError("archived prediction count invalid")
            by_id = {}
            for item in observations:
                key = str(item.get("id"))
                if key in by_id:
                    raise ValueError("duplicate predictor id within an archive")
                by_id[key] = item
            reports.append({"generated_at": generated,
                            "archive_name": name,
                            "sha256": expected_sha, "by_id": by_id})
    if not reports:
        raise ValueError("no archived snapshot in required overlap")
    reports.sort(key=lambda r: (r["generated_at"], r["archive_name"]))
    return reports


def classify(market: dict, archives: list[dict]) -> tuple[str, dict | None]:
    """Choose EARLIEST pre-kickoff observation; never search for a matching hash.

    Later pre-match snapshots cannot rescue a conflicting earliest archive.
    """
    kickoff = as_utc(market["kickoff_utc"])
    earlier = [r for r in archives if r["generated_at"] < kickoff]
    if not earlier:
        return "NO_SNAPSHOT_BEFORE_KICKOFF", None
    candidates = []
    for report in earlier:
        value = report["by_id"].get(str(market["id"]))
        if value is not None:
            candidates.append((report, value))
    if not candidates:
        return "ROW_ABSENT_FROM_PREMATCH_ARCHIVES", None
    report, original = candidates[0]
    if not row_matches_archived_identity(market, original):
        return "ARCHIVED_FIXTURE_IDENTITY_OR_HASH_INVALID", None
    if original["hash"] != market["record_hash"]:
        return "ARCHIVED_HASH_CHANGED_IN_LATER_CSV", {
            "archive_name": report["archive_name"],
            "generated_at": report["generated_at"].isoformat(),
            "initial_hash": original["hash"],
            "later_hash": market["record_hash"],
        }
    return "PREMATCH_ARCHIVE_ROW_HASH_EQUAL", {
        "archive_name": report["archive_name"],
        "generated_at": report["generated_at"].isoformat(),
        "initial_hash": original["hash"],
    }


def run(*, manifest: Path, archive_root: Path, manifest_sha: str, market_csv: Path,
        task0051_details: Path, history: Path) -> tuple[dict, list[dict]]:
    if sha256(market_csv) != FIXED_TASK0051_MARKET_SHA:
        raise ValueError("wrong historical market CSV; no silent rebuild")
    if sha256(task0051_details) != FIXED_TASK0051_DETAILS_SHA:
        raise ValueError("wrong historical 175-fixture scoring evidence")
    archive = discover_archives(manifest, archive_root, manifest_sha=manifest_sha)
    original = json.loads(task0051_details.read_text(encoding="utf-8"))
    if len(original) != 175 or len({x["match_id"] for x in original}) != 175:
        raise ValueError("original qualified cohort changed or duplicated")
    cohort = {int(x["match_id"]): x for x in original}
    index = load_historical_index(history)
    summary_counts = collections.Counter()
    records = []
    seen = set()
    with market_csv.open(encoding="utf-8-sig", newline="") as fh:
        for market in csv.DictReader(fh):
            fixture, status = associate(market, index)
            if fixture is None:
                continue
            match_id = fixture["match_id"]
            if match_id not in cohort:
                continue
            if match_id in seen:
                raise ValueError("duplicate market result for original fixture")
            seen.add(match_id)
            reason, snapshot = classify(market, archive)
            summary_counts[reason] += 1
            record = {"match_id": match_id, "market_id": str(market["id"]),
                      "date": cohort[match_id]["date"], "classification": reason,
                      "source_evidence": snapshot}
            if reason == "PREMATCH_ARCHIVE_ROW_HASH_EQUAL":
                record["market_logloss"] = cohort[match_id]["metrics"]["market_open"][0]
                record["poisson_logloss"] = cohort[match_id]["metrics"]["league_poisson"][0]
                record["market_brier3"] = cohort[match_id]["metrics"]["market_open"][1]
                record["poisson_brier3"] = cohort[match_id]["metrics"]["league_poisson"][1]
            records.append(record)
    if seen != set(cohort):
        raise ValueError("the input markets do not reproduce all 175 baseline fixtures")
    valid = [x for x in records if x["classification"] == "PREMATCH_ARCHIVE_ROW_HASH_EQUAL"]
    summary = {
        "task": "TASK0052",
        "verdict": "ARCHIVE_MATCH_QUALIFIED_BUT_INDEPENDENT_PIT_ODDS_UNVERIFIED",
        "reference_provider": PINNED_PROVIDER_REPOSITORY,
        "provider_commit": PINNED_PROVIDER_COMMIT,
        "provider_manifest_sha256": sha256(manifest),
        "original_task0051_details_sha256": sha256(task0051_details),
        "original_market_sha256": sha256(market_csv),
        "archive_count": len(archive),
        "source_archives": [{"file": r["archive_name"], "sha256": r["sha256"],
                             "publisher_generated_utc": r["generated_at"].isoformat()}
                            for r in archive],
        "original_cohort": len(cohort),
        "classification_counts": dict(sorted(summary_counts.items())),
        "pre_kickoff_hash_equal_subset": {
            "n": len(valid),
            "days": len({x["date"] for x in valid}),
            "market_logloss": sum(x["market_logloss"] for x in valid)/len(valid) if valid else None,
            "poisson_logloss": sum(x["poisson_logloss"] for x in valid)/len(valid) if valid else None,
            "market_brier3": sum(x["market_brier3"] for x in valid)/len(valid) if valid else None,
            "poisson_brier3": sum(x["poisson_brier3"] for x in valid)/len(valid) if valid else None,
            "bootstrap_delta_market_minus_poisson": daily_paired_bootstrap(valid) if valid else None,
        },
        "limits": [
            "Provider archive generated_at is provider-controlled, not independent trusted timestamp.",
            "OpenTimestamps .ots blockchain attestation was not validated by this code.",
            "Archive row contains pick/probability/hash but NOT entire three-way bookmaker odds vector.",
            "The later CSV record_hash is publisher-defined, not independent proof of all 1X2 quotes.",
            "Historical Phase3 model itself is retrospectively derived, not timestamp-certified live prediction.",
            "Hash-matched games are selected subset and cannot be compared as a random representative sample.",
            "No CLV, bookmaker executable price, betting EV, independent PIT or ROI claims."
        ],
    }
    return summary, records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", type=str, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--market-csv", type=Path, required=True)
    parser.add_argument("--task0051-details", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--out-summary", type=Path, required=True)
    parser.add_argument("--out-details", type=Path, required=True)
    args = parser.parse_args()
    if args.out_summary.exists() or args.out_details.exists():
        parser.error("create-only outputs: existing evidence must never be overwritten")
    summary, records = run(
        manifest=args.manifest, archive_root=args.archive_root,
        manifest_sha=args.manifest_sha256, market_csv=args.market_csv,
        task0051_details=args.task0051_details, history=args.history,
    )
    for path, data in ((args.out_summary, summary),(args.out_details, records)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
