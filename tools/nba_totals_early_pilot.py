"""Frozen 2026-10-30 NBA early-season totals research pilot (stdlib only).

This is a descriptive study of one third-party dataset, NOT a betting model.
Preregistration: research/experiments/NBA-TOTALS-EARLY-SEASON-PILOT-PREGISTER-20261030.md
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


def season_of(day: date) -> int:
    return day.year if day.month >= 9 else day.year - 1


def wilson(k: int, n: int) -> list[float] | None:
    if n == 0:
        return None
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 6), round(c + h, 6)]


def summarize(rows: list[dict]) -> dict:
    outcomes = Counter(r["outcome"] for r in rows)
    graded = outcomes["over"] + outcomes["under"]
    return {
        "total": len(rows),
        "over": outcomes["over"],
        "under": outcomes["under"],
        "push": outcomes["push"],
        "graded": graded,
        "over_rate": round(outcomes["over"] / graded, 6) if graded else None,
        "over_rate_ci95": wilson(outcomes["over"], graded),
    }


def comparison(rows: list[dict]) -> dict:
    early = summarize([r for r in rows if r["period"] == "early"])
    later = summarize([r for r in rows if r["period"] == "comparison"])
    n1, n2 = early["graded"], later["graded"]
    delta = None
    z = None
    p_value = None
    if n1 and n2:
        delta = early["over_rate"] - later["over_rate"]
        pooled = (early["over"] + later["over"]) / (n1 + n2)
        se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
        if se:
            z = delta / se
            p_value = math.erfc(abs(z) / math.sqrt(2))
    return {
        "early": early,
        "comparison": later,
        "delta_over_rate": round(delta, 6) if delta is not None else None,
        "two_sided_p_approx": round(p_value, 8) if p_value is not None else None,
        "z": round(z, 5) if z is not None else None,
    }


def run(path: Path, sensitivity: bool = False) -> dict:
    data = path.read_bytes()
    source_hash = hashlib.sha256(data).hexdigest()
    audit = Counter()
    raw: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rdr = csv.DictReader(file)
        needed = {"Date", "Home", "Away", "OU", "Points"}
        if not needed.issubset(set(rdr.fieldnames or [])):
            raise ValueError("Missing required columns")
        for item in rdr:
            audit["input_rows"] += 1
            try:
                day = date.fromisoformat(item["Date"])
                home, away = item["Home"].strip(), item["Away"].strip()
                ou = float(item["OU"])
                points = float(item["Points"])
                if not home or not away or not math.isfinite(ou) or not math.isfinite(points):
                    raise ValueError("missing/invalid field")
                if not (130 <= ou <= 300) or not (100 <= points <= 400):
                    audit["suspicious_values"] += 1
                    # Frozen run retains these; post-hoc quality sensitivity excludes them.
                    if sensitivity:
                        audit["quality_excluded_suspicious"] += 1
                        continue
            except (ValueError, KeyError, TypeError):
                audit["invalid_rows"] += 1
                continue
            key = (day.isoformat(), home, away)
            if key in seen:
                audit["duplicate_keys"] += 1
                continue
            seen.add(key)
            season = season_of(day)
            if not 2007 <= season <= 2025:
                audit["outside_season_scope"] += 1
                continue
            if sensitivity and season in (2020, 2025):
                # 2020 bubble contaminates the date-derived 2020/21 opener;
                # 2025/26 data stop in January 2026. Not part of frozen test.
                audit["quality_excluded_special_incomplete_season"] += 1
                continue
            result = "over" if points > ou else "under" if points < ou else "push"
            raw.append({"day": day, "season": season, "outcome": result})
    first_day: dict[int, date] = {}
    for row in raw:
        yr = row["season"]
        first_day[yr] = min(first_day.get(yr, row["day"]), row["day"])
    included = []
    period_counts = Counter()
    for row in raw:
        season_day = (row["day"] - first_day[row["season"]]).days
        if season_day <= 29:
            period = "early"
        elif season_day <= 119:
            period = "comparison"
        else:
            period = "excluded_day_120_plus"
        period_counts[period] += 1
        if period != "excluded_day_120_plus":
            included.append({"season": row["season"], "period": period, "outcome": row["outcome"]})
    train = comparison([r for r in included if r["season"] <= 2020])
    hold = comparison([r for r in included if r["season"] >= 2021])
    train_delta, hold_delta = train["delta_over_rate"], hold["delta_over_rate"]
    season_detail = {
        str(yr): comparison([r for r in included if r["season"] == yr])
        for yr in sorted(first_day)
    }
    season_agree = sum(
        1
        for yr in range(2021, 2026)
        if train_delta is not None
        and season_detail.get(str(yr), {}).get("delta_over_rate") is not None
        and season_detail[str(yr)]["delta_over_rate"] * train_delta > 0
    )
    quality_fail = audit["duplicate_keys"] > 0 or audit["suspicious_values"] > 0
    qualifies = (
        not quality_fail
        and train_delta is not None
        and hold_delta is not None
        and hold["early"]["graded"] >= 500
        and hold["two_sided_p_approx"] is not None
        and hold["two_sided_p_approx"] < 0.05
        and abs(hold_delta) >= 0.03
        and train_delta * hold_delta > 0
        and season_agree >= 3
    )
    verdict = "RESEARCH-CANDIDATE (NO BETTING CLAIM)" if qualifies else "NO-GO (FIXED HYPOTHESIS)"
    if sensitivity:
        verdict = "POST-HOC QUALITY SENSITIVITY ONLY (NOT A NEW CONFIRMATORY TEST)"
    return {
        "source": "https://raw.githubusercontent.com/aaryanshah607/nba-line-sheet/main/nba_odds_clean.csv",
        "sha256": source_hash,
        "analysis_mode": "post_hoc_quality_sensitivity" if sensitivity else "frozen_initial",
        "byte_size": len(data),
        "audit": dict(audit),
        "valid_unique_rows": len(raw),
        "period_counts": dict(period_counts),
        "season_first_date": {str(y): d.isoformat() for y, d in sorted(first_day.items())},
        "train_2007_2020": train,
        "holdout_2021_2025": hold,
        "holdout_seasons_agree_with_train": season_agree,
        "per_season": season_detail,
        "verdict": verdict,
        "limitations": [
            "Third-party odds provenance and time of quote unverified.",
            "No totals selection prices / Chinese lottery lines; ROI, CLV, EV cannot be inferred.",
            "No independent game/score reconciliation; no multiplicity-adjusted claim.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sensitivity", action="store_true")
    opts = parser.parse_args()
    report = run(opts.input, sensitivity=opts.sensitivity)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if opts.output:
        opts.output.parent.mkdir(parents=True, exist_ok=True)
        opts.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
