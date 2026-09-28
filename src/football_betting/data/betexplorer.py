"""Transport + parsing layer for the BetExplorer homepage as a ``reference_proxy``.

Why this module exists
----------------------
TASK-0005 builds an unattended collector whose *reference leg* is BetExplorer's
current/pre-match 1X2 quote. TASK-0004 established the source semantics; this
module turns them into code that the collector and the tests can share.

Three hard rules carried over from TASK-0004 and ``docs/data-policy.md``:

1. **BetExplorer exposes no provider-side update timestamp.**
   Our ``response_received_at`` is the instant the quote became knowable to us.
   It is never labelled, stored, or aliased as a provider update time. The
   dataclass below deliberately has no field that could be mistaken for one.

2. **Raw bytes are the authoritative capture.** Parsing works on a caller-supplied
   string, and the caller keeps the bytes and their SHA-256. This module never
   repairs, re-encodes, or silently drops undecodable content.

3. **Fail closed.** A row whose 1X2 triple is incomplete, non-numeric, or
   ambiguous is not guessed at. It is reported as a parse failure for that row
   and excluded, so a later reader can see how many rows were dropped and why.

Dialect note
------------
Only the **homepage** dialect carries machine-readable kickoff
(``data-dt`` / ``data-ts``). League fixture pages render kickoff as prose and are
therefore unusable for timing work; this module does not attempt them.

Reference-series note (added 2026-09-28, TASK-0005 F3)
-----------------------------------------------------
The homepage is a *multi-variant* document: the same URL returns renderings that
differ in declared ``currentGeoLocation``, in asset-version serial, in the number
of fixtures shown, and in the odds attached to the same ``data-event-id``.
:func:`parse_page_variant` reads the two page-declared tokens so the collector can
compare like-for-like. Variant transitions are a *source* fact, never a market
move.

How a fixture is identified
---------------------------
TASK-0004 measured that the homepage renders many fixtures **twice** (desktop +
mobile copies of the same event) and that the two copies can occasionally differ
on the away leg by a rounding step. Deduplication therefore keys on
``data-event-id`` (a stable provider identifier) and keeps the **first** copy in
document order, recording how many copies were collapsed. Provider identifiers
are preserved in full - never truncated to "the unique-looking part".
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone

__all__ = [
    "BETEXPLORER_HOME_URL",
    "REFERENCE_PROXY_LABEL",
    "BetExplorerParseResult",
    "BetExplorerQuote",
    "BetExplorerRowIssue",
    "PageVariant",
    "build_home_request",
    "decode_strict_utf8",
    "parse_homepage",
    "parse_page_variant",
    "variant_key_from_label",
]

#: The only dialect that exposes a machine-readable kickoff.
BETEXPLORER_HOME_URL = "https://www.betexplorer.com/"

#: The label every value from this source must carry. It is not Pinnacle,
#: not Betfair, and does not imply any named sharp bookmaker.
REFERENCE_PROXY_LABEL = "reference_proxy"

#: Row delimiter measured on 2026-09-24/25. Each match is one ``<li>`` with this
#: class prefix; the trailing class list differs between desktop and mobile.
_ROW_SPLIT = re.compile(r'<li class="showHide table-main__tournamentLiContent')

_ATTR_RE = {
    "event_id": re.compile(r'data-event-id="([^"]+)"'),
    "data_dt": re.compile(r'data-dt="([^"]+)"'),
    "data_ts": re.compile(r'data-ts="([^"]+)"'),
    "url": re.compile(r'href="(/football/[^"]+)"'),
}

#: ``data-odd`` appears once per 1X2 selection inside a row.
_ODD_RE = re.compile(r'data-odd="([^"]+)"')

#: Team names sit in these classes; used only for reporting, never for identity.
_HOME_RE = re.compile(r'table-main__participantHome[^>]*>\s*<p[^>]*>([^<]*)</p>')
_AWAY_RE = re.compile(r'table-main__participantAway[^>]*>.*?<p[^>]*>([^<]*)</p>', re.DOTALL)

#: The page's own timezone basis. ``data-dt`` is UK local (BST in September);
#: ``data-ts`` is an unambiguous epoch, which is why it is preferred below.
_UK_TZ = timezone.utc

# ---------------------------------------------------------------------------
# Page-declared variant tokens (TASK-0005 F3 remediation, 2026-09-28)
# ---------------------------------------------------------------------------
#
# The homepage is *not* one document. It is served from a multi-variant CDN
# cache, and different renderings of the same URL carry different fixtures and
# different odds for the same ``data-event-id``. Diagnostic evidence from the
# retained TASK-0005 qualification captures (452 BetExplorer payloads, 2026-09-24
# to 2026-09-28) showed:
#
#   * 20 distinct payloads, 9 distinct declared ``currentGeoLocation`` values,
#     2 distinct asset-version serials, and 92 / 93 / 107 / 108 fixtures
#     depending on the variant;
#   * 2281 cross-round odds differences collapsed into
#     1180 (geo differs, serial differs) + 843 (geo differs, serial same)
#     + 216 (geo same, serial differs) + 42 (geo same, serial same).
#
# In other words the pair (geo, serial) - both declared by the page itself -
# accounts for ~98% of the observed cross-round "changes". Neither token is a
# provider quote-update time; they only identify *which rendering* this is.
#
# The reference series must therefore be compared like-for-like. This module
# extracts the two tokens so the collector can key its baselines on them.
_VARIANT_GEO_RE = re.compile(r"currentGeoLocation\s*=\s*'([^']*)'")
_VARIANT_SERIAL_RE = re.compile(r"betexplorer\.svg\?serial=(\d+)")


@dataclass(frozen=True, slots=True)
class PageVariant:
    """Which rendering of the homepage this payload is, per the page itself.

    Both fields are read verbatim out of the served document; neither is
    inferred, and neither is a quote timestamp. ``None`` means the page did not
    declare that token, which is recorded as ``"?"`` in :attr:`key` rather than
    being guessed.
    """

    geo_location: str | None = None
    asset_serial: str | None = None

    @property
    def key(self) -> tuple[str, str]:
        """Stable, hashable identity used to key reference baselines."""
        return (self.geo_location or "?", self.asset_serial or "?")

    @property
    def label(self) -> str:
        """Human-readable form for logs and the ledger."""
        return f"geo={self.geo_location or '?'}|serial={self.asset_serial or '?'}"

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.label


def parse_page_variant(text: str) -> PageVariant:
    """Extract the page-declared variant tokens from a homepage body.

    Deliberately tolerant of *absence*: a page that does not declare them is
    reported as unknown, never back-filled from a previous observation.
    """
    geo = _VARIANT_GEO_RE.search(text)
    serial = _VARIANT_SERIAL_RE.search(text)
    return PageVariant(
        geo_location=geo.group(1).strip() if geo else None,
        asset_serial=serial.group(1).strip() if serial else None,
    )


def variant_key_from_label(label: str | None) -> tuple[str, str] | None:
    """Reverse :attr:`PageVariant.label` into the tuple used to key baselines.

    A restarted collector hydrates its reference baseline from the ledger, where
    the variant is stored in its human-readable ``label`` form (TASK-0006 §5.4).
    A label that is not a declared variant - ``"decode_error"``, say - has no
    key, and ``None`` is the honest answer rather than a fabricated one.
    """
    if label is None:
        return None
    geo: str | None = None
    serial: str | None = None
    for part in label.split("|"):
        name, _, value = part.partition("=")
        if name.strip() == "geo":
            geo = value
        elif name.strip() == "serial":
            serial = value
    if geo is None or serial is None:
        return None
    return (geo, serial)


def decode_strict_utf8(raw: bytes) -> str:
    """Decode a UTF-8 source strictly, or raise.

    ``docs/data-policy.md`` (post-500.com finding) requires that research-critical
    parsing never uses permissive ``errors='ignore'`` / ``errors='replace'``:
    silently replacing bytes can corrupt identity/odds text while still
    producing a plausible-looking parse. Callers must treat a raised
    :class:`UnicodeDecodeError` as a recorded failure, not as "no data".
    """
    return raw.decode("utf-8", "strict")



@dataclass(frozen=True, slots=True)
class BetExplorerQuote:
    """One BetExplorer fixture row, with only timestamps we can defend.

    ``kickoff_utc``
        Parsed from the provider's own ``data-ts`` epoch. Advertised kickoff,
        not an update time.
    ``response_received_at``
        **Our** clock - the moment the payload that carried this row reached us.
        The caller injects it. It is the time the quote became knowable.
    ``data_dt_raw``
        The provider's raw ``data-dt`` string, kept verbatim so a later reader
        can re-derive the kickoff in UK local time without trusting our parse.

    There is deliberately **no** ``source_updated_at`` / ``provider_updated_at``:
    BetExplorer publishes none, and inventing one would corrupt D01-B.
    """

    event_id: str
    event_url: str | None
    kickoff_utc: datetime | None
    data_dt_raw: str | None
    home: str | None
    away: str | None
    home_odds: float
    draw_odds: float
    away_odds: float
    response_received_at: datetime
    duplicate_copies_collapsed: int = 1

    @property
    def odds_tuple(self) -> tuple[float, float, float]:
        """The 1X2 tuple used by reference-change detection."""
        return (self.home_odds, self.draw_odds, self.away_odds)

    @property
    def source_label(self) -> str:
        return REFERENCE_PROXY_LABEL


@dataclass(frozen=True, slots=True)
class BetExplorerRowIssue:
    """A row that could not be turned into a quote, and why.

    Kept rather than discarded: "we saw a fixture and could not read it" is a
    data-quality fact worth retaining (``docs/data-policy.md`` §9).
    """

    reason: str
    detail: str
    raw_excerpt: str


@dataclass(frozen=True, slots=True)
class BetExplorerParseResult:
    """Everything one homepage parse produced, including what it rejected."""

    quotes: tuple[BetExplorerQuote, ...]
    issues: tuple[BetExplorerRowIssue, ...]
    rows_seen: int
    duplicates_collapsed: int
    #: Rows that carried no odds at all. This is an ordinary state (fixture not
    #: yet priced, or already finished), not a defect, so it is counted
    #: separately from ``issues`` rather than inflating the failure count.
    rows_without_odds: int = 0
    parser_version: str = "task0005-be/0.1"
    extras: Mapping[str, int] = field(default_factory=dict)
    #: Which rendering this payload was, per the page's own tokens. The collector
    #: keys its reference baselines on this so a variant transition can never be
    #: mistaken for a market move (TASK-0005 F3).
    variant: PageVariant = field(default_factory=PageVariant)


def build_home_request(
    url: str = BETEXPLORER_HOME_URL,
    *,
    timeout_seconds: float = 45.0,
):
    """Build a plain browser-shaped GET for the homepage.

    BetExplorer serves the page to ordinary clients; this is not a WAF-bypass
    helper. No cookies, no proxy, no fingerprint manipulation - TASK-0005 §8
    forbids those.
    """
    import urllib.request

    return urllib.request.Request(  # noqa: S310 - fixed https endpoint
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        method="GET",
    )


def _parse_epoch(value: str | None) -> datetime | None:
    """Decode ``data-ts`` (epoch seconds) into an aware UTC datetime.

    Absent or malformed values stay ``None`` - never back-filled from our clock.
    """
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value.strip()), tz=_UK_TZ)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _parse_odds(raw_values: list[str]) -> tuple[float, float, float] | None:
    """Decode the three ``data-odd`` values, failing closed on anything odd.

    More than three values means the row's layout is not the dialect this module
    was written against - that is ambiguous, so it is rejected rather than
    guessed at.
    """
    if len(raw_values) != 3:
        return None
    try:
        triple = tuple(float(v) for v in raw_values)
    except (TypeError, ValueError):
        return None
    if any(odd <= 1.0 for odd in triple):
        return None
    return triple  # type: ignore[return-value]


def parse_homepage(
    text: str,
    *,
    response_received_at: datetime,
    parser_version: str = "task0005-be/0.1",
) -> BetExplorerParseResult:
    """Parse a BetExplorer homepage body into deduplicated 1X2 quotes.

    Pure and deterministic: ``response_received_at`` is supplied by the caller,
    so this function can never manufacture a timestamp.

    Every issue is surfaced rather than swallowed - the caller decides how to
    record it. Nothing is repaired or imputed.
    """
    if response_received_at.tzinfo is None:
        raise ValueError("response_received_at must be timezone-aware")

    chunks = _ROW_SPLIT.split(text)[1:]
    rows_seen = len(chunks)

    quotes: list[BetExplorerQuote] = []
    issues: list[BetExplorerRowIssue] = []
    rows_without_odds = 0
    seen: dict[str, int] = {}
    duplicates_collapsed = 0

    for index, chunk in enumerate(chunks):
        excerpt = chunk[:180].replace("\n", " ")

        event_id_match = _ATTR_RE["event_id"].search(chunk)
        if event_id_match is None:
            issues.append(
                BetExplorerRowIssue(
                    reason="missing_event_id",
                    detail=f"row {index} has no data-event-id",
                    raw_excerpt=excerpt,
                )
            )
            continue
        event_id = event_id_match.group(1).strip()
        if not event_id:
            issues.append(
                BetExplorerRowIssue(
                    reason="empty_event_id",
                    detail=f"row {index} carries an empty data-event-id",
                    raw_excerpt=excerpt,
                )
            )
            continue

        odds_values = _ODD_RE.findall(chunk)

        # A row with no odds is an ordinary state (not priced yet, or finished).
        # Only a row that carries a *malformed* triple is a parse defect.
        if not odds_values:
            if event_id not in seen:
                seen[event_id] = 0
                rows_without_odds += 1
            continue

        triple = _parse_odds(odds_values)
        if triple is None:
            issues.append(
                BetExplorerRowIssue(
                    reason="unparsable_1x2",
                    detail=(
                        f"event {event_id}: expected 3 numeric data-odd values "
                        f"above 1.0, saw {len(odds_values)}"
                    ),
                    raw_excerpt=excerpt,
                )
            )
            continue

        # First *priced* copy in document order wins; later copies are counted.
        # An unpriced copy seen earlier must not shadow the priced one.
        if seen.get(event_id, 0) > 0:
            seen[event_id] += 1
            duplicates_collapsed += 1
            continue
        seen[event_id] = 1

        dt_match = _ATTR_RE["data_dt"].search(chunk)
        ts_match = _ATTR_RE["data_ts"].search(chunk)
        url_match = _ATTR_RE["url"].search(chunk)
        home_match = _HOME_RE.search(chunk)
        away_match = _AWAY_RE.search(chunk)

        quotes.append(
            BetExplorerQuote(
                event_id=event_id,
                event_url=url_match.group(1) if url_match else None,
                kickoff_utc=_parse_epoch(ts_match.group(1) if ts_match else None),
                data_dt_raw=dt_match.group(1) if dt_match else None,
                home=home_match.group(1).strip() if home_match else None,
                away=away_match.group(1).strip() if away_match else None,
                home_odds=triple[0],
                draw_odds=triple[1],
                away_odds=triple[2],
                response_received_at=response_received_at,
            )
        )

    return BetExplorerParseResult(
        quotes=tuple(quotes),
        issues=tuple(issues),
        rows_seen=rows_seen,
        duplicates_collapsed=duplicates_collapsed,
        rows_without_odds=rows_without_odds,
        parser_version=parser_version,
        extras={
            "unique_events": len(quotes),
            "collapsed_copies": duplicates_collapsed,
            "rows_without_odds": rows_without_odds,
        },
        variant=parse_page_variant(text),
    )
