"""Requirement 7: a minimal experiment can be recorded - and cannot be deleted."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from football_betting.domain import (
    DuplicateRecordError,
    ExperimentStatus,
    UnknownReferenceError,
    ValidationError,
)
from football_betting.records import ExperimentRegistry, RecordStore, new_experiment_id

REGISTERED_AT = datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Requirement 7, directly
# ---------------------------------------------------------------------------


def test_a_minimal_experiment_can_be_recorded() -> None:
    registry = ExperimentRegistry()
    experiment = registry.register(
        hypothesis="Odds drifting more than 5% before kickoff carry information",
        data_version="fixture-2026-09-18.1",
        model_version="none",
        created_at=REGISTERED_AT,
        parameters={"drift_threshold": 0.05},
    )
    assert experiment.experiment_id.startswith("exp_")
    assert experiment.status is ExperimentStatus.PLANNED
    assert experiment.result is None
    assert registry.get(experiment.experiment_id) is experiment


def test_an_experiment_carries_every_field_the_charter_requires() -> None:
    registry = ExperimentRegistry()
    experiment = registry.register(
        hypothesis="h",
        data_version="d",
        model_version="m",
        created_at=REGISTERED_AT,
        parameters={"p": 1},
    )
    for field in (
        "experiment_id",
        "hypothesis",
        "data_version",
        "model_version",
        "parameters",
        "status",
    ):
        assert hasattr(experiment, field), f"charter requires {field}"
    assert experiment.result is None, "result is null until the experiment is resolved"


def test_an_experiment_result_can_be_recorded() -> None:
    registry = ExperimentRegistry()
    experiment = registry.register(
        hypothesis="h",
        data_version="d",
        model_version="m",
        created_at=REGISTERED_AT,
    )
    completed = registry.complete(
        experiment.experiment_id,
        result={"brier": 0.61, "samples": 128},
        at=REGISTERED_AT + timedelta(hours=2),
    )
    assert completed.status is ExperimentStatus.COMPLETED
    assert completed.result["samples"] == 128
    assert completed.updated_at == REGISTERED_AT + timedelta(hours=2)


# ---------------------------------------------------------------------------
# Failures are retained
# ---------------------------------------------------------------------------


def test_a_failed_experiment_stays_in_the_registry() -> None:
    registry = ExperimentRegistry()
    experiment = registry.register(
        hypothesis="h", data_version="d", model_version="m", created_at=REGISTERED_AT
    )
    failed = registry.fail(
        experiment.experiment_id,
        result={"error": "no data source configured"},
        at=REGISTERED_AT + timedelta(minutes=5),
    )
    assert failed.status is ExperimentStatus.FAILED
    assert len(registry.all()) == 1
    assert registry.get(experiment.experiment_id).status is ExperimentStatus.FAILED


def test_the_registry_offers_no_way_to_delete() -> None:
    registry = ExperimentRegistry()
    for forbidden in ("delete", "remove", "drop", "purge", "clear"):
        assert not hasattr(registry, forbidden), (
            f"ExperimentRegistry.{forbidden} would let a failed experiment be erased; "
            "the charter forbids it"
        )


def test_a_resolved_experiment_is_frozen() -> None:
    registry = ExperimentRegistry()
    experiment = registry.register(
        hypothesis="h", data_version="d", model_version="m", created_at=REGISTERED_AT
    )
    registry.complete(experiment.experiment_id, result={"brier": 0.6}, at=REGISTERED_AT)
    with pytest.raises(ValidationError, match="already COMPLETED"):
        registry.complete(experiment.experiment_id, result={"brier": 0.1}, at=REGISTERED_AT)
    with pytest.raises(ValidationError, match="already COMPLETED"):
        registry.fail(experiment.experiment_id, result={}, at=REGISTERED_AT)


def test_a_result_cannot_precede_the_experiment() -> None:
    registry = ExperimentRegistry()
    experiment = registry.register(
        hypothesis="h", data_version="d", model_version="m", created_at=REGISTERED_AT
    )
    with pytest.raises(ValidationError, match="before the experiment was created"):
        registry.complete(
            experiment.experiment_id, result={}, at=REGISTERED_AT - timedelta(seconds=1)
        )


def test_duplicate_registration_is_refused() -> None:
    registry = ExperimentRegistry()
    registry.register(
        hypothesis="h",
        data_version="d",
        model_version="m",
        created_at=REGISTERED_AT,
        experiment_id="exp-fixed",
    )
    with pytest.raises(DuplicateRecordError):
        registry.register(
            hypothesis="h2",
            data_version="d",
            model_version="m",
            created_at=REGISTERED_AT,
            experiment_id="exp-fixed",
        )


def test_unknown_experiments_are_reported() -> None:
    registry = ExperimentRegistry()
    with pytest.raises(UnknownReferenceError):
        registry.get("exp-nope")


def test_start_then_complete_transitions_forward() -> None:
    registry = ExperimentRegistry()
    experiment = registry.register(
        hypothesis="h", data_version="d", model_version="m", created_at=REGISTERED_AT
    )
    started = registry.start(experiment.experiment_id, at=REGISTERED_AT + timedelta(minutes=1))
    assert started.status is ExperimentStatus.RUNNING
    with pytest.raises(ValidationError, match="already running"):
        registry.start(experiment.experiment_id, at=REGISTERED_AT + timedelta(minutes=2))


def test_status_counts_include_failures() -> None:
    registry = ExperimentRegistry()
    first = registry.register(
        hypothesis="h", data_version="d", model_version="m", created_at=REGISTERED_AT
    )
    second = registry.register(
        hypothesis="h", data_version="d", model_version="m", created_at=REGISTERED_AT
    )
    registry.complete(first.experiment_id, result={}, at=REGISTERED_AT)
    registry.fail(second.experiment_id, result={}, at=REGISTERED_AT)
    counts = registry.counts_by_status()
    assert counts["COMPLETED"] == 1
    assert counts["FAILED"] == 1
    assert counts["PLANNED"] == 0


def test_experiment_ids_are_unique() -> None:
    ids = {new_experiment_id() for _ in range(200)}
    assert len(ids) == 200


# ---------------------------------------------------------------------------
# The record store
# ---------------------------------------------------------------------------


def test_records_are_append_only(match, prediction) -> None:
    store = RecordStore()
    store.record_match(match)
    store.record_prediction(prediction)
    with pytest.raises(DuplicateRecordError, match="append-only"):
        store.record_prediction(prediction)


def test_the_store_has_no_mutating_api() -> None:
    for forbidden in ("update", "delete", "remove", "drop", "clear", "truncate"):
        assert not hasattr(RecordStore(), forbidden), (
            f"RecordStore.{forbidden} would allow history to be rewritten"
        )


def test_a_prediction_needs_a_known_match(prediction) -> None:
    store = RecordStore()
    with pytest.raises(UnknownReferenceError, match="unknown match"):
        store.record_prediction(prediction)


def test_a_recommendation_needs_a_known_prediction(match) -> None:
    from football_betting.domain import Decision, Market, Recommendation, Selection

    store = RecordStore()
    store.record_match(match)
    orphan = Recommendation(
        recommendation_id="rec-orphan",
        match_id="m-0001",
        prediction_id="pred-does-not-exist",
        created_at=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
        as_of=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
        market=Market.ONE_X_TWO,
        selection=Selection.HOME,
        odds=2.20,
        implied_probability=1 / 2.20,
        model_probability=0.5,
        decision=Decision.BUY,
        reason="orphan",
    )
    with pytest.raises(UnknownReferenceError, match="unknown prediction"):
        store.record_recommendation(orphan)


def test_a_raw_string_is_not_accepted_where_an_enum_belongs(match) -> None:
    """``Decision`` subclasses ``str``, so ``"BUY"`` would otherwise slip through."""
    from football_betting.domain import Decision, Market, Recommendation, Selection

    with pytest.raises(ValidationError, match="must be a Decision member"):
        Recommendation(
            recommendation_id="rec-typo",
            match_id="m-0001",
            prediction_id="pred-0001",
            created_at=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
            as_of=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
            market=Market.ONE_X_TWO,
            selection=Selection.HOME,
            odds=2.20,
            implied_probability=1 / 2.20,
            model_probability=0.5,
            decision="BUY",  # type: ignore[arg-type]
            reason="typo",
        )
    assert Decision.BUY.value == "BUY"


def test_a_bet_needs_a_known_recommendation(match, bet_record) -> None:
    store = RecordStore()
    store.record_match(match)
    with pytest.raises(UnknownReferenceError, match="unknown recommendation"):
        store.record_bet(bet_record)


def test_the_full_chain_records_and_counts(
    match, prediction, recommendation, result, bet_record
) -> None:
    store = RecordStore()
    store.record_match(match)
    store.record_prediction(prediction)
    store.record_recommendation(recommendation)
    store.record_result(result)
    store.record_bet(bet_record)
    assert store.counts() == {
        "matches": 1,
        "predictions": 1,
        "recommendations": 1,
        "results": 1,
        "bets": 1,
    }


def test_row_counts_are_exposed_for_the_run_report() -> None:
    store = RecordStore()
    assert store.counts() == {
        "matches": 0,
        "predictions": 0,
        "recommendations": 0,
        "results": 0,
        "bets": 0,
    }


def test_a_bet_is_flagged_as_logged_by_hand(bet_record) -> None:
    """The record must not read as if the system placed the bet."""
    assert "the system did not place this bet" in (bet_record.note or "")
