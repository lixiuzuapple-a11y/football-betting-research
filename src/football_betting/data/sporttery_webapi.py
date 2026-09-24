"""Transport + parsing layer for the official Sporttery (竞彩) match webapi.

Why this module exists
----------------------
TASK-0004 asks whether a *timestamped* Sporttery quote can be observed alongside
an external reference quote. That requires three things this module keeps
strictly apart:

``observed_at``
    When **our** collector received the payload. Injected by the caller, never
    invented by the parser.
``provider_updated_at``
    What **Sporttery** reports per pool (``had.updateDate`` + ``updateTime``)
    and per payload (``value.lastUpdateTime``). This is the provider's own claim
    and is deliberately never conflated with ``observed_at``.
``payload_sha256``
    Hash of the exact bytes we parsed, so a later reader can prove which
    payload produced which numbers.

Access rule (measured 2026-09-24, ``probe2/p27_official_variants.py`` and
``probe2/p28_header_isolation.py``)
-------------------------------------------------------------------------------
The endpoint answers HTTP 567 with an HTML challenge page when the request
carries **no ``Referer`` header**. With *any* ``Referer`` value it answers
HTTP 200 and JSON. Presence of the header is the determining factor; its value
is not (sporttery.cn, lottery.gov.cn and webapi.sporttery.cn all returned 200).
``Accept``, ``Accept-Language`` and ``Origin`` made no difference.

That is why :func:`build_request` always sets a ``Referer`` and why callers must
treat an HTML body as a challenge rather than as data - see
:func:`looks_like_challenge`.

Scope note
----------
This is a thin provider layer added under TASK-0004's smoke allowance. It does
**not** import :mod:`football_betting.domain` or the provenance/snapshot
pipeline on purpose: mapping these rows into ``OddsSnapshot`` /
``DataProvenance`` is an architecture decision for the Reviewer, not something a
capture task should decide unilaterally.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import MappingProxyType

__all__ = [
    "CHALLENGE_STATUS",
    "DEFAULT_REFERER",
    "MATCH_CALCULATOR_URL",
    "POOL_CODES",
    "SUPPORTED_POOLS",
    "CaptureMeta",
    "PoolAvailability",
    "SportteryQuote",
    "build_request",
    "fetch_match_calculator",
    "looks_like_challenge",
    "parse_match_calculator",
    "parse_provider_time",
]

#: The on-sale / current-quote endpoint. Omitting all query parameters returns
#: every pool for every listed match; ``poolCode`` only narrows the payload.
MATCH_CALCULATOR_URL = "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry"

#: Any ``Referer`` avoids the challenge; this is the natural same-site value.
DEFAULT_REFERER = "https://www.sporttery.cn/"

#: Observed HTTP status of the WAF challenge response (HTML, ~7.3 kB).
CHALLENGE_STATUS = 567

#: Pools the calculator exposes, as ``poolCode`` values accepted in a request.
POOL_CODES: Mapping[str, str] = {
    "had": "标准胜平负 (no handicap)",
    "hhad": "让球胜平负 (handicap 1X2)",
    "ttg": "总进球 (total goals, 8 buckets 0..7+)",
    "crs": "比分 (correct score)",
    "hafu": "半全场 (half-time / full-time)",
}

#: Pools this parser reads out. Others are counted but not normalised.
SUPPORTED_POOLS: tuple[str, ...] = ("had", "hhad", "ttg")

#: 竞彩 publishes kickoff in Beijing time; ``matchTime`` carries no offset.
BEIJING = timezone(timedelta(hours=8))

_CHALLENGE_MARKERS = ("navigator", "<script", "challenge", "verify", "captcha")

_TTG_KEYS: tuple[str, ...] = tuple(f"s{i}" for i in range(8))


def looks_like_challenge(text: str) -> bool:
    """True when a body is the access-control challenge rather than a payload.

    HTTP status alone cannot be trusted here: an interception or an error page
    can also arrive with 200, so the body is checked too.
    """
    head = text.lstrip()[:1]
    if head in "[{":
        return False
    lowered = text.lower()
    return any(marker in lowered for marker in _CHALLENGE_MARKERS)


def build_request(
    url: str = MATCH_CALCULATOR_URL,
    *,
    referer: str = DEFAULT_REFERER,
    timeout_seconds: float = 30.0,
) -> urllib.request.Request:
    """Build a request that the endpoint will answer with JSON.

    ``Referer`` is not optional decoration - see the module docstring. It is set
    here so no caller can accidentally omit it and receive a 567 challenge.
    """
    return urllib.request.Request(  # noqa: S310 - fixed https endpoint
        url,
        headers={
            "User-Agent": "football-betting-research/0.0.1 (+sporttery-capture)",
            "Referer": referer,
            "Accept": "application/json, text/plain, */*",
        },
        method="GET",
    )


def fetch_match_calculator(
    url: str = MATCH_CALCULATOR_URL,
    *,
    referer: str = DEFAULT_REFERER,
    timeout_seconds: float = 30.0,
) -> tuple[bytes, int]:
    """Fetch raw bytes plus the HTTP status. Network access - not unit tested.

    Raises :class:`ValueError` if the body is a challenge page, so a 200 that
    behaves like a block cannot silently reach the parser.
    """
    request = build_request(url, referer=referer, timeout_seconds=timeout_seconds)
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        raw: bytes = response.read()
        status = int(response.status)
    if looks_like_challenge(raw.decode("utf-8", "replace")):
        raise ValueError(
            f"Sporttery returned an access-control challenge (HTTP {status}); "
            "check that the Referer header was sent"
        )
    return raw, status


def parse_provider_time(date_part: str | None, time_part: str | None) -> datetime | None:
    """Combine a provider ``updateDate``/``updateTime`` pair into a datetime.

    Returns ``None`` when either half is missing - an absent provider timestamp
    must stay absent rather than be back-filled from our own clock.
    """
    if not date_part or not time_part:
        return None
    stamp = f"{date_part}T{time_part}"
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(stamp, fmt).replace(tzinfo=BEIJING)
        except ValueError:
            continue
    return None


def _triple(pool: Mapping[str, object]) -> tuple[float, float, float] | None:
    try:
        return (float(pool["h"]), float(pool["d"]), float(pool["a"]))  # type: ignore[arg-type]
    except (KeyError, TypeError, ValueError):
        return None


def _ttg_buckets(pool: Mapping[str, object]) -> tuple[float, ...] | None:
    try:
        values = tuple(float(pool[k]) for k in _TTG_KEYS)  # type: ignore[arg-type]
    except (KeyError, TypeError, ValueError):
        return None
    return values


def _as_int(value: object) -> int | None:
    """Coerce a payload flag to ``int``; anything else (incl. ``bool``) is absent."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _as_text(value: object) -> str | None:
    """Empty provider strings become ``None`` - absent stays absent."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _pool_updated_times(match: Mapping[str, object]) -> dict[str, datetime | None]:
    """Provider update time **per pool**, never collapsed into one value.

    On the captured ``周三003`` (Seattle vs Salt Lake) the five pools carry five
    different stamps - HAD ``18:51:22``, HHAD ``18:51:31``, CRS ``20:06:47``,
    HAFU ``21:38:47``, TTG ``21:50:41``. Keeping only their maximum would date a
    HAD quote with TTG's clock and shift the measured staleness by hours, which
    is exactly the quantity D01-B is trying to measure.
    """
    stamps: dict[str, datetime | None] = {}
    for code in POOL_CODES:
        block = match.get(code)
        if not isinstance(block, Mapping):
            continue
        stamps[code] = parse_provider_time(
            _as_text(block.get("updateDate")), _as_text(block.get("updateTime"))
        )
    return stamps


def _pool_availability(match: Mapping[str, object]) -> dict[str, PoolAvailability]:
    """Read ``poolList`` into per-pool executability facts.

    Returns ``{}`` when the payload carries no usable ``poolList``: an absent
    fact must stay absent rather than default to "sellable".
    """
    result: dict[str, PoolAvailability] = {}
    for entry in match.get("poolList") or []:
        if not isinstance(entry, Mapping):
            continue
        raw_code = _as_text(entry.get("poolCode"))
        if not raw_code:
            continue
        result[raw_code.lower()] = PoolAvailability(
            pool_code=raw_code,
            betting_single=_as_int(entry.get("bettingSingle")),
            betting_allup=_as_int(entry.get("bettingAllup")),
            pool_status=_as_text(entry.get("poolStatus")),
            pool_close_date=_as_text(entry.get("poolCloseDate")),
            pool_close_time=_as_text(entry.get("poolCloseTime")),
        )
    return result


@dataclass(frozen=True, slots=True)
class CaptureMeta:
    """Per-payload facts that belong to the update, not to a single quote."""

    payload_sha256: str
    observed_at: datetime
    http_status: int | None = None
    provider_last_update_time: datetime | None = None
    error_code: str | None = None
    match_count: int = 0
    collector_version: str = "unknown"


@dataclass(frozen=True, slots=True)
class PoolAvailability:
    """Per-pool executability facts the provider publishes in ``poolList``.

    D01-B asks whether a stale price can **still be bet**. Price plus timestamp
    cannot answer that on its own: on the captured ``周三003`` the provider allows
    single betting for TTG / CRS / HAFU (``bettingSingle=1``) while forbidding it
    for HAD / HHAD (``bettingSingle=0``), and status can leave ``Selling``
    independently per pool. Aggregating these onto the match would destroy the
    distinction the question needs.
    """

    pool_code: str
    betting_single: int | None = None
    betting_allup: int | None = None
    pool_status: str | None = None
    pool_close_date: str | None = None
    pool_close_time: str | None = None


@dataclass(frozen=True, slots=True)
class SportteryQuote:
    """One match's on-sale quotes, with every clock kept separate.

    TASK-0004's D01-B question needs three different facts to stay different:

    ``observed_at``
        **our** clock, injected by the caller and never invented here.
    ``pool_updated_at``
        the **provider's** clock *per pool*. On the captured ``周三003`` the
        five pools carry five different stamps - HAD ``18:51:22``, HHAD
        ``18:51:31``, CRS ``20:06:47``, HAFU ``21:38:47``, TTG ``21:50:41``.
        Collapsing them into one value would date a HAD quote with TTG's clock
        and move measured staleness by hours.
    ``latest_pool_updated_at``
        an **explicitly named aggregate** (the maximum of ``pool_updated_at``).
        It exists for convenience and must never be read as any particular
        market's update time.
    ``pool_availability``
        the provider's per-pool executability facts, so "this quote is old" can
        be told apart from "this quote can still be bet".
    """

    match_id: str
    match_num_str: str
    league: str
    home: str
    away: str
    kickoff_local: datetime | None
    pools: tuple[str, ...]
    had: tuple[float, float, float] | None
    hhad: tuple[float, float, float] | None
    goal_line: str | None
    ttg: tuple[float, ...] | None
    pool_updated_at: Mapping[str, datetime | None]
    latest_pool_updated_at: datetime | None
    pool_availability: Mapping[str, PoolAvailability]
    observed_at: datetime
    payload_sha256: str
    match_status: str | None = None
    sell_status: int | None = None
    extra: Mapping[str, object] = field(default_factory=dict)


def parse_match_calculator(
    text: str,
    *,
    observed_at: datetime,
    payload_sha256: str | None = None,
    http_status: int | None = None,
    collector_version: str = "task0004-revision-smoke/0.3",
) -> tuple[list[SportteryQuote], CaptureMeta]:
    """Parse a ``getMatchCalculatorV1.qry`` body into quotes.

    Pure and deterministic: ``observed_at`` is supplied by the caller, so the
    parser can never manufacture a timestamp. Pass ``payload_sha256`` of the raw
    bytes when available; otherwise it is computed from ``text``.
    """
    if observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    if looks_like_challenge(text):
        raise ValueError("payload is an access-control challenge, not match data")

    digest = payload_sha256 or hashlib.sha256(text.encode("utf-8")).hexdigest()
    document = json.loads(text)
    value = document.get("value") or {}

    quotes: list[SportteryQuote] = []
    for group in value.get("matchInfoList") or []:
        for match in group.get("subMatchList") or []:
            pools = tuple(sorted(code for code in POOL_CODES if match.get(code)))
            had_pool = match.get("had") or {}
            hhad_pool = match.get("hhad") or {}
            ttg_pool = match.get("ttg") or {}

            pool_times = _pool_updated_times(match)
            present = [s for s in pool_times.values() if s is not None]

            quotes.append(
                SportteryQuote(
                    match_id=str(match.get("matchId")),
                    match_num_str=str(match.get("matchNumStr") or ""),
                    league=str(match.get("leagueAbbName") or ""),
                    home=str(match.get("homeTeamAbbName") or ""),
                    away=str(match.get("awayTeamAbbName") or ""),
                    kickoff_local=_kickoff(match),
                    pools=pools,
                    had=_triple(had_pool),
                    hhad=_triple(hhad_pool),
                    goal_line=(str(hhad_pool["goalLine"])
                               if hhad_pool.get("goalLine") not in (None, "") else None),
                    ttg=_ttg_buckets(ttg_pool),
                    pool_updated_at=MappingProxyType(pool_times),
                    latest_pool_updated_at=max(present) if present else None,
                    pool_availability=MappingProxyType(_pool_availability(match)),
                    observed_at=observed_at,
                    payload_sha256=digest,
                    match_status=(str(match["matchStatus"])
                                  if match.get("matchStatus") else None),
                    sell_status=(int(match["sellStatus"])
                                 if isinstance(match.get("sellStatus"), int) else None),
                    extra={"businessDate": group.get("businessDate"),
                           "matchWeek": group.get("matchWeek"),
                           "leagueCode": match.get("leagueCode")},
                )
            )

    meta = CaptureMeta(
        payload_sha256=digest,
        observed_at=observed_at,
        http_status=http_status,
        provider_last_update_time=parse_provider_time(
            (value.get("lastUpdateTime") or "")[:10] or None,
            (value.get("lastUpdateTime") or "")[11:19] or None,
        ),
        error_code=str(document.get("errorCode")) if document.get("errorCode") is not None else None,
        match_count=len(quotes),
        collector_version=collector_version,
    )
    return quotes, meta


def _kickoff(match: Mapping[str, object]) -> datetime | None:
    date_part = match.get("matchDate")
    time_part = match.get("matchTime")
    if not date_part or not time_part:
        return None
    try:
        return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=BEIJING
        )
    except ValueError:
        return None


def pools_of(quotes: Sequence[SportteryQuote]) -> set[str]:
    """Convenience: the union of pools seen across ``quotes``."""
    return {code for quote in quotes for code in quote.pools}
