"""Independent read-only TASK0044 two-fixture blind-score QA.

Uses original Git anchor bytes and official raw result payload, and independently
recalculates all log losses, Brier scores and accuracies. It never calls a result
endpoint, mutates the initial freeze or reuses the original scorer's calculations.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

UTC = dt.timezone.utc
BJT = dt.timezone(dt.timedelta(hours=8))
MODEL_KEYS = ("global_frequency", "league_frequency",
              "pooled_elo_davidson", "league_poisson")
RESULT_URL = "https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry"
LEDGER_PATH = "research/task0043_pre_kickoff_multimodel_freeze_20261029.json"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def instant(raw: str) -> dt.datetime:
    value = dt.datetime.fromisoformat(raw)
    if value.utcoffset() is None:
        raise ValueError("naive timestamp")
    return value.astimezone(UTC)


def require(ok: bool, problem: str) -> None:
    if not ok:
        raise ValueError(problem)


def independent_audit(*, repo: Path, freeze: Path, ledger: Path,
                      result_root: Path, anchor: str = "a0395a0") -> dict:
    """Provenance and arithmetic must be independently verifiable from bytes."""
    original = freeze.read_bytes()
    committed = ledger.read_bytes()
    frozen = json.loads(original)
    pledge = json.loads(committed)
    score_raw = (result_root / "BLIND_SCORE.json").read_bytes()
    score = json.loads(score_raw)
    manifest = json.loads((result_root / "SOURCE_MANIFEST.json").read_bytes())
    git_source = subprocess.run(["git", "show", f"{anchor}:{LEDGER_PATH}"],
                                cwd=repo, capture_output=True, check=True, timeout=15)
    # On this Windows checkout, core.autocrlf=true and the Git index stores
    # LF while the working tree may hold CRLF. This is NOT byte-for-byte
    # identical; accept only that exact newline-only transform and record it.
    git_canonical = git_source.stdout
    newline_only = (git_canonical != committed and b"\r\n" in committed and
                    committed.replace(b"\r\n", b"\n") == git_canonical)
    require(git_canonical == committed or newline_only,
            "published Git ledger differs beyond CRLF-to-LF transformation")
    git_time = subprocess.run(["git", "show", "-s", "--format=%cI", anchor],
                              cwd=repo, capture_output=True, text=True,
                              check=True, timeout=15).stdout.strip()
    published = instant(git_time)
    require(pledge["status"] == "PRE_KICKOFF_FROZEN_RESEARCH_ONLY" and
            frozen["task"] == "TASK0043" and score["task"] == "TASK0044",
            "wrong freeze, ledger or score type")
    require(pledge["frozen_file_sha256"] == sha(original) ==
            score["frozen_sha256"] == manifest["frozen_sha256"],
            "original freeze SHA does not match anchor and result")
    require(score["committed_prediction_ledger_sha256"] == sha(committed),
            "original Git pledge SHA mismatch")
    require(frozen["predictions"] == pledge["predictions"] and
            pledge["qualified"] == len(frozen["predictions"]) ==
            score["n"] == len(score["matched"]),
            "original forecast vectors/cohort changed")
    require(frozen["capture"]["sha256"] == pledge["official_raw_sha256"] and
            frozen["market_prices_input_to_models"] is False and
            frozen["new_results_input_to_models"] is False,
            "source evidence or prediction/market independence invalid")
    train = dt.date.fromisoformat(frozen["history"]["last_training_date"])
    started = instant(frozen["frozen_at_utc"])
    observed = instant(frozen["capture"]["received_utc"])
    source_published = instant(frozen["history"]["published_at_utc"])
    scored = instant(score["scored_at_utc"])
    require(source_published <= started and
            train < started.date() and observed <= started and
            started < published < scored,
            "chronology of training/capture/commit/score invalid")
    predictions = {str(p["matchId"]):p for p in frozen["predictions"]}
    require(len(predictions) == score["n"] and score["n"] > 0,
            "duplicate or no original frozen fixtures")
    kickoff_dates = []
    for row in predictions.values():
        kick = instant(row["kickoff_utc"])
        require(published < kick and started < kick,
                "Git anchor or freeze at/after kickoff")
        kickoff_dates.append(kick)
    require(scored >= max(kickoff_dates) + dt.timedelta(hours=3),
            "official scoring before conservative post-match delay")
    pages = manifest["pages"]
    require(isinstance(pages, list) and len(pages) > 0 and
            score["raw_result_sha256"] == [p["sha256"] for p in pages],
            "manifest page SHA list conflict")
    actual = {}
    page_checks = []
    for meta in pages:
        name = meta["file"]
        require(re.fullmatch(r"official-\d{4}-\d{2}-\d{2}-page-\d+\.json", name) is not None,
                "unexpected result raw file path")
        raw = (result_root / name).read_bytes()
        require(meta["bytes"] == len(raw) and sha(raw) == meta["sha256"] and
                meta["http_status"] == 200 and
                meta["source_url"].split("?")[0] == RESULT_URL,
                "official raw byte/SHA, HTTP or URL provenance invalid")
        requested = instant(meta["request_started_utc"])
        received = instant(meta["response_received_utc"])
        require(started < requested <= received <= scored,
                "official result receipt chronology invalid")
        document = json.loads(raw)
        require(document.get("success") is True and
                str(document.get("errorCode")) == "0",
                "official result API response failed")
        value = document["value"]
        require(isinstance(value.get("matchResult"), list), "official result list absent")
        for line in value["matchResult"]:
            mid = str(line.get("matchId"))
            if mid in predictions:
                require(mid not in actual, "duplicate official target in response pages")
                actual[mid] = line
        page_checks.append({"name": name, "sha256": meta["sha256"],
                            "bytes": len(raw), "http": 200,
                            "received_utc": received.isoformat()})
    require(set(actual) == set(predictions), "official result incomplete for frozen cohort")
    independent_rows = []
    graded = {}
    for mid in sorted(predictions):
        forecast = predictions[mid]
        official = actual[mid]
        require(str(official.get("matchResultStatus")) == "2",
                "not official final status")
        require(str(official.get("homeTeamId")) == str(forecast["official_home_id"]) and
                str(official.get("awayTeamId")) == str(forecast["official_away_id"]),
                "official fixture identity mismatch")
        kick = instant(forecast["kickoff_utc"])
        require(str(official.get("matchDate")) == kick.astimezone(BJT).date().isoformat(),
                "official result match-date mismatch")
        score_text = str(official.get("sectionsNo999"))
        require(re.fullmatch(r"\d{1,2}:\d{1,2}", score_text) is not None,
                "invalid official final full-time score")
        h, a = (int(x) for x in score_text.split(":"))
        require(h <= 25 and a <= 25, "implausible official score")
        y = 0 if h > a else (1 if h == a else 2)
        per_model = {}
        vectors = forecast["models_1x2_home_draw_away"]
        require(set(vectors) == set(MODEL_KEYS), "model set differs from original freeze")
        for key in MODEL_KEYS:
            probabilities = vectors[key]
            require(len(probabilities) == 3 and
                    all(isinstance(q,(int,float)) and not isinstance(q,bool) and
                        math.isfinite(q) and 0 < q < 1 for q in probabilities) and
                    abs(sum(probabilities)-1)<1e-9,
                    "invalid historical committed 1X2 probabilities")
            l = -math.log(probabilities[y])
            b = sum((q - (1 if j == y else 0))**2
                    for j,q in enumerate(probabilities))
            acc = int(max(range(3), key=probabilities.__getitem__) == y)
            graded.setdefault(key, []).append((l,b,acc))
            per_model[key] = {
                "actual_outcome_probability": probabilities[y],
                "logloss": l, "brier3": b, "correct_top_class": bool(acc)
            }
        independent_rows.append({
            "matchId": mid, "kickoff_utc": kick.isoformat(),
            "official_home_id": str(official["homeTeamId"]),
            "official_away_id": str(official["awayTeamId"]),
            "official_result_status": "2",
            "full_time_score": [h,a], "target_home_draw_away":y,
            "per_model":per_model
        })
    require({x["matchId"] for x in score["matched"]} == set(predictions),
            "published scoring cohort differs")
    for original_row in score["matched"]:
        verified = next(z for z in independent_rows
                        if z["matchId"] == str(original_row["matchId"]))
        require(original_row["verified_score"] == verified["full_time_score"] and
                original_row["target"] == verified["target_home_draw_away"],
                "scored outcome differs from official bytes")
    stats = {}
    for name, trials in graded.items():
        n = len(trials)
        values = {"n":n,
                  "mean_logloss":sum(t[0] for t in trials)/n,
                  "mean_brier3":sum(t[1] for t in trials)/n,
                  "accuracy":sum(t[2] for t in trials)/n}
        for key,value in values.items():
            original_metric = score["model_metrics"][name][key]
            require(math.isclose(value,original_metric,abs_tol=1e-12,rel_tol=1e-12),
                    f"independently recomputed {name}.{key} differs")
        stats[name] = values
    return {
        "scope":"EVLab/TASK0044",
        "verdict":"ACCEPT_FIRST_REAL_OFFICIAL_PROSPECTIVE_SCORE_N2",
        "not_market_EV_or_model_selection":True,
        "git_anchor_commit":anchor,
        "git_anchor_commit_time_utc":published.isoformat(),
        "git_commit_time_is_not_independent_timestamp_authority":True,
        "frozen_at_utc":started.isoformat(),
        "training_last_date":train.isoformat(),
        "training_snapshot_published_utc":source_published.isoformat(),
        "prediction_source_observed_utc":observed.isoformat(),
        "frozen_sha256":sha(original),
        "git_ledger_sha256":sha(committed),
        "git_blob_ledger_sha256":sha(git_canonical),
        "git_checkout_differs_only_in_crlf_to_lf":bool(newline_only),
        "git_ledger_byte_identity":git_canonical == committed,
        "score_sha256":sha(score_raw),
        "scored_at_utc":scored.isoformat(),
        "official_pages":page_checks,
        "matched":independent_rows,
        "model_metrics_independently_recomputed":stats,
        "n":len(independent_rows),
        "market_odds_status":"UNVERIFIED_NOT_ASSESSED",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--freeze",required=True,type=Path)
    p.add_argument("--ledger",required=True,type=Path)
    p.add_argument("--score-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--anchor",default="a0395a0")
    a=p.parse_args()
    audit=independent_audit(repo=a.repo,freeze=a.freeze,ledger=a.ledger,
                            result_root=a.score_root,anchor=a.anchor)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as fd:
        json.dump(audit,fd,ensure_ascii=False,sort_keys=True,indent=2)
    print(json.dumps({"verdict":audit["verdict"],"n":audit["n"],
                      "score_sha256":audit["score_sha256"],
                      "out":str(a.out)},ensure_ascii=False))


if __name__=="__main__":
    main()
