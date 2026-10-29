"""TASK0043: real official capture -> verified prior-team identity -> independent 1X2 freeze.

No score, bookmaker price, result source, quote candidate or BUY input enters
the model. The July 2026 historical snapshot is already published BEFORE the
October 2026 target fixtures; it is stale and research-only.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import math
import sqlite3
from pathlib import Path

from tools.phase2_forecast_lab import _create_only
from tools.phase3_multimodel_walkforward import (
    State, Scheduled, deduplicate, read_source,
)
from tools.task0038_teams import HF_TEAM_BRIDGE
from tools.task0017_official_only import ENDPOINT

UTC = dt.timezone.utc
BJT = dt.timezone(dt.timedelta(hours=8))
HISTORY_AVAILABLE_AT = dt.datetime(2026, 7, 5, 1, 23, 18, tzinfo=UTC)
HISTORY_LAST_EXCLUSIVE = dt.date(2026, 7, 5)
MAX_CAPTURE_AGE = dt.timedelta(hours=6)
EXPECTED_HISTORY_MANIFEST = "eb3c37793866a27f8c1520c78a69e6098fdf79f08622b37fed64070fa1f8748f"
EXPECTED_BRIDGE_SHA = "13d373dbab8363e606cfaf39c478b6035c35c86ad0ffcbf4c53e6e5014f63f2f"
ELIGIBLE_LEAGUES = {
    "挪超": (23, "Eliteserien", "Norway"),
    "法甲": (9, "Ligue 1", "France"),
}
EXPECTED_HISTORY_ROWS = 53705


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _aware(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("naive event timestamp")
    return parsed.astimezone(UTC)


def load_capture(root: Path, now: dt.datetime) -> tuple[list[dict], dict]:
    """Require a genuine exactly-one-round immutable official capture."""
    root = root.resolve()
    cfg = json.loads((root / "CONFIG.json").read_text(encoding="utf-8"))
    if (cfg.get("mode") != "QUALIFICATION_OFFICIAL_ONLY"
            or cfg.get("url") != ENDPOINT or cfg.get("max_rounds") != 1
            or not isinstance(cfg.get("source_commit"), str)
            or len(cfg["source_commit"]) != 40
            or any(c not in "0123456789abcdef" for c in cfg["source_commit"].lower())):
        raise ValueError("capture configuration/provenance not accepted")
    conn = sqlite3.connect((root / "official.sqlite3").resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("source SQLite invalid")
        rows = conn.execute("""SELECT capture_id,observed_at_utc,request_url,http_status,
                                   result,match_count,raw_sha256,raw_path,raw_length,
                                   source_commit FROM captures""").fetchall()
    finally:
        conn.close()
    if len(rows) != 1:
        raise ValueError("require exactly one source observation")
    cid, stamp, url, http, status, total, sha, relative, size, commit = rows[0]
    received = _aware(stamp)
    if (cid != 1 or url != ENDPOINT or http != 200 or status != "ok"
            or commit != cfg["source_commit"] or not isinstance(total, int)
            or total < 1 or not isinstance(relative, str)
            or not relative.startswith("raw/") or not relative.endswith(".json.gz")
            or not isinstance(sha, str) or len(sha) != 64
            or not isinstance(size, int) or size <= 0
            or not _aware(cfg["created_at_utc"]) <= received):
        raise ValueError("invalid source observation metadata")
    if not received <= now or now - received > MAX_CAPTURE_AGE:
        raise ValueError("capture future-dated or stale for new freeze")
    rawfile = (root / relative).resolve()
    if not rawfile.is_relative_to(root) or not rawfile.is_file():
        raise ValueError("raw capture path unsafe")
    raw = gzip.open(rawfile, "rb").read()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError("official raw SHA/byte mismatch")
    doc = json.loads(raw)
    if (doc.get("success") is not True or doc.get("errorCode") not in (0, "0", None)
            or not isinstance(doc.get("value"), dict)
            or not isinstance(doc["value"].get("matchInfoList"), list)):
        raise ValueError("invalid official response")
    matches = []
    for group in doc["value"]["matchInfoList"]:
        if not isinstance(group, dict) or not isinstance(group.get("subMatchList"), list):
            raise ValueError("invalid official fixture group")
        matches.extend(group["subMatchList"])
    ids = [str(m["matchId"]) for m in matches]
    if len(matches) != total or len(set(ids)) != total:
        raise ValueError("source match count/identity conflict")
    return matches, {
        "capture_id": cid, "received_utc": received.isoformat(), "sha256": sha,
        "capture_source_commit": commit, "fixture_count": total,
    }


def frozen_team_bridge(path: Path) -> tuple[dict[str, tuple[int, str]], str]:
    sha = _hash(path)
    if sha != EXPECTED_BRIDGE_SHA:
        raise ValueError("previously approved identity ledger changed")
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if ledger.get("new_unique_cup_identity") != 35 or len(ledger.get("accepted", [])) != 35:
        raise ValueError("unexpected approved cross-provider identity cohort")
    mapping = {}
    used = {}
    for z in ledger["accepted"]:
        for side, index in (("home", 0), ("away", 1)):
            official_id = str(z[f"official_{side}_id"])
            approved_name = z["ESPN_names"][index]
            hf = HF_TEAM_BRIDGE[approved_name]
            record = (int(hf["id"]), z["original_zh"][index])
            if official_id in mapping and mapping[official_id] != record:
                raise ValueError("ambiguous official to HF identity")
            if record[0] in used and used[record[0]] != official_id:
                raise ValueError("two official teams mapped to one HF team")
            used[record[0]] = official_id
            mapping[official_id] = record
    return mapping, sha


def qualify_fixtures(matches: list[dict], crosswalk: dict,
                     now: dt.datetime) -> tuple[list[dict], dict[str, int]]:
    allowed = []
    excluded = collections.Counter()
    for row in matches:
        kickoff = dt.datetime.fromisoformat(
            str(row["matchDate"]) + "T" + str(row["matchTime"])
        ).replace(tzinfo=BJT).astimezone(UTC)
        if now >= kickoff:
            excluded["not_future_at_freeze"] += 1
            continue
        league_name = str(row.get("leagueAbbName"))
        if league_name not in ELIGIBLE_LEAGUES:
            excluded["league_not_approved_for_forward_model"] += 1
            continue
        hid, aid = str(row.get("homeTeamId")), str(row.get("awayTeamId"))
        if hid == aid or hid not in crosswalk or aid not in crosswalk:
            excluded["missing_preapproved_both_team_identity"] += 1
            continue
        home, hname = crosswalk[hid]
        away, aname = crosswalk[aid]
        if (home == away or str(row.get("homeTeamAllName")) != hname
                or str(row.get("awayTeamAllName")) != aname):
            excluded["approved_team_name_conflict"] += 1
            continue
        allowed.append({
            "matchId": str(row["matchId"]), "league": league_name,
            "kickoff_utc": kickoff.isoformat(),
            "official_home_id": hid, "official_away_id": aid,
            "hf_home_id": home, "hf_away_id": away,
            "hf_league_id": ELIGIBLE_LEAGUES[league_name][0],
        })
    return allowed, dict(sorted(excluded.items()))


def load_historical_state(history: Path, now: dt.datetime) -> tuple[State, dict]:
    if now <= HISTORY_AVAILABLE_AT:
        raise ValueError("future historical source publication")
    if _hash(history / "hf_manifest.json") != EXPECTED_HISTORY_MANIFEST:
        raise ValueError("historical manifest changed")
    meta = json.loads((history / "HUGGINGFACE_DATASET_METADATA.json").read_text(encoding="utf-8"))
    if (meta.get("id") != "eatpizzanot/soccer-dataset"
            or _aware(meta["lastModified"]) != HISTORY_AVAILABLE_AT):
        raise ValueError("source publisher time changed")
    import duckdb
    conn = duckdb.connect()
    try:
        leagues = conn.execute("SELECT id,name,country FROM read_parquet(?)",
                               [str(history / "leagues.parquet")]).fetchall()
        present = set(leagues)
        if any(tuple(item) not in present for item in ELIGIBLE_LEAGUES.values()):
            raise ValueError("approved league identity changed")
        teams = dict(conn.execute("SELECT id,name FROM read_parquet(?)",
                                  [str(history / "teams.parquet")]).fetchall())
        for z in HF_TEAM_BRIDGE.values():
            if teams.get(z["id"]) != z["hf_name"]:
                raise ValueError("historic source team ID/name contradiction")
    finally:
        conn.close()
    games, sources = read_source(history)  # rechecks all frozen manifest source hashes
    games, duplicates = deduplicate(games)
    if len(games) != EXPECTED_HISTORY_ROWS:
        raise ValueError("previously frozen historical corpus changed")
    if any(g.date >= HISTORY_LAST_EXCLUSIVE for g in games):
        raise ValueError("history contains future match")
    state = State()
    for g in games:
        state.add_training(g)
    return state, {**sources, "training_matches": len(games),
                   "deduped_identical": duplicates,
                   "last_training_date": state.last_training_date.isoformat()}


def model_fixtures(qualified: list[dict], state: State) -> tuple[list[dict], dict]:
    accepted = []
    excluded = collections.Counter()
    for row in qualified:
        prediction = state.predict(Scheduled(
            row["hf_league_id"], row["hf_home_id"], row["hf_away_id"]))
        if "pooled_elo_davidson" not in prediction:
            excluded["elo_prior_or_connection_missing"] += 1
            continue
        if "league_poisson" not in prediction:
            excluded["poisson_position_history_missing"] += 1
            continue
        for p in prediction.values():
            if len(p) != 3 or any(not math.isfinite(v) or v <= 0 for v in p) or abs(sum(p)-1) > 1e-9:
                raise ValueError("invalid independent probabilities")
        accepted.append({**row, "models_1x2_home_draw_away": prediction})
    return accepted, dict(sorted(excluded.items()))


def build(*, capture: Path, identity: Path, history: Path,
          now: dt.datetime | None = None) -> dict:
    now = (now or dt.datetime.now(UTC))
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("freeze time requires timezone")
    now = now.astimezone(UTC)
    if now <= HISTORY_AVAILABLE_AT:
        raise ValueError("historical snapshot not published as-of freeze")
    matches, capture_meta = load_capture(capture, now)
    mapping, identity_sha = frozen_team_bridge(identity)
    qualified, rejected = qualify_fixtures(matches, mapping, now)
    state, history_meta = load_historical_state(history, now)
    accepted, model_rejected = model_fixtures(qualified, state)
    return {
        "task": "TASK0043", "phase": "REAL_PROSPECTIVE_RESEARCH_FREEZE",
        "frozen_at_utc": now.isoformat(), "capture": capture_meta,
        "identity_ledger_sha256": identity_sha,
        "history": {**history_meta, "history_manifest_sha256": EXPECTED_HISTORY_MANIFEST,
                    "published_at_utc": HISTORY_AVAILABLE_AT.isoformat()},
        "total_observed_fixtures": len(matches),
        "crosswalk_qualified": len(qualified), "model_qualified": len(accepted),
        "identity_or_league_rejections": rejected,
        "model_rejections": model_rejected,
        "predictions": accepted, "market_prices_input_to_models": False,
        "new_results_input_to_models": False, "no_bet_or_buy": True,
        "not_realtime_trading_eligible": True,
        "limitations": [
            "Frozen historic training source was published in July 2026, 4 months before predictions; staleness is not corrected.",
            "Only previously verified 35-cup-match identity ledger and two exact leagues eligible.",
            "Odds, result and CLV are not inputs or validated by this forecast.",
            "Local UTC system clock is not an independent timestamp authority; pre-kickoff Git commit required.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture", required=True, type=Path)
    ap.add_argument("--identity", required=True, type=Path)
    ap.add_argument("--history", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    output = args.out.resolve()
    for source in (args.capture, args.identity, args.history):
        if output.is_relative_to(source.resolve()):
            ap.error("cannot write into a source evidence directory")
    result = build(capture=args.capture, identity=args.identity, history=args.history)
    if not result["model_qualified"]:
        raise SystemExit("NO-GO: no eligible Poisson/Elo prospects; no freeze fabricated")
    digest = _create_only(output, result)
    print(json.dumps({"status":"FROZEN_CREATE_ONLY", "sha256":digest,
                      "frozen_at_utc":result["frozen_at_utc"],
                      "source_raw_sha256":result["capture"]["sha256"],
                      "observed":result["total_observed_fixtures"],
                      "qualified":result["model_qualified"],
                      "rejected":result["identity_or_league_rejections"],
                      "model_rejected":result["model_rejections"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
