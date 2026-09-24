"""Append-only SQLite ledger + raw-capture store for the TASK-0005 collector.

Design constraints, from TASK-0005 §6/§7 and ``docs/data-policy.md``:

- **Append-only.** There is no update path and no delete path. A correction is a
  new row. Raw captures are written once and never edited in place.
- **Raw bytes are authoritative.** Every captured body is gzip-compressed to
  disk with its byte length and SHA-256 recorded next to it, so a later reader
  can prove which bytes produced which numbers.
- **Two clocks stay two clocks.** The ledger records ``request_started_at`` and
  ``response_received_at`` separately, plus the derived ``latency_ms``. Nothing
  is collapsed into a single "time".
- **Qualification data is labelled.** Every row carries
  ``dataset_phase = QUALIFICATION`` so it can never be mistaken for the sealed
  prospective dataset TASK-0006 will collect.

The store is deliberately standard-library only (``sqlite3``, ``gzip``,
``hashlib``) so the runtime has no dependency surface to reproduce.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

__all__ = [
    "DATASET_PHASE",
    "CAPTURE_KIND_REGULAR",
    "CAPTURE_KIND_CHANGE_CONFIRMATION",
    "CaptureRecord",
    "LedgerStore",
    "SOURCE_OFFICIAL_SPORTTERY",
    "SOURCE_REFERENCE_BETEXPLORER",
    "source_display_name",
]

#: Marks every row this collector writes. TASK-0006 collects the real thing.
DATASET_PHASE = "QUALIFICATION"

CAPTURE_KIND_REGULAR = "regular"
CAPTURE_KIND_CHANGE_CONFIRMATION = "change_confirmation"

SOURCE_OFFICIAL_SPORTTERY = "official_sporttery"
SOURCE_REFERENCE_BETEXPLORER = "reference_betexplorer"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS captures (
    capture_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id            TEXT    NOT NULL,
    capture_kind        TEXT    NOT NULL,
    source              TEXT    NOT NULL,
    request_url         TEXT,
    request_started_at  TEXT    NOT NULL,
    response_received_at TEXT   NOT NULL,
    latency_ms          REAL,
    http_status         INTEGER,
    failure_class       TEXT,
    raw_byte_length     INTEGER,
    raw_sha256          TEXT,
    raw_file_path       TEXT,
    parser_version      TEXT,
    deployed_commit     TEXT,
    dataset_phase       TEXT    NOT NULL,
    change_event_id     TEXT,
    created_at          TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_captures_round ON captures(round_id);
CREATE INDEX IF NOT EXISTS idx_captures_kind ON captures(capture_kind);
CREATE INDEX IF NOT EXISTS idx_captures_source ON captures(source);

CREATE TABLE IF NOT EXISTS sporttery_facts (
    fact_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    capture_id          INTEGER NOT NULL,
    match_id            TEXT,
    match_num_str       TEXT,
    league              TEXT,
    home                TEXT,
    away                TEXT,
    kickoff_local       TEXT,
    had_h               REAL,
    had_d               REAL,
    had_a               REAL,
    provider_had_updated_at TEXT,
    had_betting_single  INTEGER,
    had_betting_allup   INTEGER,
    had_pool_status     TEXT,
    had_close_date      TEXT,
    had_close_time      TEXT,
    observed_at         TEXT,
    payload_sha256      TEXT,
    dataset_phase       TEXT    NOT NULL,
    FOREIGN KEY (capture_id) REFERENCES captures(capture_id)
);
CREATE INDEX IF NOT EXISTS idx_sf_capture ON sporttery_facts(capture_id);
CREATE INDEX IF NOT EXISTS idx_sf_match ON sporttery_facts(match_id, capture_id);

CREATE TABLE IF NOT EXISTS betexplorer_facts (
    fact_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    capture_id          INTEGER NOT NULL,
    event_id            TEXT    NOT NULL,
    event_url           TEXT,
    home                TEXT,
    away                TEXT,
    kickoff_utc         TEXT,
    home_odds           REAL,
    draw_odds           REAL,
    away_odds           REAL,
    response_received_at TEXT   NOT NULL,
    duplicate_copies_collapsed INTEGER,
    parser_status       TEXT,
    dataset_phase       TEXT    NOT NULL,
    FOREIGN KEY (capture_id) REFERENCES captures(capture_id)
);
CREATE INDEX IF NOT EXISTS idx_bf_capture ON betexplorer_facts(capture_id);
CREATE INDEX IF NOT EXISTS idx_bf_event ON betexplorer_facts(event_id, capture_id);

CREATE TABLE IF NOT EXISTS reference_changes (
    change_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            TEXT    NOT NULL,
    previous_tuple      TEXT    NOT NULL,
    current_tuple       TEXT    NOT NULL,
    previous_response_received_at TEXT NOT NULL,
    current_response_received_at  TEXT NOT NULL,
    change_interval_lower TEXT,
    change_interval_upper TEXT,
    confirmation_capture_id INTEGER,
    round_id            TEXT,
    dataset_phase       TEXT    NOT NULL,
    created_at          TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rc_event ON reference_changes(event_id);
"""


def _now_iso(moment: datetime | None = None) -> str:
    """ISO-8601 with an explicit offset. Naive input is a programming error."""
    stamp = moment or datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        raise ValueError("ledger timestamps must be timezone-aware")
    return stamp.isoformat()


@dataclass(frozen=True, slots=True)
class CaptureRecord:
    """Everything one HTTP observation contributes to the ledger."""

    round_id: str
    capture_kind: str
    source: str
    request_url: str
    request_started_at: datetime
    response_received_at: datetime
    latency_ms: float | None
    http_status: int | None
    failure_class: str | None
    raw_byte_length: int | None
    raw_sha256: str | None
    raw_file_path: str | None
    parser_version: str
    deployed_commit: str
    change_event_id: str | None = None


class LedgerStore:
    """Append-only ledger plus a content-addressed raw-capture directory."""

    def __init__(self, data_root: str | Path, *, deployed_commit: str = "unknown") -> None:
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.raw_root = self.data_root / "raw"
        self.raw_root.mkdir(parents=True, exist_ok=True)
        self.log_root = self.data_root / "logs"
        self.log_root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_root / "ledger.sqlite3"
        self.deployed_commit = deployed_commit
        # The two collection legs run in separate threads, so the connection is
        # opened for cross-thread use and every write is serialised by a lock.
        # Writes are tiny and infrequent, so this costs nothing measurable.
        self._write_lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self.db_path), isolation_level=None, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        # Durability over throughput: this writes a handful of rows a minute.
        self._conn.execute("PRAGMA journal_mode=WAL")

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> LedgerStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- raw storage -------------------------------------------------------

    def persist_raw(
        self,
        raw: bytes,
        *,
        source: str,
        observed_at: datetime,
        suffix: str = "bin",
    ) -> tuple[str, str]:
        """Write raw bytes once and return ``(sha256, relative_path)``.

        The file name embeds the content hash, so re-writing identical bytes is a
        no-op and a changed payload can never silently overwrite an old one.
        """
        digest = hashlib.sha256(raw).hexdigest()
        day = observed_at.astimezone(timezone.utc).strftime("%Y%m%d")
        rel = Path(day) / f"{source}-{digest[:16]}.{suffix}.gz"
        target = self.raw_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with gzip.open(target, "wb") as handle:
                handle.write(raw)
        return digest, str(rel)

    # -- capture ledger ----------------------------------------------------

    def record_capture(self, record: CaptureRecord) -> int:
        with self._write_lock:
            return self._record_capture_locked(record)

    def _record_capture_locked(self, record: CaptureRecord) -> int:
        cursor = self._conn.execute(
            """
            INSERT INTO captures (
                round_id, capture_kind, source, request_url,
                request_started_at, response_received_at, latency_ms,
                http_status, failure_class, raw_byte_length, raw_sha256,
                raw_file_path, parser_version, deployed_commit, dataset_phase,
                change_event_id, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                record.round_id,
                record.capture_kind,
                record.source,
                record.request_url,
                _now_iso(record.request_started_at),
                _now_iso(record.response_received_at),
                record.latency_ms,
                record.http_status,
                record.failure_class,
                record.raw_byte_length,
                record.raw_sha256,
                record.raw_file_path,
                record.parser_version,
                record.deployed_commit,
                DATASET_PHASE,
                record.change_event_id,
                _now_iso(),
            ),
        )
        return int(cursor.lastrowid)

    # -- normalised facts --------------------------------------------------

    def record_sporttery_facts(
        self,
        capture_id: int,
        rows: Iterable[Mapping[str, object]],
    ) -> int:
        """Persist HAD-level facts for one Sporttery capture.

        Only the fields TASK-0004 validated are required here. Other pools the
        payload may carry are intentionally not promoted to comparison markets.
        """
        payload = [
            (
                capture_id,
                row.get("match_id"),
                row.get("match_num_str"),
                row.get("league"),
                row.get("home"),
                row.get("away"),
                row.get("kickoff_local"),
                row.get("had_h"),
                row.get("had_d"),
                row.get("had_a"),
                row.get("provider_had_updated_at"),
                row.get("had_betting_single"),
                row.get("had_betting_allup"),
                row.get("had_pool_status"),
                row.get("had_close_date"),
                row.get("had_close_time"),
                row.get("observed_at"),
                row.get("payload_sha256"),
                DATASET_PHASE,
            )
            for row in rows
        ]
        if not payload:
            return 0
        with self._write_lock:
            self._insert_sporttery_facts(payload)
        return len(payload)

    def _insert_sporttery_facts(self, payload: list) -> None:
        self._conn.executemany(
            """
            INSERT INTO sporttery_facts (
                capture_id, match_id, match_num_str, league, home, away,
                kickoff_local, had_h, had_d, had_a, provider_had_updated_at,
                had_betting_single, had_betting_allup, had_pool_status,
                had_close_date, had_close_time, observed_at, payload_sha256,
                dataset_phase
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            payload,
        )

    def record_betexplorer_facts(
        self,
        capture_id: int,
        rows: Iterable[Mapping[str, object]],
    ) -> int:
        payload = [
            (
                capture_id,
                row.get("event_id"),
                row.get("event_url"),
                row.get("home"),
                row.get("away"),
                row.get("kickoff_utc"),
                row.get("home_odds"),
                row.get("draw_odds"),
                row.get("away_odds"),
                row.get("response_received_at"),
                row.get("duplicate_copies_collapsed"),
                row.get("parser_status"),
                DATASET_PHASE,
            )
            for row in rows
        ]
        if not payload:
            return 0
        with self._write_lock:
            self._insert_betexplorer_facts(payload)
        return len(payload)

    def _insert_betexplorer_facts(self, payload: list) -> None:
        self._conn.executemany(
            """
            INSERT INTO betexplorer_facts (
                capture_id, event_id, event_url, home, away, kickoff_utc,
                home_odds, draw_odds, away_odds, response_received_at,
                duplicate_copies_collapsed, parser_status, dataset_phase
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            payload,
        )

    # -- reference-change ledger -------------------------------------------

    def record_reference_change(
        self,
        *,
        event_id: str,
        previous_tuple: Sequence[float],
        current_tuple: Sequence[float],
        previous_response_received_at: datetime,
        current_response_received_at: datetime,
        confirmation_capture_id: int | None,
        round_id: str,
    ) -> int:
        """Persist one reference-price change event.

        ``change_interval_lower`` / ``upper`` express the honest bracket: the
        change happened *after* the previous successful observation and *at or
        before* the current one. The exact provider change instant is **not**
        claimed, because BetExplorer publishes none.
        """
        with self._write_lock:
            return self._record_reference_change_locked(
                event_id=event_id,
                previous_tuple=previous_tuple,
                current_tuple=current_tuple,
                previous_response_received_at=previous_response_received_at,
                current_response_received_at=current_response_received_at,
                confirmation_capture_id=confirmation_capture_id,
                round_id=round_id,
            )

    def _record_reference_change_locked(
        self,
        *,
        event_id: str,
        previous_tuple: Sequence[float],
        current_tuple: Sequence[float],
        previous_response_received_at: datetime,
        current_response_received_at: datetime,
        confirmation_capture_id: int | None,
        round_id: str,
    ) -> int:
        cursor = self._conn.execute(
            """
            INSERT INTO reference_changes (
                event_id, previous_tuple, current_tuple,
                previous_response_received_at, current_response_received_at,
                change_interval_lower, change_interval_upper,
                confirmation_capture_id, round_id, dataset_phase, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                event_id,
                json.dumps(list(previous_tuple)),
                json.dumps(list(current_tuple)),
                _now_iso(previous_response_received_at),
                _now_iso(current_response_received_at),
                _now_iso(previous_response_received_at),
                _now_iso(current_response_received_at),
                confirmation_capture_id,
                round_id,
                DATASET_PHASE,
                _now_iso(),
            ),
        )
        return int(cursor.lastrowid)

    # -- inspection helpers (reviewer access, TASK-0005 §12) ---------------

    def count_captures(self, *, kind: str | None = None) -> int:
        if kind is None:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM captures").fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM captures WHERE capture_kind = ?", (kind,)
            ).fetchone()
        return int(row["n"])

    def latency_summary(self, source: str) -> dict[str, float | int | None]:
        row = self._conn.execute(
            """
            SELECT COUNT(*) AS n, MIN(latency_ms) AS lo, MAX(latency_ms) AS hi,
                   AVG(latency_ms) AS avg
            FROM captures WHERE source = ? AND latency_ms IS NOT NULL
            """,
            (source,),
        ).fetchone()
        return {
            "count": int(row["n"]),
            "min_ms": row["lo"],
            "max_ms": row["hi"],
            "mean_ms": row["avg"],
        }

    def source_success_failure(self, source: str) -> dict[str, int]:
        rows = self._conn.execute(
            """
            SELECT failure_class, COUNT(*) AS n FROM captures
            WHERE source = ? GROUP BY failure_class
            """,
            (source,),
        ).fetchall()
        result = {"success": 0, "failure": 0}
        for row in rows:
            if row["failure_class"] is None:
                result["success"] += int(row["n"])
            else:
                result["failure"] += int(row["n"])
        return result


def source_display_name(source: str) -> str:
    """Human-readable source name for logs and reports."""
    return {
        SOURCE_OFFICIAL_SPORTTERY: "Sporttery official (HAD)",
        SOURCE_REFERENCE_BETEXPLORER: "BetExplorer homepage (reference_proxy)",
    }.get(source, source)
