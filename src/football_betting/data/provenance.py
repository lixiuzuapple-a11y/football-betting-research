"""Provenance metadata and dataset snapshots.

Without provenance a dataset is unusable for research: you cannot say what was
known, when, or from where. ``DataSnapshot.knowable_at`` is the operational
form of that requirement - it answers "given only what had arrived by time *t*,
which rows may I use?".
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from ..domain.errors import ProvenanceError, ValidationError
from ..domain.models import Match, OddsSnapshot
from ..domain.validation import require_aware, require_non_empty_text


@dataclass(frozen=True, slots=True)
class DataProvenance:
    """Traceability header for one immutable dataset version.

    Field meanings (see ``docs/data-policy.md``):

    ``source``
        Where the rows came from - a URL, an API endpoint, a file hash.
    ``collected_at``
        When *we* pulled the data and finalised this version.
    ``data_time_start`` / ``data_time_end``
        The instants the rows describe. These are data times, not collection
        times, and they must not extend past ``collected_at``.
    ``version``
        Our own immutable label for this snapshot (e.g. ``2026-09-18.1``).
    ``schema``
        The contract version the payload conforms to, so that a later reader
        knows how to parse it.
    """

    source: str
    collected_at: datetime
    data_time_start: datetime
    data_time_end: datetime
    version: str
    schema: str
    notes: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_text(self.source, "source")
        require_non_empty_text(self.version, "version")
        require_non_empty_text(self.schema, "schema")
        require_aware(self.collected_at, "collected_at")
        require_aware(self.data_time_start, "data_time_start")
        require_aware(self.data_time_end, "data_time_end")
        if self.data_time_end < self.data_time_start:
            raise ValidationError("data_time_end must not be earlier than data_time_start")
        if self.data_time_end > self.collected_at:
            raise ProvenanceError(
                f"data_time_end ({self.data_time_end.isoformat()}) is later than "
                f"collected_at ({self.collected_at.isoformat()}): a dataset cannot "
                "describe a moment that had not happened when it was collected"
            )


@dataclass(frozen=True, slots=True)
class DataSnapshot:
    """An immutable, provenance-stamped set of rows.

    Snapshots are the only thing the feature layer is allowed to read. They are
    never edited in place; a correction is a new snapshot with a new version.

    ``matches`` here are fixtures whose *schedule* is known. A scoreline is not
    a ``Match``: it is a :class:`~football_betting.domain.models.MatchResult`,
    which lives outside this snapshot and is never a model input.
    """

    provenance: DataProvenance
    matches: tuple[Match, ...] = ()
    odds: tuple[OddsSnapshot, ...] = ()

    def __post_init__(self) -> None:
        start = self.provenance.data_time_start
        end = self.provenance.data_time_end
        for quote in self.odds:
            if not start <= quote.data_time <= end:
                raise ProvenanceError(
                    f"quote {quote.snapshot_id!r} has data_time "
                    f"{quote.data_time.isoformat()}, outside the window "
                    f"[{start.isoformat()}, {end.isoformat()}] this snapshot claims to cover"
                )

    @property
    def version(self) -> str:
        """Immutable label of this snapshot."""
        return self.provenance.version

    @property
    def collected_at(self) -> datetime:
        """When this snapshot was pulled and finalised."""
        return self.provenance.collected_at

    def knowable_at(self, when: datetime) -> DataSnapshot:
        """Restrict this snapshot to what had actually arrived by ``when``.

        Two different rules apply, because the two kinds of row become known in
        different ways:

        * **Quotes** carry their own arrival time, so they are filtered per row.
          A quote counts as known only when ``data_time <= when`` *and*
          ``collected_at <= when``. A feed that hands us a five-minute-old price
          does **not** let us claim we knew that price five minutes earlier, and
          a quote still sitting in an upstream queue is not ours yet.
        * **Fixtures** carry no arrival time of their own, so the snapshot as a
          whole governs them: no fixture is known before
          ``provenance.collected_at``. Attributing an arrival time to a fixture
          row would be invented precision.

        The two rules can disagree for an instant before the version was
        finalised, and that is intentional: an individual quote that had already
        reached us is genuinely known, even though the version containing it was
        not yet sealed.
        """
        require_aware(when, "when")
        matches = self.matches if self.provenance.collected_at <= when else ()
        odds = tuple(o for o in self.odds if o.data_time <= when and o.collected_at <= when)
        return replace(self, matches=matches, odds=odds)
