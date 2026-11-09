"""TASK0057 adversarial tests: a prospective N=3 is not model alpha."""
import copy
import datetime as dt
import hashlib
import json
import math

import pytest

from tools import task0057_prospective_n3_audit as a


def write_json(path, item):
    path.write_text(json.dumps(item, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_cohort(tmp_path, mids, *, name, anchor, verdict, date,
                targets=None):
    targets = targets or [0] * len(mids)
    anchor_when = dt.datetime.fromisoformat(date + "T07:00:00+00:00")
    frozen_when = anchor_when - dt.timedelta(minutes=10)
    source_when = frozen_when - dt.timedelta(minutes=1)
    training_when = source_when - dt.timedelta(days=60)
    kickoff = anchor_when + dt.timedelta(hours=8)
    scored = kickoff + dt.timedelta(hours=4)
    rows = []
    matching = []
    for i, (mid, target) in enumerate(zip(mids, targets)):
        score = [1, 0] if target == 0 else [0, 2] if target == 2 else [1, 1]
        pm = {}
        for j, key in enumerate(a.MODEL_KEYS):
            prob = .5 - .025 * j - .03 * i
            pm[key] = {
                "actual_outcome_probability": prob,
                "logloss": -math.log(prob),
                "brier3": .5 + j * .01 + i * .02,
                "correct_top_class": bool((i + j) % 2 == 0),
            }
        rows.append({
            "matchId": str(mid), "full_time_score": score,
            "target_home_draw_away": target,
            "kickoff_utc": kickoff.isoformat(), "official_result_status": "2",
            "per_model": pm,
        })
        matching.append({"matchId": str(mid), "target": target,
                         "verified_score": score})
    models = {}
    for key in a.MODEL_KEYS:
        models[key] = {
            "n": len(rows),
            "accuracy": sum(int(r["per_model"][key]["correct_top_class"])
                            for r in rows) / len(rows),
            "mean_logloss": sum(r["per_model"][key]["logloss"] for r in rows) / len(rows),
            "mean_brier3": sum(r["per_model"][key]["brier3"] for r in rows) / len(rows),
        }
    original = {
        "task": "TASK0044", "phase": "OFFICIAL_BLIND_SCORE", "n": len(mids),
        "frozen_sha256": "a" * 64,
        "committed_prediction_ledger_sha256": "b" * 64,
        "raw_result_sha256": ["c" * 64],
        "matched": matching, "model_metrics": models,
        "small_n_no_model_selection": True,
        "no_market_clv_or_profit_claim": True,
    }
    score_path = tmp_path / (name + "-score.json")
    score_sha = write_json(score_path, original)
    qa = {
        "n": len(mids), "verdict": verdict, "git_anchor_commit": anchor,
        "score_sha256": score_sha, "frozen_sha256": "a" * 64,
        "git_ledger_sha256": "b" * 64,
        "not_market_EV_or_model_selection": True,
        "frozen_at_utc": frozen_when.isoformat(),
        "git_anchor_commit_time_utc": anchor_when.isoformat(),
        "scored_at_utc": scored.isoformat(),
        "prediction_source_observed_utc": source_when.isoformat(),
        "training_snapshot_published_utc": training_when.isoformat(),
        "matched": rows,
        "model_metrics_independently_recomputed": models,
    }
    qa_path = tmp_path / (name + "-qa.json")
    qa_sha = write_json(qa_path, qa)
    spec = {"label": name, "ids": tuple(str(i) for i in mids),
            "verdict": verdict, "anchor": anchor,
            "score_sha": score_sha, "qa_sha": qa_sha}
    return score_path, qa_path, spec


def repin(score_path, qa_path, spec):
    spec = copy.deepcopy(spec)
    spec["score_sha"] = a.digest(score_path)
    spec["qa_sha"] = a.digest(qa_path)
    return spec


def test_two_independent_cohorts_weighted_by_actual_match_count(tmp_path, monkeypatch):
    c1 = make_cohort(tmp_path, [1, 2], name="first", anchor="commit1",
                     verdict="QA_2", date="2026-10-28")
    c2 = make_cohort(tmp_path, [3], name="second", anchor="commit2",
                     verdict="QA_1", date="2026-11-08", targets=[2])
    monkeypatch.setattr(a, "COHORTS", (c1[2], c2[2]))
    summary, rows = a.aggregate([(c1[0], c1[1]), (c2[0], c2[1])])
    assert summary["n"] == 3
    assert summary["official_verified_results"] == {
        "home_wins": 2, "draws": 0, "away_wins": 1,
    }
    assert len(rows) == 3
    expected = sum(r["per_model"]["global_frequency"]["logloss"] for r in rows) / 3
    assert summary["models"]["global_frequency"]["mean_logloss"] == pytest.approx(expected)
    assert all(x["n"] == 3 for x in summary["models"].values())
    assert not any("positive" in str(x).lower() for x in summary["models"].values())


def test_any_changed_original_raw_bytes_fail_sha(tmp_path):
    c = make_cohort(tmp_path, [1], name="x", anchor="commit",
                    verdict="QA", date="2026-11-08")
    c[0].write_bytes(c[0].read_bytes() + b" ")
    with pytest.raises(ValueError, match="pinned original"):
        a.validate_cohort(c[0], c[1], c[2])


def test_independent_qa_metrics_mismatch_cannot_be_silently_accepted(tmp_path):
    score, qa_path, spec = make_cohort(
        tmp_path, [1, 2], name="x", anchor="commit", verdict="QA", date="2026-10-28"
    )
    qa = json.loads(qa_path.read_text())
    qa["model_metrics_independently_recomputed"]["league_poisson"]["mean_logloss"] += .02
    write_json(qa_path, qa)
    with pytest.raises(ValueError, match="arithmetic/QA mismatch"):
        a.validate_cohort(score, qa_path, repin(score, qa_path, spec))


def test_inconsistent_official_outcome_is_hard_error(tmp_path):
    score, qa_path, spec = make_cohort(
        tmp_path, [1], name="x", anchor="commit", verdict="QA", date="2026-11-08"
    )
    qa = json.loads(qa_path.read_text())
    qa["matched"][0]["full_time_score"] = [0, 1]
    write_json(qa_path, qa)
    with pytest.raises(ValueError, match="official outcome differs"):
        a.validate_cohort(score, qa_path, repin(score, qa_path, spec))


def test_git_anchor_after_kickoff_must_fail_even_with_accepted_verdict(tmp_path):
    score, qa_path, spec = make_cohort(
        tmp_path, [1], name="x", anchor="commit", verdict="QA", date="2026-11-08"
    )
    qa = json.loads(qa_path.read_text())
    qa["git_anchor_commit_time_utc"] = "2026-11-08T18:00:00+00:00"
    write_json(qa_path, qa)
    with pytest.raises(ValueError, match="invalid Git pre-kickoff"):
        a.validate_cohort(score, qa_path, repin(score, qa_path, spec))


def test_nonfinal_official_status_never_scores(tmp_path):
    score, qa_path, spec = make_cohort(
        tmp_path, [1], name="x", anchor="commit", verdict="QA", date="2026-11-08"
    )
    qa = json.loads(qa_path.read_text())
    qa["matched"][0]["official_result_status"] = "1"
    write_json(qa_path, qa)
    with pytest.raises(ValueError, match="official outcome differs"):
        a.validate_cohort(score, qa_path, repin(score, qa_path, spec))


def test_original_models_cannot_be_removed_or_renamed(tmp_path):
    score_path, qa_path, spec = make_cohort(
        tmp_path, [1], name="x", anchor="commit", verdict="QA", date="2026-11-08"
    )
    score = json.loads(score_path.read_text())
    score["model_metrics"].pop("league_poisson")
    write_json(score_path, score)
    qa = json.loads(qa_path.read_text())
    qa["score_sha256"] = a.digest(score_path)
    write_json(qa_path, qa)
    with pytest.raises(ValueError, match="model contract changed"):
        a.validate_cohort(score_path, qa_path, repin(score_path, qa_path, spec))


def test_duplicate_match_across_cohorts_rejected(tmp_path, monkeypatch):
    c1 = make_cohort(tmp_path, [1, 2], name="first", anchor="commit1",
                     verdict="QA_2", date="2026-10-28")
    c2 = make_cohort(tmp_path, [2], name="second", anchor="commit2",
                     verdict="QA_1", date="2026-11-08")
    monkeypatch.setattr(a, "COHORTS", (c1[2], c2[2]))
    with pytest.raises(ValueError, match="disjoint"):
        a.aggregate([(c1[0], c1[1]), (c2[0], c2[1])])


def test_wrong_cohort_number_refused():
    with pytest.raises(ValueError, match="exactly two"):
        a.aggregate([])


def test_naive_timestamps_rejected():
    with pytest.raises(ValueError, match="naive"):
        a.instant("2026-11-08T19:45:00")
