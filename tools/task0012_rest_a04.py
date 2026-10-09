"""TASK-0011 A04 fixed historical rest residual experiment.

Run from repo root: python tools/task0011_rest_a04.py --input <hist_v2.csv> --output <summary.json>
Only standard library; never changes source data.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


def parse_date(value: str):
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError("invalid date")

def compute(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    records = []
    exclusions = Counter()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for record in csv.DictReader(f):
            try:
                date = parse_date(record["date"])
                key = (record["lg"], record["season"], date, record["home"].strip(), record["away"].strip())
                if not all(key[i] for i in (0, 1, 3, 4)):
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                exclusions["invalid_identity_date"] += 1
                continue
            records.append((key, record))
    records.sort(key=lambda item: item[0][2])
    frequencies = Counter(key for key, _ in records)
    same_day = Counter((key[0], key[1], key[2], team) for key, _ in records for team in (key[3], key[4]))
    last_date = {}
    groups = defaultdict(list)
    valid_with_rest = 0
    for key, r in records:
        lg, season, date, home, away = key
        if frequencies[key] > 1:
            exclusions["duplicate_fixture"] += 1
            continue
        if same_day[(lg, season, date, home)] > 1 or same_day[(lg, season, date, away)] > 1:
            exclusions["ambiguous_same_day"] += 1
            continue
        home_key, away_key = (lg, season, home), (lg, season, away)
        hp, ap = last_date.get(home_key), last_date.get(away_key)
        # update the known fixture sequence even if price/outcome is missing
        last_date[home_key] = date
        last_date[away_key] = date
        if hp is None or ap is None:
            exclusions["no_prior_fixture"] += 1
            continue
        hrest, arest = (date - hp).days, (date - ap).days
        if not (0 < hrest <= 30 and 0 < arest <= 30):
            exclusions["invalid_rest_interval"] += 1
            continue
        valid_with_rest += 1
        try:
            odds = [float(r[field]) for field in ("PSH", "PSD", "PSA")]
            if any(not math.isfinite(x) or x <= 1.0 for x in odds):
                raise ValueError()
            implied = [1 / x for x in odds]
            ph = implied[0] / sum(implied)
            result = r["ftr"].strip().upper()
            if result not in ("H", "D", "A"):
                raise ValueError()
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            exclusions["missing_opening_price_or_result"] += 1
            continue
        diff = hrest - arest
        name = "home_adv" if diff >= 3 else "away_adv" if diff <= -3 else "neutral"
        groups[(lg, season)].append((name, (1.0 if result == "H" else 0.0) - ph, ph))
    def aggregate(parts):
        sums = Counter()
        counts = Counter()
        probs = Counter()
        for observations in parts:
            for name, resid, ph in observations:
                sums[name] += resid
                counts[name] += 1
                probs[name] += ph
        return counts, sums, probs
    counts, sums, probs = aggregate(groups.values())
    def contrast(cnt, sm):
        if cnt["home_adv"] == 0 or cnt["away_adv"] == 0:
            return None
        return sm["home_adv"] / cnt["home_adv"] - sm["away_adv"] / cnt["away_adv"]
    effect = contrast(counts, sums)
    rng = random.Random(1109)
    keys = sorted(groups)
    samples = []
    for _ in range(2000):
        selected = [groups[keys[rng.randrange(len(keys))]] for _ in keys] if keys else []
        cc, ss, _ = aggregate(selected)
        val = contrast(cc, ss)
        if val is not None:
            samples.append(val)
    samples.sort()
    ci = [samples[int((len(samples) - 1) * p)] for p in (0.025, 0.975)] if samples else None
    enough = len(keys) >= 8 and counts["home_adv"] >= 50 and counts["away_adv"] >= 50 and len(samples) == 2000
    result = {
        "source_sha256": digest, "source_rows_parsed": len(records),
        "exclusions": dict(exclusions), "valid_rest_rows_before_price_filter": valid_with_rest,
        "matched_league_seasons": len(keys), "groups": {
            name: {"n": counts[name], "mean_home_win_residual": sums[name] / counts[name] if counts[name] else None,
                   "mean_market_home_probability": probs[name] / counts[name] if counts[name] else None}
            for name in ("home_adv", "away_adv", "neutral")
        }, "primary_contrast": effect, "cluster_bootstrap_seed": 1109,
        "cluster_bootstrap_draws_valid": len(samples), "cluster_bootstrap_ci_95": ci,
        "preregistered_adequacy_pass": enough,
        "interpretation": ("EXPLORATORY_POSITIVE_ASSOCIATION_ONLY" if enough and ci and ci[0] > 0 else
            "EXPLORATORY_NEGATIVE_DIRECTION" if enough and ci and ci[1] < 0 else
            "NOT_VALIDATED_OR_INCONCLUSIVE"),
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compute(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

