"""TASK0051: retrospective, same-fixture international-market score audit.

This is a non-PIT research benchmark. The historical model predictions are
frozen retrospectively by test date, and the published market snapshot itself
is not independently time-attested as of the model prediction cutoff.
Never infer market alpha, executable CLV, or EV from this tool.

Input market data must carry permission to perform this analysis; source raw
bytes and match-level evidence remain outside Git. No data is fetched here.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
import random
import unicodedata
from pathlib import Path

MODEL_DETAILS_SHA = "9156dadeb36147163deef80591be069aec577668e8ca6dd7487110b0dbaa5fee"
HIST_FIXTURES_SHA = "7ba90661dbed29eb940daf5ea385c7d76d5751d16be86bd9063293a982abc7b7"
MARKET_URL = "https://tipsaudit.com/data/tipsaudit-predictions.csv"
FIRST = dt.date(2026, 6, 11)
LAST_EXCLUSIVE = dt.date(2026, 7, 1)
UTC = dt.timezone.utc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_team(value: str) -> str:
    """Case/diacritic/punctuation normalization; never invent fuzzy aliases."""
    raw = unicodedata.normalize("NFKD", (value or "").casefold())
    return "".join(c for c in raw if c.isalnum() and not unicodedata.combining(c))


def read_odds(values: list[str]) -> list[float] | None:
    try:
        odds = [float(v) for v in values]
    except (TypeError, ValueError):
        return None
    if len(odds) != 3 or any(not math.isfinite(o) or o <= 1.001 or o >= 500 for o in odds):
        return None
    inverse = [1 / o for o in odds]
    return [x / sum(inverse) for x in inverse]


def read_fair(values: list[str]) -> list[float] | None:
    try:
        probabilities = [float(v) for v in values]
    except (TypeError, ValueError):
        return None
    if len(probabilities) != 3 or any(not math.isfinite(x) or x <= 0 or x >= 1 for x in probabilities):
        return None
    total = sum(probabilities)
    if abs(total - 1) > 0.003:
        return None
    return [x / total for x in probabilities]


def metric(prob: list[float], target: int) -> tuple[float, float]:
    if not (0 <= target <= 2 and len(prob) == 3 and
            all(math.isfinite(x) and 0 < x < 1 for x in prob) and
            abs(sum(prob) - 1) < 1e-5):
        raise ValueError("invalid target or 1X2 probability vector")
    return -math.log(prob[target]), sum((prob[i] - int(i == target))**2 for i in range(3))


def market_result(row: dict) -> int | None:
    return {"1": 0, "X": 1, "2": 2}.get(row.get("result", ""))


def load_historical_index(source: Path, *, max_minutes: int = 60) -> dict:
    """Index only by same home/away team names plus aligned UTC kickoff time.

    Historical final score is returned as an independent validation attribute
    and is never used to choose among candidate fixture IDs.
    """
    import duckdb
    if sha256(source / "fixtures.parquet") != HIST_FIXTURES_SHA:
        raise ValueError("frozen historical fixture source SHA changed")
    con = duckdb.connect()
    try:
        fixtures = con.execute(
            "SELECT id,date_utc,league_id,home_team_id,away_team_id,goals_home,goals_away "
            "FROM read_parquet(?) WHERE date_utc>=? AND date_utc<?",
            [str(source / "fixtures.parquet"),
             (FIRST-dt.timedelta(days=1)).isoformat(),
             (LAST_EXCLUSIVE+dt.timedelta(days=1)).isoformat()],
        ).fetchall()
        team_names = {i: (name, fd) for i, name, fd in con.execute(
            "SELECT id,name,fd_name FROM read_parquet(?)", [str(source / "teams.parquet")]
        ).fetchall()}
        league_countries = {i: country for i, country in con.execute(
            "SELECT id,country FROM read_parquet(?)", [str(source / "leagues.parquet")]
        ).fetchall()}
    finally:
        con.close()
    index = collections.defaultdict(dict)
    for mid, when, league, hid, aid, goals_home, goals_away in fixtures:
        hnames = {normalize_team(s) for s in team_names.get(hid, ()) if s}
        anames = {normalize_team(s) for s in team_names.get(aid, ()) if s}
        for hname in hnames:
            for aname in anames:
                if hname and aname:
                    index[(hname, aname)][int(mid)] = {
                        "match_id": int(mid), "when": when, "league_id": int(league),
                        "country": league_countries.get(league),
                        "gh": goals_home, "ga": goals_away,
                    }
    return dict(index)


def associate(market: dict, index: dict, *, max_minutes: int = 60) -> tuple[dict | None, str]:
    """Strict unique fixture mapping, never using market or historical result."""
    try:
        kickoff = dt.datetime.fromisoformat(market["kickoff_utc"])
    except (KeyError, TypeError, ValueError):
        return None, "bad_kickoff"
    if kickoff.utcoffset() is None:
        return None, "bad_kickoff"
    if not (FIRST <= kickoff.date() < LAST_EXCLUSIVE):
        return None, "out_of_window"
    when_utc = kickoff.astimezone(UTC).replace(tzinfo=None)
    pair = (normalize_team(market.get("home", "")),
            normalize_team(market.get("away", "")))
    candidates = [
        x for x in index.get(pair, {}).values()
        if x["when"] is not None
        and abs((when_utc - x["when"]).total_seconds()) <= max_minutes * 60
        and normalize_team(x.get("country") or "") == normalize_team(market.get("country", ""))
    ]
    if len(candidates) != 1:
        return None, "ambiguous" if candidates else "unmatched_identity_or_time"
    return candidates[0], "ok"


def mean(vals: list[float]) -> float:
    return sum(vals)/len(vals)


def daily_paired_bootstrap(pairs: list[dict], *, draws: int = 3000) -> dict:
    by_day = collections.defaultdict(list)
    for item in pairs:
        by_day[item["date"]].append(item["market_logloss"] - item["poisson_logloss"])
    days = sorted(by_day)
    if len(days) < 2:
        return {"lower_95": None, "upper_95": None, "days": len(days)}
    rng = random.Random(20261103)
    samples = []
    for _ in range(draws):
        selected = [by_day[days[rng.randrange(len(days))]] for __ in days]
        samples.append(sum(map(sum, selected)) / sum(map(len, selected)))
    samples.sort()
    return {
        "lower_95": samples[int(draws * .025)],
        "upper_95": samples[int(draws * .975)],
        "days": len(days), "bootstrap_seed": 20261103,
        "method": "paired resampling of calendar days, retrospective nominal interval"
    }


def run(source: Path, models: Path, markets: Path, *, expected_market_sha: str) -> tuple[dict, list[dict]]:
    if sha256(models) != MODEL_DETAILS_SHA:
        raise ValueError("phase3 frozen model details SHA mismatch")
    actual_market_sha = sha256(markets)
    if not expected_market_sha or actual_market_sha != expected_market_sha.lower():
        raise ValueError("market input must be explicitly SHA-pinned")
    details = json.loads(models.read_text(encoding="utf-8"))
    model_by_id = {int(x["match_id"]): x for x in details}
    if len(model_by_id) != len(details):
        raise ValueError("historical model duplicate match IDs")
    index = load_historical_index(source)
    counts = collections.Counter()
    rows = []
    seen_market = set()
    seen_ids = set()
    with markets.open(encoding="utf-8-sig", newline="") as file:
        for market in csv.DictReader(file):
            # Inputs outside the exact phase3 test window are not a test sample.
            if not (FIRST.isoformat() <= market.get("kickoff_utc", "")[:10] < LAST_EXCLUSIVE.isoformat()):
                continue
            counts["market_candidate_rows"] += 1
            key = market.get("id")
            if key in seen_market:
                counts["duplicate_market_id"] += 1
                continue
            seen_market.add(key)
            fixture, status = associate(market, index)
            if fixture is None:
                counts[status] += 1
                continue
            mid = fixture["match_id"]
            if mid not in model_by_id:
                counts["no_historical_model"] += 1
                continue
            if mid in seen_ids:
                counts["duplicate_model_fixture"] += 1
                continue
            market_target = market_result(market)
            if market_target is None:
                counts["missing_or_void_result"] += 1
                continue
            gh, ga = fixture["gh"], fixture["ga"]
            historical_target = 0 if gh > ga else 2 if gh < ga else 1
            if market_target != historical_target or historical_target != model_by_id[mid]["y"]:
                counts["result_conflict"] += 1
                continue
            opening = read_odds([market.get(x, "") for x in ("pin_open_home", "pin_open_draw", "pin_open_away")])
            fair = read_fair([market.get(x, "") for x in ("fair_prob_home", "fair_prob_draw", "fair_prob_away")])
            if opening is None:
                counts["missing_open_1x2"] += 1
                continue
            if fair is None:
                counts["missing_fair_1x2"] += 1
                continue
            preds = model_by_id[mid]["predictions"]
            try:
                metrics = {k: metric(v, historical_target) for k, v in {
                    "market_open": opening, "market_fair": fair, **preds
                }.items()}
            except ValueError:
                counts["invalid_model_probability"] += 1
                continue
            seen_ids.add(mid)
            counts["matched_valid_quote"] += 1
            rows.append({
                "date": model_by_id[mid]["date"], "match_id": mid,
                "league_id": fixture["league_id"], "metrics": metrics,
                "market_logloss": metrics["market_open"][0],
                "poisson_logloss": metrics.get("league_poisson", (None, None))[0],
            })

    if counts["result_conflict"] or counts["duplicate_model_fixture"] or counts["duplicate_market_id"]:
        raise ValueError("identity/result conflict or duplicated source: fail closed")
    summaries = {}
    for key in ("market_open", "market_fair", "global_frequency",
                "league_frequency", "pooled_elo_davidson", "league_poisson"):
        eligible = [r["metrics"][key] for r in rows if key in r["metrics"]]
        if eligible:
            summaries[key] = {"n": len(eligible),
                              "logloss": mean([x[0] for x in eligible]),
                              "brier3": mean([x[1] for x in eligible])}
    common = [r for r in rows if "league_poisson" in r["metrics"]
              and "pooled_elo_davidson" in r["metrics"]]
    both = {}
    for key in ("market_open", "market_fair", "league_poisson",
                "pooled_elo_davidson", "global_frequency", "league_frequency"):
        both[key] = {"n": len(common),
                     "logloss": mean([x["metrics"][key][0] for x in common]) if common else None,
                     "brier3": mean([x["metrics"][key][1] for x in common]) if common else None}
    delta = [r["market_logloss"] - r["poisson_logloss"] for r in common]
    result = {
        "task": "TASK0051", "status": "RETROSPECTIVE_EXPLORATORY_NOT_PIT",
        "study_period": [FIRST.isoformat(), (LAST_EXCLUSIVE - dt.timedelta(days=1)).isoformat()],
        "source": {"dataset": "TipsAudit public CC-BY-4.0", "url": MARKET_URL,
                   "market_sha256": actual_market_sha,
                   "phase3_model_details_sha256": sha256(models),
                   "historic_fixture_sha256": sha256(source / "fixtures.parquet")},
        "match_rules": "same normalized home and away team + same country + unique UTC kickoff within 60 min; result independently checked",
        "counts": dict(sorted(counts.items())),
        "all_matched": summaries,
        "same_poisson_elo_market_cohort": both,
        "market_open_minus_poisson_logloss": mean(delta) if delta else None,
        "paired_uncertainty": daily_paired_bootstrap(common) if common else None,
        "limitations": [
            "20-day June 2026 overlap only; 2026-06-11..2026-06-30, selected by data availability",
            "Phase3 predictions retrospectively derived from July 2026 historical snapshot; no historical PIT source attestations",
            "Market 'pin_open' may be first quote after site prediction and may be backfilled; not independently verified at same model timestamp",
            "Pinnacle/market prices are not proven executable; no bet, EV, CLV or profit calculation",
            "Market provider's own audit and record hashes are not independent timestamp certificates",
            "Strict exact-name/time matches cause selection bias; unmatched events not assumed equal",
        ],
    }
    return result, rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--history", required=True, type=Path)
    ap.add_argument("--model-details", required=True, type=Path)
    ap.add_argument("--market-csv", required=True, type=Path)
    ap.add_argument("--market-sha256", required=True)
    ap.add_argument("--out-summary", required=True, type=Path)
    ap.add_argument("--out-details", required=True, type=Path)
    args = ap.parse_args()
    for output in (args.out_summary, args.out_details):
        if output.exists():
            ap.error("never overwrite existing audit evidence")
        if output.resolve().is_relative_to(args.history.resolve()):
            ap.error("cannot write into frozen history source")
    result, rows = run(args.history, args.model_details, args.market_csv,
                       expected_market_sha=args.market_sha256)
    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    args.out_details.parent.mkdir(parents=True, exist_ok=True)
    args.out_summary.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")
    args.out_details.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
