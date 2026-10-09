"""Independent standard-library cross-check of TASK-0011 A04 group counts/means.

Does not import the primary A04 implementation or use the saved summary to compute.
"""
import argparse
import csv
import datetime
import json
from collections import defaultdict
from pathlib import Path


def audit(src):
    raw = []
    bad = 0
    for r in csv.DictReader(Path(src).open(encoding="utf-8-sig", newline="")):
        try:
            d = datetime.datetime.strptime(r["date"], "%d/%m/%y").date()
            key = (r["lg"], r["season"], d, r["home"].strip(), r["away"].strip())
            if not all([key[0], key[1], key[3], key[4]]):
                raise ValueError("empty identity")
            raw.append((key, r))
        except (ValueError, KeyError, TypeError):
            bad += 1
    raw.sort(key=lambda x: x[0][2])
    from collections import Counter
    duplicates = Counter(x[0] for x in raw)
    dates = Counter((k[0], k[1], k[2], team) for k, _ in raw for team in (k[3], k[4]))
    seen = {}
    out = defaultdict(list)
    for k, r in raw:
        lg, season, date, home, away = k
        if duplicates[k] != 1 or dates[(lg, season, date, home)] != 1 or dates[(lg, season, date, away)] != 1:
            continue
        hk = lg, season, home
        ak = lg, season, away
        hprev = seen.get(hk)
        aprev = seen.get(ak)
        seen[hk] = date
        seen[ak] = date
        if hprev is None or aprev is None:
            continue
        hr = (date - hprev).days
        ar = (date - aprev).days
        if not (0 < hr <= 30 and 0 < ar <= 30):
            continue
        try:
            odds = [float(r[col]) for col in ["PSH", "PSD", "PSA"]]
            if not all(1.0 < x < float("inf") for x in odds):
                continue
            result = r["ftr"].strip().upper()
            if result not in ("H", "D", "A"):
                continue
            p = (1/odds[0]) / sum(1/x for x in odds)
        except (KeyError, ValueError, TypeError, ZeroDivisionError):
            continue
        label = "home_adv" if hr-ar >= 3 else ("away_adv" if hr-ar <= -3 else "neutral")
        out[label].append((int(result == "H") - p, p))
    def metric(k):
        vals = out[k]
        return {"n": len(vals), "mean_home_win_residual": sum(x[0] for x in vals) / len(vals) if vals else None}
    h, a, n = metric("home_adv"), metric("away_adv"), metric("neutral")
    return {"source_rows_parsed": len(raw), "invalid_identity_date": bad,
            "groups": {"home_adv": h, "away_adv": a, "neutral": n},
            "primary_contrast": h["mean_home_win_residual"] - a["mean_home_win_residual"]}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--compare", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    actual = audit(a.input)
    reference = json.loads(Path(a.compare).read_text(encoding="utf-8"))
    matched = actual["source_rows_parsed"] == reference["source_rows_parsed"]
    matched &= actual["invalid_identity_date"] == reference["exclusions"]["invalid_identity_date"]
    for key in ("home_adv", "away_adv", "neutral"):
        matched &= actual["groups"][key]["n"] == reference["groups"][key]["n"]
        matched &= abs(actual["groups"][key]["mean_home_win_residual"] - reference["groups"][key]["mean_home_win_residual"]) < 1e-10
    matched &= abs(actual["primary_contrast"] - reference["primary_contrast"]) < 1e-10
    actual["matches_primary"] = bool(matched)
    Path(a.output).write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(actual, indent=2))
    raise SystemExit(0 if matched else 1)
