"""Fail-closed real prospective international 1X2 same-time quote validator.

Input is an externally collected, unmodified The Odds API-style JSON response,
the *independently collected* raw HTTP receipt and separately QA-approved
event/club identity bridge. Missing any of them => no market admission.

The quote must have been captured, source-Git-anchored, updated and readable
BEFORE model freeze, with a bounded age. Historical CSV "open"/"close" labels
and postmatch web pages are NEVER contemporaneous market observations.

No source is fetched here; source owners' licensing/API keys remain external.
No market odds feed into the football model, no wager/EV is produced.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

UTC = dt.timezone.utc
MAX_CAPTURE_TO_FREEZE_SECONDS = 10 * 60
MAX_BOOK_UPDATE_TO_FREEZE_SECONDS = 15 * 60
MAX_KICKOFF_DIFF_SECONDS = 15 * 60
MIN_FREEZE_TO_KICKOFF_SECONDS = 60 * 60


class RejectedEvidence(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def aware(text):
    try:
        value = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (AttributeError, ValueError, TypeError) as err:
        raise RejectedEvidence("TIMESTAMP_INVALID") from err
    if value.utcoffset() is None:
        raise RejectedEvidence("TIMESTAMP_NAIVE")
    return value.astimezone(UTC)


def reject_if(condition, reason):
    if condition:
        raise RejectedEvidence(reason)


def evaluate(ledger: dict, candidate: dict, raw_bytes: bytes | None) -> dict:
    """Admit at most one specific bookmaker's full-time pre-match 1X2 book."""
    reject_if(ledger.get("record_schema") != "EVLAB_TASK0046_FORWARD_V1",
              "MODEL_NOT_GIT_ANCHORED_FORWARD_LEDGER")
    reject_if(ledger.get("status") != "PRE_KICKOFF_FROZEN_RESEARCH_ONLY",
              "MODEL_UNQUALIFIED")
    reject_if(ledger.get("market_quote_status") != "UNVERIFIED_NOT_INCLUDED"
              or ledger.get("market_odds") is not None,
              "FORECAST_CONTAMINATED_BY_MARKET_INPUT")
    reject_if(not isinstance(ledger.get("predictions"), list),
              "MODEL_PREDICTIONS_MISSING")
    matches = [p for p in ledger["predictions"]
               if str(p["matchId"]) == str(candidate.get("official_match_id"))]
    reject_if(len(matches) != 1, "NO_UNIQUE_GIT_PREMATCH_FIXTURE")
    model = matches[0]
    freeze = aware(ledger["frozen_at_utc"])
    kickoff = aware(model["kickoff_utc"])
    reject_if((kickoff - freeze).total_seconds() < MIN_FREEZE_TO_KICKOFF_SECONDS,
              "MODEL_FREEZE_TOO_CLOSE_TO_KICKOFF")

    bridge = candidate.get("identity_bridge") or {}
    # Quarantine both single-side inference and fuzzy alias candidates. Every
    # accepted fixture must have independently vetted two-side ID provenance.
    reject_if(bridge.get("status") != "INDEPENDENT_TWO_SIDE_EVENT_ACCEPTED"
              or not bridge.get("evidence_sha256")
              or len(str(bridge["evidence_sha256"])) != 64,
              "CROSS_PROVIDER_IDENTITY_NOT_INDEPENDENTLY_APPROVED")
    for source_field, model_field in (
        ("official_match_id", "matchId"),
        ("hf_home_id", "hf_home_id"),
        ("hf_away_id", "hf_away_id"),
        ("official_home_id", "official_home_id"),
        ("official_away_id", "official_away_id"),
        ("league_zh", "league"),
    ):
        reject_if(str(bridge.get(source_field)) != str(model.get(model_field)),
                  "SOURCE_EVENT_HOME_AWAY_LEAGUE_CONFLICT")
    reject_if(abs((aware(bridge["kickoff_utc"]) - kickoff).total_seconds()) >
              MAX_KICKOFF_DIFF_SECONDS, "EVENT_KICKOFF_TIME_CONFLICT")
    reject_if(str(bridge.get("provider_event_id")) !=
              str(candidate.get("provider_event_id")),
              "INDEPENDENT_PROVIDER_EVENT_ID_MISMATCH")

    receipt = candidate.get("receipt") or {}
    reject_if(raw_bytes is None, "RAW_MARKET_RESPONSE_NOT_PRESERVED")
    reject_if(receipt.get("http_status") != 200
              or receipt.get("source_provider") != "the-odds-api"
              or not str(receipt.get("source_url", "")).startswith(
                  "https://api.the-odds-api.com/v4/"),
              "PROVIDER_RESPONSE_NOT_VERIFIED")
    if hashlib.sha256(raw_bytes).hexdigest() != receipt.get("raw_sha256"):
        raise RejectedEvidence("MARKET_RAW_SOURCE_SHA_MISMATCH")
    seen = aware(receipt["first_received_utc"])
    anchored = aware(receipt["git_anchor_time_utc"])
    reject_if(anchored < seen or anchored > freeze, "MARKET_CAPTURE_NOT_GIT_ANCHORED_BEFORE_MODEL")
    reject_if(seen > freeze, "MARKET_CAPTURE_AFTER_MODEL_FREEZE")
    reject_if(not 0 <= (freeze - seen).total_seconds() <=
              MAX_CAPTURE_TO_FREEZE_SECONDS,
              "MARKET_QUOTE_NOT_AT_MODEL_TIME")

    try:
        doc = json.loads(raw_bytes)
    except (TypeError, UnicodeError, ValueError) as err:
        raise RejectedEvidence("MARKET_RESPONSE_NOT_JSON") from err
    reject_if(not isinstance(doc, list), "MARKET_RESPONSE_NOT_EVENT_LIST")
    items = [e for e in doc if str(e.get("id")) ==
             str(candidate["provider_event_id"])]
    reject_if(len(items) != 1, "NO_UNIQUE_MARKET_EVENT")
    event = items[0]
    reject_if(str(event.get("sport_key")) != str(candidate.get("sport_key")),
              "PROVIDER_LEAGUE_SPORT_MISMATCH")
    reject_if(abs((aware(event["commence_time"]) - kickoff).total_seconds()) >
              MAX_KICKOFF_DIFF_SECONDS, "MARKET_KICKOFF_MISMATCH")
    reject_if((event.get("home_team"), event.get("away_team")) !=
              (bridge.get("provider_home_team"), bridge.get("provider_away_team")),
              "MARKET_HOME_AWAY_REVERSED_OR_UNKNOWN")
    books = [b for b in event.get("bookmakers", [])
             if b.get("key") == candidate.get("bookmaker_key")]
    reject_if(len(books) != 1, "BOOKMAKER_NOT_UNIQUE_OR_MISSING")
    book = books[0]
    markets = [m for m in book.get("markets", []) if m.get("key") == "h2h"]
    reject_if(len(markets) != 1 or candidate.get("period") != "FULL_TIME_90"
              or candidate.get("market_key") != "h2h",
              "NOT_FULL_TIME_1X2_MARKET")
    market = markets[0]
    book_update = aware(market.get("last_update", book.get("last_update")))
    reject_if(book_update > seen, "QUOTE_LAST_UPDATE_AFTER_CAPTURE")
    reject_if(not 0 <= (freeze - book_update).total_seconds() <=
              MAX_BOOK_UPDATE_TO_FREEZE_SECONDS,
              "BOOKMAKER_PRICE_STALE_AT_MODEL_TIME")
    outcome = {}
    for x in market.get("outcomes", []):
        key = x.get("name")
        reject_if(key in outcome, "DUPLICATE_MARKET_OUTCOME")
        outcome[key] = x.get("price")
    labels = (event["home_team"], "Draw", event["away_team"])
    reject_if(set(outcome) != set(labels) or len(outcome) != 3,
              "INCOMPLETE_OR_MISLABELED_1X2")
    try:
        prices = [float(outcome[k]) for k in labels]
    except (TypeError, ValueError) as err:
        raise RejectedEvidence("INVALID_MARKET_ODDS") from err
    reject_if(any(not math.isfinite(x) or x <= 1.001 or x >= 500
                  for x in prices), "INVALID_MARKET_ODDS")
    inv = [1/x for x in prices]
    margin = sum(inv) - 1
    reject_if(not -0.05 < margin < 0.40, "MARKET_OVERROUND_OUT_OF_RANGE")
    fair = [x/sum(inv) for x in inv]
    return {
        "status": "SAME_MATCH_SAME_TIME_SOURCE_GATE_ACCEPTED_NOT_PROFIT",
        "official_match_id": str(model["matchId"]),
        "provider_event_id": str(event["id"]),
        "bookmaker_key": book["key"], "market_key": "h2h",
        "period": "FULL_TIME_90",
        "model_frozen_at_utc": freeze.isoformat(),
        "quote_received_utc": seen.isoformat(),
        "bookmaker_last_update_utc": book_update.isoformat(),
        "kickoff_utc": kickoff.isoformat(),
        "model_hf_home_id": model["hf_home_id"],
        "model_hf_away_id": model["hf_away_id"],
        "quote_raw_sha256": receipt["raw_sha256"],
        "independent_event_bridge_sha256": bridge["evidence_sha256"],
        "odds_home_draw_away": prices, "overround": margin,
        "devigged_market_1x2": fair,
        "not_tradeable_profit_or_CLV_proof": True,
    }


def audit(ledger_path: Path, candidates_path: Path, raw_root: Path):
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    if not isinstance(candidates, list):
        raise ValueError("candidate receipt array expected")
    responses = []
    for candidate in candidates:
        loc = candidate.get("receipt", {}).get("relative_raw_path")
        raw = None
        if loc:
            path = (raw_root / loc).resolve()
            if not path.is_relative_to(raw_root.resolve()):
                raise ValueError("raw response path traversal")
            if path.is_file():
                raw = path.read_bytes()
        try:
            result = evaluate(ledger, candidate, raw)
        except (RejectedEvidence, KeyError, TypeError, ValueError) as err:
            result = {
                "status": "REJECTED_UNVERIFIED_SAME_TIME_MARKET",
                "official_match_id": str(candidate.get("official_match_id", "")),
                "provider_event_id": str(candidate.get("provider_event_id", "")),
                "reason": err.reason if isinstance(err, RejectedEvidence)
                else "INVALID_SOURCE_EVIDENCE_SCHEMA",
            }
        responses.append(result)
    return {
        "task": "TASK0061", "stage": "INDEPENDENT_SAME_TIME_1X2_GATE",
        "source_model_ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        "candidates_seen": len(responses),
        "contemporaneous_markets_accepted": sum(
            z["status"].startswith("SAME_MATCH_SAME_TIME_SOURCE_GATE_ACCEPTED")
            for z in responses),
        "results": responses, "no_bet_no_model_selection_no_EV": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("ledger", "candidates", "raw-root", "out"):
        parser.add_argument("--"+key, dest=key.replace("-", "_"),
                            type=Path, required=True)
    args = parser.parse_args()
    summary = audit(args.ledger, args.candidates, args.raw_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({
        "candidates_seen": summary["candidates_seen"],
        "accepted": summary["contemporaneous_markets_accepted"],
        "reasons": [x.get("reason", "ACCEPT")
                    for x in summary["results"]],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
