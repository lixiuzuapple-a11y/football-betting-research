"""TASK0057: historical + live, already-independent-QA-accepted prospective N=3.

This is a *closed-cohort, read-only* second-order aggregation. It does not
fetch results, modify freezes, select a model, estimate market EV, or bet.
It refuses any substituted/edited scored evidence (known SHA anchors).
Source score and independently recomputed per-match metrics must agree.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

UTC = dt.timezone.utc
MODEL_KEYS = ("global_frequency", "league_frequency",
              "pooled_elo_davidson", "league_poisson")
COHORTS = (
    {
        "label": "TASK0044_FIRST_BLIND_OCT31",
        "ids": ("2042359", "2042364"),
        "verdict": "ACCEPT_FIRST_REAL_OFFICIAL_PROSPECTIVE_SCORE_N2",
        "anchor": "a0395a0",
        "score_sha": "c33ae8cf8f67da7453102a840a18bb8c4414b428afb1d36a48178a3b268c8be0",
        "qa_sha": "a9aa37976239489d9eeaded024f06781a713b9fae12c3cb3e3db00a61f021a91",
    },
    {
        "label": "TASK0053_CLOUD_ANCHORED_NOV09_SCORE",
        "ids": ("2042640",),
        "verdict": "ACCEPT_PROSPECTIVE_OFFICIAL_BLIND_SCORE_N1",
        "anchor": "632aced51dabaee194c9a62ab58e3210bc8be3fc",
        "score_sha": "246c62a7f12c2e04773d68155ad018d6a19b5e80514c7e46e8c26e7989a36b97",
        "qa_sha": "8fccb751d0d20e3520a2f42754e9f4d4f6a598213cac91450cbed653edcf668c",
    },
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instant(text: str) -> dt.datetime:
    when = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("naive time in independent score")
    return when.astimezone(UTC)


def near(a: float, b: float) -> None:
    if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(
        a, b, rel_tol=1e-12, abs_tol=1e-12
    ):
        raise ValueError("arithmetic/QA mismatch")


def validate_cohort(score_path: Path, qa_path: Path, spec: dict) -> tuple[dict, list[dict]]:
    if digest(score_path) != spec["score_sha"] or digest(qa_path) != spec["qa_sha"]:
        raise ValueError("pinned original score or independent QA SHA mismatch")
    score = json.loads(score_path.read_text(encoding="utf-8"))
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    n = len(spec["ids"])
    if (score.get("task") != "TASK0044" or score.get("phase") != "OFFICIAL_BLIND_SCORE"
            or score.get("n") != n or qa.get("n") != n
            or qa.get("verdict") != spec["verdict"]
            or qa.get("git_anchor_commit") != spec["anchor"]
            or qa.get("score_sha256") != spec["score_sha"]
            or qa.get("frozen_sha256") != score.get("frozen_sha256")
            or qa.get("git_ledger_sha256") != score.get("committed_prediction_ledger_sha256")
            or not score.get("small_n_no_model_selection")
            or not score.get("no_market_clv_or_profit_claim")
            or not qa.get("not_market_EV_or_model_selection")):
        raise ValueError("source cohort QA identity or non-EV guard mismatch")
    if set(score["model_metrics"]) != set(MODEL_KEYS) or set(
        qa["model_metrics_independently_recomputed"]
    ) != set(MODEL_KEYS):
        raise ValueError("model contract changed")
    sm = {str(x["matchId"]): x for x in score["matched"]}
    qm = {str(x["matchId"]): x for x in qa["matched"]}
    if (len(sm) != n or len(qm) != n
            or set(sm) != set(spec["ids"]) or set(qm) != set(spec["ids"])):
        raise ValueError("partial, substituted or duplicate scored fixture")
    freeze = instant(qa["frozen_at_utc"])
    anchor = instant(qa["git_anchor_commit_time_utc"])
    scored = instant(qa["scored_at_utc"])
    source = instant(qa["prediction_source_observed_utc"])
    training = instant(qa["training_snapshot_published_utc"])
    if not (training <= source <= freeze < anchor < scored):
        raise ValueError("PIT provenance chronological conflict")
    details = []
    for mid in sorted(sm):
        original = sm[mid]
        checked = qm[mid]
        kickoff = instant(checked["kickoff_utc"])
        if anchor >= kickoff or scored < kickoff + dt.timedelta(hours=3):
            raise ValueError("invalid Git pre-kickoff anchor or score timing")
        if (checked["official_result_status"] != "2"
                or checked["full_time_score"] != original["verified_score"]
                or checked["target_home_draw_away"] != original["target"]):
            raise ValueError("official outcome differs from independent QA")
        home, away = original["verified_score"]
        if (not isinstance(home, int) or not isinstance(away, int)
                or home < 0 or away < 0
                or original["target"] != (0 if home > away else 1 if home == away else 2)):
            raise ValueError("illegal full-time result/target")
        if set(checked["per_model"]) != set(MODEL_KEYS):
            raise ValueError("one or more models missing from independent per-fixture score")
        by_model = {}
        for key in MODEL_KEYS:
            row = checked["per_model"][key]
            probability = row["actual_outcome_probability"]
            if not 0 < probability <= 1:
                raise ValueError("invalid realized-outcome probability")
            near(row["logloss"], -math.log(probability))
            if not 0 <= row["brier3"] <= 2 or not isinstance(row["correct_top_class"], bool):
                raise ValueError("invalid independent metric")
            by_model[key] = {
                "logloss": row["logloss"], "brier3": row["brier3"],
                "top_class_hit": int(row["correct_top_class"]),
                "realized_outcome_probability": probability,
            }
        details.append({
            "matchId": mid, "kickoff_utc": kickoff.isoformat(), "target": original["target"],
            "verified_score": original["verified_score"],
            "from_cohort": spec["label"], "per_model": by_model,
        })

    for key in MODEL_KEYS:
        score_summary = score["model_metrics"][key]
        independent = qa["model_metrics_independently_recomputed"][key]
        if score_summary["n"] != n or independent["n"] != n:
            raise ValueError("model N inconsistent")
        for score_field, item_field in (
            ("mean_logloss", "logloss"),
            ("mean_brier3", "brier3"),
            ("accuracy", "top_class_hit"),
        ):
            from_rows = sum(r["per_model"][key][item_field] for r in details) / n
            near(score_summary[score_field], from_rows)
            near(independent[score_field], from_rows)

    return {
        "cohort": spec["label"], "n": n, "git_anchor": spec["anchor"],
        "score_sha256": spec["score_sha"], "independent_qa_sha256": spec["qa_sha"],
        "frozen_source_sha256": score["frozen_sha256"],
        "source_official_pages_sha256": score["raw_result_sha256"],
        "scored_at_utc": scored.isoformat(),
    }, details


def aggregate(inputs: list[tuple[Path, Path]]) -> tuple[dict, list[dict]]:
    if len(inputs) != len(COHORTS):
        raise ValueError("exactly two original independently accepted cohorts required")
    cohorts, rows = [], []
    for (score_path, qa_path), spec in zip(inputs, COHORTS):
        cohort, details = validate_cohort(score_path, qa_path, spec)
        cohorts.append(cohort)
        rows.extend(details)
    if len(rows) != 3 or len({r["matchId"] for r in rows}) != len(rows):
        raise ValueError("not exactly the 3 disjoint accepted prospective fixtures")
    result = {
        "task": "TASK0057",
        "status": "ACCEPT_DESCRIPTIVE_PROSPECTIVE_N3_NO_EV",
        "model_freeze_policy": "previously committed independent QA only; no refitting",
        "n": len(rows), "source_cohorts": cohorts,
        "official_verified_results": {
            "home_wins": sum(x["target"] == 0 for x in rows),
            "draws": sum(x["target"] == 1 for x in rows),
            "away_wins": sum(x["target"] == 2 for x in rows),
        },
        "models": {},
        "limits": [
            "n=3: descriptive arithmetic, no statistical model comparison or selection.",
            "Market pre-kickoff 1X2 odds absent for these 3 games; CLV, EV and ROI not assessed.",
            "Do not merge retrospective 175-game market benchmark into this forward cohort.",
            "Git commit clock is not an independently notarized timestamp authority.",
            "Do not project a win rate, place wagers or change original prospective model parameters.",
        ],
    }
    for key in MODEL_KEYS:
        measures = [r["per_model"][key] for r in rows]
        result["models"][key] = {
            "n": 3,
            "mean_logloss": sum(r["logloss"] for r in measures) / 3,
            "mean_brier3": sum(r["brier3"] for r in measures) / 3,
            "top_class_correct": sum(r["top_class_hit"] for r in measures),
            "top_class_accuracy": sum(r["top_class_hit"] for r in measures) / 3,
        }
    return result, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("prior-score", "prior-audit", "new-score", "new-audit",
                  "out-summary", "out-detail"):
        parser.add_argument("--" + field, dest=field.replace("-", "_"),
                            type=Path, required=True)
    args = parser.parse_args()
    summary, detail = aggregate([
        (args.prior_score, args.prior_audit), (args.new_score, args.new_audit)
    ])
    for file, value in ((args.out_summary, summary), (args.out_detail, detail)):
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
