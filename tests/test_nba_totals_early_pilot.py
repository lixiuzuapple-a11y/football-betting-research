"""Tiny synthetic QA for the isolated NBA totals pilot, no network or live odds."""

import csv
from datetime import date

from tools.nba_totals_early_pilot import comparison, run, season_of, summarize, wilson


def test_season_assignment_regular_2021():
    assert season_of(date(2021, 10, 19)) == 2021
    assert season_of(date(2022, 1, 10)) == 2021


def test_push_is_not_in_graded_denominator():
    summary = summarize(
        [
            {"outcome": "over"},
            {"outcome": "under"},
            {"outcome": "push"},
        ]
    )
    assert summary["total"] == 3
    assert summary["graded"] == 2
    assert summary["over_rate"] == 0.5
    assert wilson(1, 2)[0] < 0.5 < wilson(1, 2)[1]


def test_early_vs_comparison_direction():
    sample = [
        {"period": "early", "outcome": "over"},
        {"period": "early", "outcome": "over"},
        {"period": "comparison", "outcome": "under"},
        {"period": "comparison", "outcome": "under"},
    ]
    result = comparison(sample)
    assert result["delta_over_rate"] == 1.0
    assert result["two_sided_p_approx"] < 0.05


def test_source_data_validation_and_sensitivity(tmp_path):
    path = tmp_path / "pilot.csv"
    with path.open("w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Home", "Away", "OU", "Points"])
        writer.writeheader()
        writer.writerow({"Date": "2021-10-19", "Home": "A", "Away": "B", "OU": "200", "Points": "201"})
        writer.writerow({"Date": "2021-10-19", "Home": "A", "Away": "B", "OU": "200", "Points": "201"})
        writer.writerow({"Date": "2021-10-20", "Home": "C", "Away": "D", "OU": "0", "Points": "202"})
        writer.writerow({"Date": "2021-10-21", "Home": "E", "Away": "F", "OU": "205", "Points": "205"})
    original = run(path)
    clean = run(path, sensitivity=True)
    assert original["audit"]["duplicate_keys"] == 1
    assert original["audit"]["suspicious_values"] == 1
    assert original["holdout_2021_2025"]["early"]["push"] == 1
    assert clean["audit"]["quality_excluded_suspicious"] == 1
    assert clean["holdout_2021_2025"]["early"]["total"] == 2
