"""Phase 3: broad, leakage-embargoed historical multi-model benchmark.

Original published HF fixture data is a retrospectively obtained historical
snapshot: this is NOT a timestamp-certified historical PIT feed. No betting
odds, market comparison, 2026-October outcomes or wager path.

Fixed, untuned models: global and league base rates, pooled Elo/Davidson,
and league-level home/away smoothed independent Poisson.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from tools.task0038_common_elo_model_gate import dav_probs, K

START = dt.date(2025, 7, 1)
TEST_START = dt.date(2026, 1, 1)
TEST_END = dt.date(2026, 7, 1)  # exclusive
SOURCE_END = dt.date(2026, 7, 5)
MIN_TEAM = 5
MIN_POSITION = 3
SHRINK_GOALS = 5.0
SHRINK_LEAGUE = 20.0
CONFIDENCE_SEED = 20261026
MODELS = ("global_frequency", "league_frequency", "pooled_elo_davidson", "league_poisson")


@dataclass(frozen=True)
class Game:
    id: int
    date: dt.date
    when: dt.datetime
    league: int
    home: int
    away: int
    gh: int
    ga: int

    @property
    def target(self) -> int:
        return 0 if self.gh > self.ga else 2 if self.gh < self.ga else 1


@dataclass(frozen=True)
class Scheduled:
    """Pre-match-only model input. Deliberately contains no results or prices."""
    league: int
    home: int
    away: int


@dataclass
class Totals:
    n: int = 0
    scored: float = 0.0
    conceded: float = 0.0

    def add(self, s: int, c: int) -> None:
        self.n += 1
        self.scored += s
        self.conceded += c


class Union:
    def __init__(self):
        self.parents: dict[int, int] = {}

    def root(self, a: int) -> int:
        if a not in self.parents:
            self.parents[a] = a
        while self.parents[a] != a:
            self.parents[a] = self.parents[self.parents[a]]
            a = self.parents[a]
        return a

    def merge(self, a: int, b: int) -> None:
        x, y = self.root(a), self.root(b)
        if x != y:
            self.parents[y] = x

    def connected(self, a: int, b: int) -> bool:
        return a in self.parents and b in self.parents and self.root(a) == self.root(b)


@dataclass
class State:
    global_result: list[int] = field(default_factory=lambda: [0, 0, 0])
    by_league: dict[int, list[int]] = field(default_factory=dict)
    elo: dict[int, float] = field(default_factory=dict)
    team_games: collections.Counter = field(default_factory=collections.Counter)
    home: dict[tuple[int, int], Totals] = field(default_factory=dict)
    away: dict[tuple[int, int], Totals] = field(default_factory=dict)
    league_home: dict[int, Totals] = field(default_factory=dict)
    league_away: dict[int, Totals] = field(default_factory=dict)
    graph: Union = field(default_factory=Union)
    trained_game_count: int = 0
    last_training_date: dt.date | None = None

    def add_training(self, game: Game) -> None:
        self.global_result[game.target] += 1
        self.by_league.setdefault(game.league, [0, 0, 0])[game.target] += 1
        eh = self.elo.get(game.home, 1500.0)
        ea = self.elo.get(game.away, 1500.0)
        p = dav_probs(eh, ea)
        expected = p[0] + 0.5 * p[1]
        actual = 1.0 if game.target == 0 else 0.5 if game.target == 1 else 0.0
        shift = K * (actual - expected)
        self.elo[game.home] = eh + shift
        self.elo[game.away] = ea - shift
        self.team_games[game.home] += 1
        self.team_games[game.away] += 1
        self.graph.merge(game.home, game.away)
        self.home.setdefault((game.league, game.home), Totals()).add(game.gh, game.ga)
        self.away.setdefault((game.league, game.away), Totals()).add(game.ga, game.gh)
        self.league_home.setdefault(game.league, Totals()).add(game.gh, game.ga)
        self.league_away.setdefault(game.league, Totals()).add(game.ga, game.gh)
        self.trained_game_count += 1
        self.last_training_date = game.date

    def predict(self, game: Game | Scheduled) -> dict[str, list[float]]:
        base = self.global_result
        prior = [(x + 1.0) / (sum(base) + 3) for x in base]
        predictions = {"global_frequency": prior}
        lg = self.by_league.get(game.league, [0, 0, 0])
        n = sum(lg)
        predictions["league_frequency"] = [
            (lg[i] + SHRINK_LEAGUE * prior[i]) / (n + SHRINK_LEAGUE)
            for i in range(3)
        ]
        eligible = (self.team_games[game.home] >= MIN_TEAM
                    and self.team_games[game.away] >= MIN_TEAM
                    and self.graph.connected(game.home, game.away))
        if eligible:
            predictions["pooled_elo_davidson"] = dav_probs(
                self.elo[game.home], self.elo[game.away])
        h = self.home.get((game.league, game.home), Totals())
        a = self.away.get((game.league, game.away), Totals())
        lg_h = self.league_home.get(game.league, Totals())
        lg_a = self.league_away.get(game.league, Totals())
        if eligible and h.n >= MIN_POSITION and a.n >= MIN_POSITION and lg_h.n >= 25:
            mu_h = (lg_h.scored + SHRINK_LEAGUE * 1.35) / (lg_h.n + SHRINK_LEAGUE)
            mu_a = (lg_a.scored + SHRINK_LEAGUE * 1.10) / (lg_a.n + SHRINK_LEAGUE)
            ha = (h.scored + SHRINK_GOALS * mu_h) / (h.n + SHRINK_GOALS)
            ad = (a.conceded + SHRINK_GOALS * mu_h) / (a.n + SHRINK_GOALS)
            aa = (a.scored + SHRINK_GOALS * mu_a) / (a.n + SHRINK_GOALS)
            hd = (h.conceded + SHRINK_GOALS * mu_a) / (h.n + SHRINK_GOALS)
            goals_h = min(5.0, max(0.2, ha * ad / mu_h))
            goals_a = min(5.0, max(0.2, aa * hd / mu_a))
            predictions["league_poisson"] = poisson_1x2(goals_h, goals_a)
        return predictions


def poisson_1x2(h: float, a: float) -> list[float]:
    if not (0 < h <= 5 and 0 < a <= 5):
        raise ValueError("unsafe Poisson rates")
    def pmf(mean: float) -> list[float]:
        r = [math.exp(-mean)]
        for n in range(1, 21):
            r.append(r[-1] * mean / n)
        return r
    hp, ap = pmf(h), pmf(a)
    win, draw, lose = 0.0, 0.0, 0.0
    for i, x in enumerate(hp):
        for j, y in enumerate(ap):
            if i > j:
                win += x*y
            elif i == j:
                draw += x*y
            else:
                lose += x*y
    total = win + draw + lose
    return [win/total, draw/total, lose/total]


def deduplicate(games: list[Game]) -> tuple[list[Game], int]:
    seen = {}
    repeated = 0
    ids = {}
    for g in games:
        if g.date != g.when.date() or not (START <= g.date < SOURCE_END):
            raise ValueError("unexpected fixture period")
        if g.home == g.away or min(g.gh, g.ga) < 0:
            raise ValueError("invalid fixture goals or team IDs")
        old_id = ids.get(g.id)
        if old_id and (old_id.when, old_id.home, old_id.away, old_id.gh, old_id.ga) != (
            g.when, g.home, g.away, g.gh, g.ga
        ):
            raise ValueError("same provider row ID with conflicting match facts")
        ids[g.id] = g
        key = (g.when, g.home, g.away)
        prior = seen.get(key)
        if prior:
            if (prior.gh, prior.ga) != (g.gh, g.ga):
                raise ValueError("duplicate fixture key has conflicting final scores")
            repeated += 1
            if g.id < prior.id:
                seen[key] = g
        else:
            seen[key] = g
    return sorted(seen.values(), key=lambda g: (g.when, g.id)), repeated


def _metric(probabilities: list[list[float]], labels: list[int]) -> dict | None:
    if not probabilities:
        return None
    n = len(labels)
    ll = sum(-math.log(max(p[y], 1e-15)) for p, y in zip(probabilities, labels))
    bs = sum(sum((p[i] - (i == y))**2 for i in range(3))
             for p, y in zip(probabilities, labels))
    hit = sum(max(range(3), key=lambda i: p[i]) == y
              for p, y in zip(probabilities, labels))
    return {"n": n, "logloss": ll/n, "brier3": bs/n, "accuracy": hit/n}


def _date_cluster_delta(paired: list[dict], challenger: str,
                        draws: int = 1000) -> dict | None:
    byday: dict[str, tuple[float, int]] = {}
    for r in paired:
        if challenger not in r["predictions"]:
            continue
        day = r["date"]
        y = r["y"]
        delta = -math.log(r["predictions"][challenger][y]) + math.log(
            r["predictions"]["global_frequency"][y])
        previous, n = byday.get(day, (0.0, 0))
        byday[day] = (previous + delta, n + 1)
    if len(byday) < 5:
        return None
    values = list(byday.values())
    all_n = sum(v[1] for v in values)
    effect = sum(v[0] for v in values) / all_n
    rng = random.Random(CONFIDENCE_SEED)
    boots = []
    for _ in range(draws):
        selected = [values[rng.randrange(len(values))] for _ in values]
        boots.append(sum(v[0] for v in selected) / sum(v[1] for v in selected))
    boots.sort()
    return {"delta_logloss_vs_global": effect, "dates": len(values),
            "nominal_day_cluster_95": [boots[int(.025*draws)],
                                        boots[int(.975*draws)-1]]}


def evaluate(games: list[Game], *, sample_limit: int | None = None) -> dict:
    frozen, duplicates = deduplicate(games)
    train = State()
    byday = collections.defaultdict(list)
    for game in frozen:
        byday[game.date].append(game)
    dates = sorted(byday)
    k = 0
    current = []
    prediction_rows = []
    exclusions = collections.Counter()
    earliest_training_constraint = None
    for day in dates:
        if day < TEST_START or day >= TEST_END:
            continue
        # One COMPLETE UTC calendar day embargo: excludes same day and previous UTC date.
        cutoff = day - dt.timedelta(days=2)
        while k < len(dates) and dates[k] <= cutoff:
            for game in byday[dates[k]]:
                train.add_training(game)
            k += 1
        if train.last_training_date is not None and train.last_training_date > cutoff:
            raise AssertionError("train/test date fence broken")
        earliest_training_constraint = str(train.last_training_date) if earliest_training_constraint is None else earliest_training_constraint
        for game in byday[day]:
            predictions = train.predict(game)
            if not (0 < min(predictions["global_frequency"]) <= 1):
                raise AssertionError("improper baseline probability")
            for name, values in predictions.items():
                if (len(values) != 3 or any(not math.isfinite(v) or v <= 0 for v in values)
                        or abs(sum(values)-1) > 1e-9):
                    raise AssertionError("invalid model probability")
            if "pooled_elo_davidson" not in predictions:
                exclusions["elo_missing_prior_or_connection"] += 1
            if "league_poisson" not in predictions:
                exclusions["poisson_missing_league_home_away_history"] += 1
            prediction_rows.append({
                "date": day.isoformat(), "match_id": game.id,
                "league_id": game.league, "y": game.target,
                "predictions": predictions,
                "max_allowed_training_date": cutoff.isoformat(),
                "last_actual_training_date": train.last_training_date.isoformat()
                    if train.last_training_date else None,
            })
            if sample_limit and len(prediction_rows) >= sample_limit:
                break
        if sample_limit and len(prediction_rows) >= sample_limit:
            break

    metric = {}
    compare = {}
    for name in MODELS:
        eligible = [r for r in prediction_rows if name in r["predictions"]]
        metric[name] = _metric([r["predictions"][name] for r in eligible],
                               [r["y"] for r in eligible])
        if name != "global_frequency":
            compare[name] = {
                "matched_global": _metric(
                    [r["predictions"]["global_frequency"] for r in eligible],
                    [r["y"] for r in eligible]),
                "paired_delta": _date_cluster_delta(eligible, name),
            }
    return {
        "schema_version": 1, "source_type": "retrospective historical snapshot NOT PIT",
        "market_odds_used": False, "wagers_executed": False,
        "model_hyperparameters_selected_on_holdout": False,
        "train_start": START.isoformat(), "test_start": TEST_START.isoformat(),
        "test_end_exclusive": TEST_END.isoformat(), "source_end_exclusive": SOURCE_END.isoformat(),
        "prior_day_embargo": "Train on UTC dates <= test UTC date minus 2 days",
        "params": {"elo_k": K, "elo_home": 50.0, "elo_draw_weight": .7,
                   "league_prior": SHRINK_LEAGUE, "poisson_prior_games": SHRINK_GOALS,
                   "min_connected_team_matches": MIN_TEAM,
                   "min_position_games": MIN_POSITION},
        "input_rows": len(games), "deduplicated_rows": len(frozen),
        "removed_identical_duplicates": duplicates,
        "test_rows": len(prediction_rows), "tested_dates": len(set(r["date"] for r in prediction_rows)),
        "training_rows_as_of_last_test": train.trained_game_count,
        "train_latest_date_as_of_last_test": str(train.last_training_date),
        "earliest_test_prior_train_date": earliest_training_constraint,
        "exclusions": dict(exclusions), "model_metrics": metric,
        "matched_baseline_comparison": compare,
        "details": prediction_rows,
    }


def read_source(source: Path) -> tuple[list[Game], dict]:
    import duckdb
    manifest = json.loads((source / "hf_manifest.json").read_text(encoding="utf8"))
    for item in manifest:
        file = source / item["file"]
        if hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("historical source SHA256 mismatch: " + item["file"])
    fixture = source / "fixtures.parquet"
    con = duckdb.connect()
    try:
        data = con.execute("""
            SELECT id, date_utc, league_id, home_team_id, away_team_id, goals_home, goals_away
            FROM read_parquet(?)
            WHERE is_played=true AND date_utc >= TIMESTAMP '2025-07-01'
              AND date_utc < TIMESTAMP '2026-07-05'
              AND league_id IS NOT NULL AND home_team_id IS NOT NULL
              AND away_team_id IS NOT NULL AND goals_home IS NOT NULL
              AND goals_away IS NOT NULL
            ORDER BY date_utc, id
        """, [str(fixture)]).fetchall()
    finally:
        con.close()
    games = [Game(int(x[0]), x[1].date(), x[1], *map(int, x[2:])) for x in data]
    return games, {"source_fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
                   "source_manifest_sha256": hashlib.sha256(
                       (source/"hf_manifest.json").read_bytes()).hexdigest()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out-summary", type=Path, required=True)
    ap.add_argument("--out-details", type=Path, required=True)
    args = ap.parse_args()
    if args.out_summary.exists() or args.out_details.exists():
        ap.error("refusing to replace existing evidence")
    if args.out_summary.resolve() == args.out_details.resolve():
        ap.error("summary/details may not point to the same file")
    games, sha = read_source(args.source)
    result = evaluate(games)
    details = result.pop("details")
    result.update(sha)
    summary = args.out_summary.resolve()
    detail_path = args.out_details.resolve()
    summary.parent.mkdir(parents=True, exist_ok=True)
    detail_path.parent.mkdir(parents=True, exist_ok=True)
    # Both derivative outputs are written into new isolated off-repo evidence directories.
    with summary.open("x", encoding="utf8") as f:
        json.dump(result, f, indent=2)
    with detail_path.open("x", encoding="utf8") as f:
        json.dump(details, f)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
