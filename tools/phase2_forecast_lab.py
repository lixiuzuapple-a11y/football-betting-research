"""EV-Lab phase 2: real-time pre-kickoff independent-baseline freeze, then blind scoring.

The official final-score snapshot is used only as HISTORICAL LABELS, never
as future fixture scores. Market quote inputs are never given to predictor.
New freezes are create-only. No BUY, bankroll, CLV or executable odds claim.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

# Executable from a clean source checkout without requiring pip install -e .
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from football_betting.domain.models import Match
from football_betting.features.build import FeatureSet
from football_betting.models.base import PredictionRequest
from football_betting.models.observed_frequency import ObservedFrequencyPredictor
from football_betting.evaluation.metrics import log_loss, brier_score, accuracy
from tools.task0040_new_window_gate import validate_source, classify_one
from tools.task0031_actual_scoring import parse

UTC = dt.timezone.utc
BEIJING = dt.timezone(dt.timedelta(hours=8))


def load_prior_official_results(path: Path, *, before: dt.datetime) -> tuple[tuple[int, int, int], str, str]:
    raw = path.read_bytes()
    rows = json.loads(raw)
    if not isinstance(rows, list) or not rows:
        raise ValueError("official prior label snapshot must be a nonempty list")
    counts = [0, 0, 0]
    seen = set()
    max_date = ""
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("bad result evidence row")
        mid = str(row["matchId"])
        if mid in seen:
            raise ValueError("duplicate historical result matchId")
        seen.add(mid)
        if row.get("source") != "sporttery_official_result_api" or str(row.get("matchResultStatus")) != "2":
            raise ValueError("unverified prior official result source/status")
        if str(row.get("homeTeamId")) == str(row.get("awayTeamId")):
            raise ValueError("invalid prior result identity")
        date = str(row["matchDate"])
        if len(date) != 10:
            raise ValueError("bad prior date")
        day = dt.date.fromisoformat(date)
        # Must be strictly before the current Beijing calendar date, not just before a kick-off time.
        if day >= before.astimezone(BEIJING).date():
            raise ValueError("training includes today's or future matches")
        score = row["score"]
        if (not isinstance(score, list) or len(score) != 2
                or any(type(x) is not int or x < 0 for x in score)
                or str(row.get("sectionsNo999")) != f"{score[0]}:{score[1]}"):
            raise ValueError("invalid result label or score conflict")
        counts[0 if score[0] > score[1] else 2 if score[0] < score[1] else 1] += 1
        max_date = max(max_date, date)
    return tuple(counts), hashlib.sha256(raw).hexdigest(), max_date


def build_forecast(*, labels: Path, quote_manifest: Path, at: dt.datetime | None = None) -> dict[str, Any]:
    at = at or dt.datetime.now(UTC)
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("freeze time must be timezone-aware")
    at = at.astimezone(UTC)
    counts, source_hash, last_date = load_prior_official_results(labels, before=at)
    predictor = ObservedFrequencyPredictor(counts, source_hash, last_date, trained_as_of=at)
    manifest, matches, start, response = validate_source(quote_manifest)
    if response > at:
        raise ValueError("quote capture not yet observed at freeze")
    if response <= start or (at-response)>dt.timedelta(hours=24):
        raise ValueError("market response arrived too long ago or at invalid time")
    snap_sha = hashlib.sha256(Path(quote_manifest).read_bytes()).hexdigest()
    frozen = []
    for raw in matches:
        item = classify_one(raw, start, response)
        kickoff = parse(item["kickoff_bjt"])
        if not kickoff or kickoff <= at:
            # Do not backdate a prediction for a game that started already.
            raise ValueError("freeze requested at/after target kickoff")
        match = Match(
            match_id=item["matchId"], league=str(item.get("league") or "unlabelled"),
            season=str(kickoff.year), kickoff_at=kickoff,
            home_team_id=item["official_home_team_id"],
            away_team_id=item["official_away_team_id"],
        )
        features = FeatureSet(match.match_id, at, "prior-outcomes-only-v1", {
            "prior_counts": counts, "training_raw_sha256": source_hash,
        })
        request = PredictionRequest(match, features, at, at, source_hash)
        pred = predictor.predict(request)
        market = item.get("frozen_had_fair_market_probabilities")
        frozen.append({
            "matchId": match.match_id,
            "league": match.league,
            "kickoff_utc": kickoff.astimezone(UTC).isoformat(),
            "homeTeamId": match.home_team_id, "awayTeamId": match.away_team_id,
            "independent_prediction_id": pred.prediction_id,
            "independent_model": pred.model_version,
            "independent_1x2": list(pred.probabilities()),
            "market_1x2": market if market is not None else None,
            "market_raw_decimal_odds": item.get("frozen_had_odds"),
            "market_received_utc": response.isoformat(),
            "market_provider_updated_bjt": item.get("provider_had_updated_at_bjt"),
            "market_rejection_reasons": item["rejection_reasons"],
            "market_quote_is_not_executable": True,
        })
    return {
        "schema_version": 1, "phase": "FORWARD_BASELINE_FROZEN",
        "created_at_utc": at.isoformat(),
        "source_manifest_sha256": snap_sha,
        "source_raw_sha256": manifest["sha256"],
        "labels_sha256": source_hash, "labels_count": sum(counts),
        "labels_last_match_date": last_date, "training_counts_1x2": list(counts),
        "training_source": "verified official historical result snapshot",
        "model": predictor.version,
        "model_input_market_odds": False,
        "market_is_comparison_only": True,
        "no_future_results_joined": True,
        "no_buy_or_wager": True,
        "fixtures": frozen,
    }


def score_frozen(frozen: dict, result_rows: list[dict], *, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(UTC)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("scoring time missing timezone")
    seen = set()
    byid = {}
    for row in result_rows:
        mid = str(row["matchId"])
        if mid in seen:
            raise ValueError("duplicate official result id")
        seen.add(mid)
        byid[mid] = row
    model = []
    market = []
    y = []
    scored = []
    for rec in frozen["fixtures"]:
        match_id = rec["matchId"]
        row = byid.get(match_id)
        if row is None:
            continue
        kickoff = dt.datetime.fromisoformat(rec["kickoff_utc"])
        created = dt.datetime.fromisoformat(frozen["created_at_utc"])
        if now <= kickoff or created >= kickoff:
            raise ValueError("cannot score match before kickoff / invalid frozen prediction")
        if str(row.get("source")) != "sporttery_official_result_api" or str(row.get("matchResultStatus")) != "2":
            raise ValueError("unverified future result")
        if (str(row.get("homeTeamId")) != rec["homeTeamId"]
                or str(row.get("awayTeamId")) != rec["awayTeamId"]
                or str(row.get("matchDate")) != kickoff.astimezone(BEIJING).date().isoformat()):
            raise ValueError("future fixture identity conflict")
        h, a = row["score"]
        if (any(type(n) is not int or n < 0 for n in (h, a))
                or str(row.get("sectionsNo999")) != f"{h}:{a}"):
            raise ValueError("invalid future result score")
        target = 0 if h>a else 2 if h<a else 1
        model.append(rec["independent_1x2"])
        y.append(target)
        if rec["market_1x2"] is not None:
            market.append((rec["market_1x2"], target))
        scored.append(match_id)
    result = {
        "n": len(scored), "scored_match_ids": scored,
        "independent": {
            "logloss": log_loss(model, y), "brier3": brier_score(model, y),
            "accuracy": accuracy(model, y),
        } if scored else None,
        "market_n": len(market),
        "market": {
            "logloss": log_loss([p for p, _ in market], [y for _, y in market]),
            "brier3": brier_score([p for p, _ in market], [y for _, y in market]),
            "accuracy": accuracy([p for p, _ in market], [y for _, y in market]),
        } if market else None,
        "no_executable_odds_or_profit_claim": True,
    }
    return result


def _create_only(path: Path, data: dict) -> str:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as out:
        out.write(encoded)
        out.flush()
        os.fsync(out.fileno())
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="cmd", required=True)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--historical-labels", required=True, type=Path)
    freeze.add_argument("--quote-manifest", required=True, type=Path)
    freeze.add_argument("--out", required=True, type=Path)
    scorer = commands.add_parser("score")
    scorer.add_argument("--frozen", required=True, type=Path)
    scorer.add_argument("--official-results", required=True, type=Path)
    scorer.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.cmd == "freeze":
        result = build_forecast(labels=args.historical_labels, quote_manifest=args.quote_manifest)
    else:
        frozen = json.loads(args.frozen.read_text(encoding="utf8"))
        rows = json.loads(args.official_results.read_text(encoding="utf8"))
        result = score_frozen(frozen, rows)
    digest = _create_only(args.out, result)
    print(json.dumps({"status": "recorded", "sha256": digest, "out": str(args.out),
                      "fixtures": len(result.get("fixtures", [])), "scored": result.get("n")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
