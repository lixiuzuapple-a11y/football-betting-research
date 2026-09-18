"""Exception hierarchy for the research system.

Every error raised by this package derives from :class:`FootballBettingError`
so that callers can separate "our rules were violated" from genuine bugs.
"""

from __future__ import annotations


class FootballBettingError(Exception):
    """Base class for all errors raised by this package."""


class ValidationError(FootballBettingError, ValueError):
    """A data model was constructed with invalid values."""


class ProvenanceError(ValidationError):
    """A dataset lacks traceable provenance metadata.

    See ``docs/data-policy.md``.
    """


class FutureInformationError(FootballBettingError):
    """Data that was not knowable at the decision time was about to be used.

    Raised whenever an operation would let post-kickoff or post-match
    information enter a pre-match artefact. This is the single most important
    guard in the project; see ``docs/project-charter.md`` section 6.1.
    """


class NotAnInputError(FootballBettingError):
    """An object that can never be a model input was passed as an input.

    Post-match objects (``MatchResult``) fall in this category: they are
    outcomes, not features.
    """


class DuplicateRecordError(FootballBettingError):
    """A record with the same identifier already exists.

    The record stores are append-only, so re-writing an existing identifier
    is an error rather than an overwrite.
    """


class UnknownReferenceError(FootballBettingError):
    """A record references an entity that was never recorded."""


class NotImplementedYetError(FootballBettingError, NotImplementedError):
    """An honest placeholder.

    Raised by deliberate stage-1 stubs. This exception exists so that "not
    built yet" is machine-detectable and can never be mistaken for a working
    implementation. Stubs must never silently return fabricated values.
    """
