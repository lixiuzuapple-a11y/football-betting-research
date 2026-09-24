"""Unattended prospective collector for TASK-0005.

What it does, once every ~60 seconds, start-to-start:

1. Fires the two regular legs **concurrently**:
   - Sporttery official ``getMatchCalculatorV1.qry`` (HAD focus);
   - BetExplorer homepage (``reference_proxy``).
2. Records, per leg, ``request_started_at`` / ``response_received_at`` /
   ``latency_ms`` separately and persists the raw bytes with their SHA-256.
3. Compares each BetExplorer fixture's 1X2 tuple against the last successful
   observation of that same ``event_id``. On any change it immediately fires
   **one** extra Sporttery confirmation capture, tagged
   ``change_confirmation``.
4. Never overlaps two regular rounds. If a round runs long, the next round
   starts after the previous finishes and the scheduler lag is recorded.

What it deliberately does not do (TASK-0005 §14): no EV, no ROI, no threshold
tuning, no BUY/PASS, no model fitting, no profitability claim. It observes and
records.

Timing discipline (TASK-0005 §5) is the part most worth protecting:
a response that took 45 seconds is not known at request start, so the collector
never reports a quote as knowable before it actually arrived.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from football_betting.data.betexplorer import (
    BETEXPLORER_HOME_URL,
    build_home_request,
    parse_homepage,
)
from football_betting.data.sporttery_webapi import (
    MATCH_CALCULATOR_URL,
    looks_like_challenge,
    parse_match_calculator,
)
from football_betting.data.sporttery_webapi import (
    build_request as build_sporttery_request,
)

from .ledger import (
    CAPTURE_KIND_CHANGE_CONFIRMATION,
    CAPTURE_KIND_REGULAR,
    SOURCE_OFFICIAL_SPORTTERY,
    SOURCE_REFERENCE_BETEXPLORER,
    CaptureRecord,
    LedgerStore,
)

__all__ = ["CollectorConfig", "ProspectiveCollector", "run_forever"]

LOGGER = logging.getLogger("task0005.collector")

ROUND_INTERVAL_SECONDS = 60.0
HTTP_TIMEOUT_SECONDS = 50.0
#: Bounded backoff for transient failures. Capped so a persistent outage does
#: not turn into a tight retry loop (TASK-0005 §9).
BACKOFF_STEPS_SECONDS = (5.0, 15.0, 45.0, 90.0)


@dataclass(frozen=True, slots=True)
class CollectorConfig:
    """Runtime configuration. Defaults match the TASK-0005 contract."""

    data_root: str
    deployed_commit: str = "unknown"
    round_interval_seconds: float = ROUND_INTERVAL_SECONDS
    http_timeout_seconds: float = HTTP_TIMEOUT_SECONDS
    betexplorer_url: str = BETEXPLORER_HOME_URL
    sporttery_url: str = MATCH_CALCULATOR_URL
    max_rounds: int | None = None
    parser_version: str = "task0005-collector/0.1"


@dataclass(frozen=True, slots=True)
class LegOutcome:
    """The result of one HTTP leg, with both clocks preserved."""

    source: str
    request_started_at: datetime
    response_received_at: datetime
    latency_ms: float
    http_status: int | None
    failure_class: str | None
    raw: bytes | None
    text: str | None


class ProspectiveCollector:
    """Runs the dual-leg loop and writes only to the append-only ledger."""

    def __init__(self, config: CollectorConfig, *, store: LedgerStore | None = None) -> None:
        self.config = config
        self.store = store or LedgerStore(config.data_root, deployed_commit=config.deployed_commit)
        #: Last successful BetExplorer observation per event, for change detection.
        self._last_reference: dict[str, tuple[tuple[float, float, float], datetime]] = {}
        self._round_index = 0
        self._stop = threading.Event()

    @property
    def _commit(self) -> str:
        """The commit recorded on every capture row.

        The store is authoritative: it is created with the commit the deployment
        actually pinned, so a config default can never silently downgrade the
        provenance of a row.
        """
        return self.store.deployed_commit or self.config.deployed_commit

    # -- HTTP ---------------------------------------------------------------

    def _fetch(self, source: str, request: urllib.request.Request) -> LegOutcome:
        """Perform one request, keeping both clocks and never inventing times."""
        started = datetime.now(timezone.utc)
        status: int | None = None
        failure: str | None = None
        raw: bytes | None = None

        try:
            with urllib.request.urlopen(  # noqa: S310 - fixed endpoints
                request, timeout=self.config.http_timeout_seconds
            ) as response:
                raw = response.read()
                status = int(response.status)
        except urllib.error.HTTPError as exc:
            failure = f"http_error_{exc.code}"
            status = int(exc.code)
            # An error body is evidence too: TASK-0005 §7 requires the raw hash
            # to survive even when parsing fails, so the challenge page is kept.
            try:
                raw = exc.read()
            except Exception:  # noqa: BLE001 - body may be unreadable
                raw = None
        except (urllib.error.URLError, TimeoutError) as exc:
            failure = "transport_error"
            LOGGER.warning("%s transport error: %s", source, exc)
        except OSError as exc:  # pragma: no cover - environment specific
            failure = "os_error"
            LOGGER.warning("%s os error: %s", source, exc)

        received = datetime.now(timezone.utc)
        text = raw.decode("utf-8", "replace") if raw is not None else None

        # A 200 that is actually a challenge page is a failure, not data.
        if (
            failure is None
            and source == SOURCE_OFFICIAL_SPORTTERY
            and text is not None
            and looks_like_challenge(text)
        ):
            failure = "access_control_challenge"

        return LegOutcome(
            source=source,
            request_started_at=started,
            response_received_at=received,
            latency_ms=(received - started).total_seconds() * 1000.0,
            http_status=status,
            failure_class=failure,
            raw=raw,
            text=text,
        )

    def _persist_leg(self, outcome: LegOutcome, *, round_id: str, kind: str,
                     change_event_id: str | None = None) -> int:
        """Write the capture row plus its raw bytes. Returns the capture id."""
        digest: str | None = None
        rel_path: str | None = None
        if outcome.raw:
            suffix = "json" if outcome.source == SOURCE_OFFICIAL_SPORTTERY else "html"
            digest, rel_path = self.store.persist_raw(
                outcome.raw,
                source=outcome.source,
                observed_at=outcome.response_received_at,
                suffix=suffix,
            )

        record = CaptureRecord(
            round_id=round_id,
            capture_kind=kind,
            source=outcome.source,
            request_url=(
                self.config.sporttery_url
                if outcome.source == SOURCE_OFFICIAL_SPORTTERY
                else self.config.betexplorer_url
            ),
            request_started_at=outcome.request_started_at,
            response_received_at=outcome.response_received_at,
            latency_ms=outcome.latency_ms,
            http_status=outcome.http_status,
            failure_class=outcome.failure_class,
            raw_byte_length=len(outcome.raw) if outcome.raw is not None else None,
            raw_sha256=digest,
            raw_file_path=rel_path,
            parser_version=self.config.parser_version,
            deployed_commit=self._commit,
            change_event_id=change_event_id,
        )
        return self.store.record_capture(record)

    # -- legs ---------------------------------------------------------------

    def _capture_sporttery(self, *, round_id: str, kind: str,
                           change_event_id: str | None = None) -> int:
        outcome = self._fetch(
            SOURCE_OFFICIAL_SPORTTERY, build_sporttery_request(self.config.sporttery_url)
        )
        capture_id = self._persist_leg(
            outcome, round_id=round_id, kind=kind, change_event_id=change_event_id
        )

        if outcome.failure_class is None and outcome.text is not None:
            try:
                quotes, meta = parse_match_calculator(
                    outcome.text,
                    observed_at=outcome.response_received_at,
                    payload_sha256=hashlib.sha256(outcome.raw or b"").hexdigest(),
                    http_status=outcome.http_status,
                    collector_version=self.config.parser_version,
                )
            except (ValueError, json.JSONDecodeError) as exc:
                LOGGER.warning("sporttery parse failed: %s", exc)
                return capture_id

            rows: list[dict[str, Any]] = []
            for quote in quotes:
                availability = quote.pool_availability.get("had")
                provider_stamp = quote.pool_updated_at.get("had")
                rows.append(
                    {
                        "match_id": quote.match_id,
                        "match_num_str": quote.match_num_str,
                        "league": quote.league,
                        "home": quote.home,
                        "away": quote.away,
                        "kickoff_local": (
                            quote.kickoff_local.isoformat() if quote.kickoff_local else None
                        ),
                        "had_h": quote.had[0] if quote.had else None,
                        "had_d": quote.had[1] if quote.had else None,
                        "had_a": quote.had[2] if quote.had else None,
                        "provider_had_updated_at": (
                            provider_stamp.isoformat() if provider_stamp else None
                        ),
                        "had_betting_single": (
                            availability.betting_single if availability else None
                        ),
                        "had_betting_allup": (
                            availability.betting_allup if availability else None
                        ),
                        "had_pool_status": availability.pool_status if availability else None,
                        "had_close_date": availability.pool_close_date if availability else None,
                        "had_close_time": availability.pool_close_time if availability else None,
                        "observed_at": quote.observed_at.isoformat(),
                        "payload_sha256": meta.payload_sha256,
                    }
                )
            self.store.record_sporttery_facts(capture_id, rows)
            LOGGER.info("sporttery %s: %d match rows", kind, len(rows))

        return capture_id

    def _capture_betexplorer(self, *, round_id: str, kind: str) -> tuple[int, list[tuple[str, tuple[float, float, float], tuple[float, float, float], datetime]]]:
        """Capture the reference leg.

        Returns ``(capture_id, changes)`` where each change is
        ``(event_id, previous_tuple, current_tuple, previous_received_at)``.

        The previous tuple and its receive time are captured **before** the
        baseline is refreshed, so the recorded interval describes the real
        transition rather than the value it moved to.
        """
        outcome = self._fetch(SOURCE_REFERENCE_BETEXPLORER, build_home_request(self.config.betexplorer_url))
        capture_id = self._persist_leg(outcome, round_id=round_id, kind=kind)

        changes: list[tuple[str, tuple[float, float, float], tuple[float, float, float], datetime]] = []
        if outcome.failure_class is None and outcome.text is not None:
            result = parse_homepage(
                outcome.text,
                response_received_at=outcome.response_received_at,
                parser_version=self.config.parser_version,
            )
            rows = [
                {
                    "event_id": q.event_id,
                    "event_url": q.event_url,
                    "home": q.home,
                    "away": q.away,
                    "kickoff_utc": q.kickoff_utc.isoformat() if q.kickoff_utc else None,
                    "home_odds": q.home_odds,
                    "draw_odds": q.draw_odds,
                    "away_odds": q.away_odds,
                    "response_received_at": q.response_received_at.isoformat(),
                    "duplicate_copies_collapsed": q.duplicate_copies_collapsed,
                    "parser_status": "ok",
                }
                for q in result.quotes
            ]
            self.store.record_betexplorer_facts(capture_id, rows)

            # Compare against the previous observation, then refresh the
            # baseline so a change is reported exactly once per transition.
            for quote in result.quotes:
                previous = self._last_reference.get(quote.event_id)
                if previous is not None and previous[0] != quote.odds_tuple:
                    changes.append(
                        (quote.event_id, previous[0], quote.odds_tuple, previous[1])
                    )
            for quote in result.quotes:
                self._last_reference[quote.event_id] = (
                    quote.odds_tuple,
                    outcome.response_received_at,
                )

            LOGGER.info(
                "betexplorer %s: %d quotes, %d issues, %d rows w/o odds, %d changes",
                kind, len(result.quotes), len(result.issues),
                result.rows_without_odds, len(changes),
            )

        return capture_id, changes

    # -- rounds -------------------------------------------------------------

    def run_round(self, *, kind: str = CAPTURE_KIND_REGULAR,
                  round_id: str | None = None) -> dict[str, Any]:
        """Execute one round: two concurrent legs, then any confirmations."""
        self._round_index += 1
        rid = round_id or f"r{self._round_index:05d}"
        summary: dict[str, Any] = {"round_id": rid, "kind": kind}

        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_sp = pool.submit(self._capture_sporttery, round_id=rid, kind=kind)
            fut_be = pool.submit(self._capture_betexplorer, round_id=rid, kind=kind)
            sp_capture = fut_sp.result()
            be_capture, changes = fut_be.result()

        summary["sporttery_capture_id"] = sp_capture
        summary["betexplorer_capture_id"] = be_capture
        summary["changes"] = len(changes)

        for event_id, previous_tuple, current_tuple, previous_received in changes:
            # One extra official fetch per changed event, marked distinctly.
            confirm_capture = self._capture_sporttery(
                round_id=rid,
                kind=CAPTURE_KIND_CHANGE_CONFIRMATION,
                change_event_id=event_id,
            )
            self.store.record_reference_change(
                event_id=event_id,
                previous_tuple=previous_tuple,
                current_tuple=current_tuple,
                previous_response_received_at=previous_received,
                current_response_received_at=datetime.now(timezone.utc),
                confirmation_capture_id=confirm_capture,
                round_id=rid,
            )
            LOGGER.info("reference change %s -> confirmation capture %d", event_id, confirm_capture)

        return summary

    def stop(self) -> None:
        self._stop.set()

    def run_forever(self) -> None:
        """Run rounds on a start-to-start cadence without overlapping."""
        while not self._stop.is_set():
            if self.config.max_rounds is not None and self._round_index >= self.config.max_rounds:
                LOGGER.info("reached max_rounds=%d, stopping", self.config.max_rounds)
                break
            started = time.monotonic()
            try:
                summary = self.run_round()
                LOGGER.info("round done: %s", summary)
            except Exception:  # noqa: BLE001 - a round must never kill the loop
                LOGGER.exception("round failed; continuing")

            elapsed = time.monotonic() - started
            lag = elapsed - self.config.round_interval_seconds
            if lag > 0:
                LOGGER.warning("scheduler lag %.1fs (round took %.1fs)", lag, elapsed)

            remaining = self.config.round_interval_seconds - elapsed
            if remaining > 0:
                self._stop.wait(remaining)


def run_forever(config: CollectorConfig) -> None:
    """Module-level entry point used by the systemd unit."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    collector = ProspectiveCollector(config)
    LOGGER.info("collector starting: data_root=%s commit=%s", config.data_root,
                config.deployed_commit)
    try:
        collector.run_forever()
    finally:
        collector.store.close()
        LOGGER.info("collector stopped")
