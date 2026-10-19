"""Search-branch derived adversarial, no-future-data regression tests.

Method inspiration: dank0i/football-forecast/tests/test_leakage.py.
Written independently; no external code imported or copied.
"""
from tools.task0032_independent_baseline import evaluate


def _rows():
    days = [
        ("2026-10-10", [0, 1]),
        ("2026-10-11", [2, 0]),
        ("2026-10-12", [1, 0]),
        ("2026-10-13", [2, 2]),
    ]
    return [
        {"matchId": f"{day}-{j}", "date": day, "y": y, "p": [0.50, 0.25, 0.25]}
        for day, outcomes in days
        for j, y in enumerate(outcomes)
    ]


def test_mutating_future_scores_does_not_change_earlier_forecast():
    rows = _rows()
    original = evaluate(rows, min_prior=2)
    tampered = [{**r, "y": 0 if r["date"] == "2026-10-13" else r["y"]} for r in rows]
    changed = evaluate(tampered, min_prior=2)
    earlier = lambda result: [
        (r["day"], r["mid"], r["independent_p"], r["ll_ind"])
        for r in result["evaluated_records"]
        if r["day"] < "2026-10-13"
    ]
    assert earlier(original) == earlier(changed)


def test_odds_mutation_cannot_change_independent_probabilities():
    rows = _rows()
    original = evaluate(rows, min_prior=2)
    changed_rows = [{**r, "p": [0.10, 0.80, 0.10]} for r in rows]
    changed = evaluate(changed_rows, min_prior=2)
    original_independent = [r["independent_p"] for r in original["evaluated_records"]]
    changed_independent = [r["independent_p"] for r in changed["evaluated_records"]]
    assert original_independent == changed_independent
    assert original["market"]["logloss"] != changed["market"]["logloss"]


def test_same_day_outcome_mutation_does_not_change_same_day_forecast():
    rows = _rows()
    baseline = evaluate(rows, min_prior=2)
    target_day = "2026-10-12"
    corrupted = [
        {**r, "y": 2} if r["date"] == target_day else r
        for r in rows
    ]
    replayed = evaluate(corrupted, min_prior=2)
    extract = lambda x, day: [
        (r["mid"], r["independent_p"])
        for r in x["evaluated_records"]
        if r["day"] == day
    ]
    assert extract(baseline, target_day) == extract(replayed, target_day)
    # A later day's forecast is allowed to change after the outcome becomes historical.
    assert extract(baseline, "2026-10-13") != extract(replayed, "2026-10-13")
