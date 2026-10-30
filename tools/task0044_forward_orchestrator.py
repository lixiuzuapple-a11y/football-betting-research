"""EV-Lab TASK0044: bounded no-duplicate forward capture/freeze and blind official scoring.

No wagers, no market odds in models, no retroactive prediction creation.
On-demand commands (NOT a deployed scheduler): capture and freeze or fetch
official final scores only after a conservative post-match delay.
Evidence roots are create-only and kept outside Git.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sqlite3
from pathlib import Path

from tools.phase2_forecast_lab import _create_only
from tools.task0017_official_only import run as collector_run
from tools.task0030_official_result_evidence import BASE as RESULT_BASE, get as official_get
from tools.task0043_prospective_multimodel_freeze import build as model_build

UTC = dt.timezone.utc
BJT = dt.timezone(dt.timedelta(hours=8))
MODEL_KEYS = ("global_frequency", "league_frequency",
              "pooled_elo_davidson", "league_poisson")
MIN_SCORE_DELAY_HOURS = 3
MAX_SCORE_PAGES_PER_DATE = 15


def aware(text: str) -> dt.datetime:
    value = dt.datetime.fromisoformat(text)
    if value.utcoffset() is None:
        raise ValueError("source timestamp must have timezone")
    return value.astimezone(UTC)


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_bytes())
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def verified_freeze(frozen: Path, ledger: Path) -> tuple[dict, dict]:
    """Do not permit a silently altered off-repo freeze, forecast or selection."""
    snap, commitment = _read_json(frozen), _read_json(ledger)
    file_sha = hashlib.sha256(frozen.read_bytes()).hexdigest()
    if (commitment.get("task") != "TASK0043"
            or commitment.get("frozen_file_sha256") != file_sha
            or commitment.get("status") != "PRE_KICKOFF_FROZEN_RESEARCH_ONLY"
            or snap.get("task") != "TASK0043"
            or snap.get("frozen_at_utc") != commitment.get("frozen_at_utc")
            or snap.get("capture", {}).get("sha256") != commitment.get("official_raw_sha256")
            or snap.get("market_prices_input_to_models") is not False
            or snap.get("new_results_input_to_models") is not False
            or snap.get("no_bet_or_buy") is not True
            or snap.get("predictions") != commitment.get("predictions")
            or len(snap.get("predictions", [])) != commitment.get("qualified")):
        raise ValueError("freeze/committed forecast provenance mismatch")
    start = aware(snap["frozen_at_utc"])
    if not snap["predictions"]:
        raise ValueError("empty committed freeze")
    seen = set()
    for rec in snap["predictions"]:
        mid = str(rec["matchId"])
        if mid in seen or aware(rec["kickoff_utc"]) <= start:
            raise ValueError("duplicate or retroactively frozen match")
        seen.add(mid)
        models = rec["models_1x2_home_draw_away"]
        if set(models) != set(MODEL_KEYS):
            raise ValueError("not all four independently frozen models present")
        for prob in models.values():
            if (len(prob) != 3 or any(type(x) not in (float, int) or
                    not math.isfinite(x) or x <= 0 for x in prob)
                    or abs(sum(prob) - 1) > 1e-9):
                raise ValueError("invalid committed probability vector")
    return snap, commitment


def capture_and_freeze(*, output_root: Path, identity: Path, history: Path,
                       commit: str, previous_ledgers: list[Path],
                       now: dt.datetime | None = None) -> dict:
    """One bounded capture, then attempt one new model freeze. No repeated match IDs."""
    now = now or dt.datetime.now(UTC)
    if now.utcoffset() is None:
        raise ValueError("clock is timezone-naive")
    output_root = output_root.resolve()
    if output_root.exists():
        raise FileExistsError("refuse to overwrite prior evidence root")
    if output_root.is_relative_to(history.resolve()) or output_root.is_relative_to(identity.resolve().parent):
        raise ValueError("output must not be located within immutable input evidence")
    if (len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit.lower())):
        raise ValueError("actual 40-hex source commit required")
    known_ids = set()
    for path in previous_ledgers:
        ledger = _read_json(path)
        if ledger.get("status") != "PRE_KICKOFF_FROZEN_RESEARCH_ONLY":
            raise ValueError("prior committed ledger untrusted")
        ids = [str(row["matchId"]) for row in ledger["predictions"]]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate prior predictions")
        known_ids.update(ids)
    output_root.mkdir(parents=True)
    raw_root = output_root / "capture"
    code = collector_run(raw_root, max_rounds=1, max_hours=0.1,
                         cadence=60, timeout=20, max_bad=1, commit=commit)
    if code:
        raise RuntimeError("official capture failed; retain raw failure evidence")
    with sqlite3.connect((raw_root / "official.sqlite3").resolve().as_uri() + "?mode=ro",
                         uri=True) as con:
        statuses = con.execute("SELECT result,http_status FROM captures").fetchall()
    if statuses == [("no_offer", 200)]:
        output = {"status": "NORMAL_NO_OFFER_NOT_A_FAILURE",
                  "raw_capture_root": str(raw_root)}
        _create_only(output_root / "NO_OFFER.json", output)
        return output
    if len(statuses) != 1 or statuses[0][0] != "ok":
        raise ValueError("unexpected captured source state")
    candidate = model_build(capture=raw_root, identity=identity, history=history)
    candidates = candidate["predictions"]
    fresh = [row for row in candidates if str(row["matchId"]) not in known_ids]
    skipped = sorted(str(row["matchId"]) for row in candidates if str(row["matchId"]) in known_ids)
    candidate["predictions"] = fresh
    candidate["model_qualified"] = len(fresh)
    candidate["previously_frozen_skipped"] = skipped
    candidate["previous_commitment_sha256"] = sorted(
        hashlib.sha256(p.read_bytes()).hexdigest() for p in previous_ledgers)
    if not fresh:
        status = {"status": "NO_NEW_ELIGIBLE_PREMATCH_FIXTURES",
                  "raw_source_sha256": candidate["capture"]["sha256"],
                  "skipped_previous_ids": skipped,
                  "source_observed": candidate["total_observed_fixtures"]}
        _create_only(output_root / "NO_NEW_FREEZE.json", status)
        return status
    frozen_path = output_root / "NEW_FORECAST_FREEZE.json"
    sha = _create_only(frozen_path, candidate)
    return {"status": "FROZEN_LOCALLY_NOT_GIT_ANCHORED", "sha256": sha,
            "path": str(frozen_path), "new_fixtures": len(fresh),
            "previously_frozen_skipped": skipped,
            "requires_pre_kickoff_git_commit": True}


def score_evidence(*, frozen: dict, raw_pages: list[dict], now: dt.datetime) -> dict:
    """Score only after verified official source pages and complete final statuses."""
    if now.utcoffset() is None:
        raise ValueError("naive scoring clock")
    now = now.astimezone(UTC)
    predictions = frozen["predictions"]
    if now < max(aware(p["kickoff_utc"]) for p in predictions) + dt.timedelta(hours=MIN_SCORE_DELAY_HOURS):
        raise ValueError("post-kickoff final-score delay not satisfied")
    ids = {str(x["matchId"]): x for x in predictions}
    results = {}
    source_hashes = []
    for page in raw_pages:
        payload = page["raw"]
        meta = page["meta"]
        if (meta["http_status"] != 200
                or meta.get("source_url", "").split("?")[0] != RESULT_BASE
                or aware(meta["response_received_utc"]) > now
                or aware(meta["request_started_utc"]) > aware(meta["response_received_utc"])
                or len(payload) != meta["bytes"]
                or hashlib.sha256(payload).hexdigest() != meta["sha256"]):
            raise ValueError("unverified official result response provenance")
        doc = json.loads(payload)
        if (doc.get("success") is not True
                or str(doc.get("errorCode")) != "0"
                or not isinstance(doc.get("value"), dict)
                or not isinstance(doc["value"].get("matchResult"), list)):
            raise ValueError("official result API source invalid")
        source_hashes.append(meta["sha256"])
        for r in doc["value"]["matchResult"]:
            mid = str(r.get("matchId", ""))
            if mid not in ids:
                continue
            if mid in results:
                raise ValueError("duplicate target match result across pages")
            results[mid] = r
    if set(results) != set(ids):
        raise ValueError("missing official target final results")
    matched = []
    for mid, rec in sorted(ids.items()):
        r = results[mid]
        kickoff = aware(rec["kickoff_utc"])
        played_bjt = kickoff.astimezone(BJT).date().isoformat()
        if (str(r.get("matchResultStatus")) != "2"
                or str(r.get("homeTeamId")) != str(rec["official_home_id"])
                or str(r.get("awayTeamId")) != str(rec["official_away_id"])
                or str(r.get("matchDate")) != played_bjt):
            raise ValueError("final status or official fixture identity conflict")
        score = str(r.get("sectionsNo999", ""))
        if not re.fullmatch(r"\d{1,2}:\d{1,2}", score):
            raise ValueError("official final full-time score not verified")
        h, a = (int(x) for x in score.split(":"))
        if h > 25 or a > 25:
            raise ValueError("implausible final full-time score")
        y = 0 if h > a else (2 if h < a else 1)
        matched.append({"matchId": mid, "target": y, "verified_score": [h, a]})
    metric = {}
    for key in MODEL_KEYS:
        ps = [ids[z["matchId"]]["models_1x2_home_draw_away"][key] for z in matched]
        ys = [z["target"] for z in matched]
        n = len(ys)
        metric[key] = {
            "n": n,
            "mean_logloss": sum(-math.log(p[y]) for p, y in zip(ps, ys)) / n,
            "mean_brier3": sum(sum((v - (k == y))**2 for k, v in enumerate(p))
                               for p, y in zip(ps, ys)) / n,
            "accuracy": sum(p.index(max(p)) == y for p, y in zip(ps, ys)) / n,
        }
    return {"task": "TASK0044", "phase": "OFFICIAL_BLIND_SCORE",
            "scored_at_utc": now.isoformat(), "matched": matched,
            "n": len(matched), "model_metrics": metric,
            "raw_result_sha256": source_hashes,
            "no_market_clv_or_profit_claim": True,
            "small_n_no_model_selection": True}


def fetch_and_score(*, frozen_path: Path, ledger_path: Path, out_root: Path,
                    now: dt.datetime | None = None) -> dict:
    """Fetch official results once; preserve source files and reject partial evidence."""
    now = now or dt.datetime.now(UTC)
    frozen, ledger = verified_freeze(frozen_path, ledger_path)
    if now.utcoffset() is None:
        raise ValueError("naive clock")
    cutoff = max(aware(z["kickoff_utc"]) for z in frozen["predictions"]) + dt.timedelta(hours=MIN_SCORE_DELAY_HOURS)
    if now.astimezone(UTC) < cutoff:
        raise ValueError("refuse to fetch/score before last fixture plus three hours")
    out_root = out_root.resolve()
    if out_root.exists():
        raise FileExistsError("refuse to overwrite prior score evidence")
    out_root.mkdir(parents=True)
    days = sorted(set(aware(z["kickoff_utc"]).astimezone(BJT).date().isoformat()
                      for z in frozen["predictions"]))
    raw_pages = []
    for day in days:
        for page in range(1, MAX_SCORE_PAGES_PER_DATE + 1):
            requested = dt.datetime.now(UTC)
            url, raw, status = official_get(day, page)
            received = dt.datetime.now(UTC)
            if status != 200:
                raise ValueError("official result endpoint HTTP non-200")
            filename = f"official-{day}-page-{page}.json"
            path = out_root / filename
            with path.open("xb") as handle:
                handle.write(raw)
            meta = {"source_url": url, "http_status": status,
                    "request_started_utc": requested.isoformat(),
                    "response_received_utc": received.isoformat(),
                    "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                    "file": filename}
            raw_pages.append({"raw": raw, "meta": meta})
            obj = json.loads(raw)
            if obj.get("success") is not True or str(obj.get("errorCode")) != "0":
                raise ValueError("official response not success")
            val = obj.get("value") or {}
            data = val.get("matchResult")
            if not isinstance(data, list):
                raise ValueError("official matchResult schema invalid")
            total = int(val.get("total", -1))
            if total < 0 or total > 1500 or (not data and total):
                raise ValueError("invalid official result pagination total")
            if page * 100 >= total:
                break
        else:
            raise ValueError("official result pagination bound exceeded")
    _create_only(out_root / "SOURCE_MANIFEST.json",
                 {"frozen_sha256": ledger["frozen_file_sha256"],
                  "pages": [item["meta"] for item in raw_pages]})
    result = score_evidence(frozen=frozen, raw_pages=raw_pages, now=dt.datetime.now(UTC))
    result["frozen_sha256"] = ledger["frozen_file_sha256"]
    result["committed_prediction_ledger_sha256"] = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
    digest = _create_only(out_root / "BLIND_SCORE.json", result)
    return {"status": "OFFICIAL_RESULTS_SCORED", "matched": result["n"],
            "score_sha256": digest, "result_pages": len(raw_pages)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    cap = sub.add_parser("capture-freeze")
    cap.add_argument("--root", type=Path, required=True)
    cap.add_argument("--history", type=Path, required=True)
    cap.add_argument("--identity", type=Path, required=True)
    cap.add_argument("--source-commit", required=True)
    cap.add_argument("--previous-ledger", action="append", type=Path, required=True)
    scr = sub.add_parser("official-score")
    scr.add_argument("--frozen", type=Path, required=True)
    scr.add_argument("--ledger", type=Path, required=True)
    scr.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    if args.mode == "capture-freeze":
        answer = capture_and_freeze(
            output_root=args.root, identity=args.identity, history=args.history,
            commit=args.source_commit, previous_ledgers=args.previous_ledger)
    else:
        answer = fetch_and_score(frozen_path=args.frozen, ledger_path=args.ledger,
                                 out_root=args.root)
    print(json.dumps(answer, ensure_ascii=False))


if __name__ == "__main__":
    main()
