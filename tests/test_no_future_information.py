"""Requirement 6: post-match information can never become a pre-match input.

This is the most important test module in the project. Every other mistake is
recoverable; a look-ahead leak silently invalidates every result that follows
from it, and it is invisible in the output.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from football_betting.data import DataProvenance, DataSnapshot
from football_betting.domain import (
    FutureInformationError,
    Market,
    MatchPhase,
    MatchResult,
    NotAnInputError,
    NotImplementedYetError,
    OddsSnapshot,
    Prediction,
    Selection,
    UnknownReferenceError,
    ValidationError,
)
from football_betting.features import (
    PERMITTED_INPUT_TYPES,
    build_features,
    is_post_match,
    validate_observations,
)
from football_betting.models import PredictionRequest, UnimplementedPredictor
from football_betting.records import RecordStore

MORNING = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Outcomes are not inputs
# ---------------------------------------------------------------------------


def test_a_result_is_flagged_post_match(result: MatchResult) -> None:
    assert result.phase is MatchPhase.POST_MATCH
    assert is_post_match(result)


def test_a_result_is_refused_as_an_observation(match, result) -> None:
    with pytest.raises(NotAnInputError, match="post-match"):
        validate_observations(match, MORNING, [result])


def test_a_result_is_refused_even_alongside_valid_quotes(match, odds_snapshot, result) -> None:
    """A single bad element must poison the whole set, not be silently skipped."""
    with pytest.raises(NotAnInputError):
        validate_observations(match, MORNING, [odds_snapshot, result])


def test_a_result_is_refused_when_building_features(match, result) -> None:
    with pytest.raises(NotAnInputError):
        build_features(match, MORNING, [result])


def test_an_unauthorised_type_is_refused(match) -> None:
    class Mystery:
        pass

    with pytest.raises(ValidationError, match="not an authorised input"):
        validate_observations(match, MORNING, [Mystery()])


def test_the_permitted_input_list_is_explicit() -> None:
    assert (OddsSnapshot,) == PERMITTED_INPUT_TYPES, (
        "adding an input type must be a deliberate, reviewed act"
    )


# ---------------------------------------------------------------------------
# Time travel
# ---------------------------------------------------------------------------


def test_an_observation_describing_the_future_is_refused(match) -> None:
    future_quote = OddsSnapshot(
        snapshot_id="odds-future",
        match_id="m-0001",
        market=Market.ONE_X_TWO,
        selection=Selection.HOME,
        decimal_odds=2.0,
        data_time=MORNING + timedelta(hours=1),
        collected_at=MORNING + timedelta(hours=1),
        source="fixture://synthetic",
    )
    with pytest.raises(FutureInformationError, match="describes"):
        validate_observations(match, MORNING, [future_quote])


def test_an_observation_that_had_not_arrived_yet_is_refused(match) -> None:
    """A price that existed but was not yet in our hands is not known."""
    late_delivery = OddsSnapshot(
        snapshot_id="odds-late-delivery",
        match_id="m-0001",
        market=Market.ONE_X_TWO,
        selection=Selection.HOME,
        decimal_odds=2.0,
        data_time=MORNING - timedelta(hours=1),
        collected_at=MORNING + timedelta(minutes=5),
        source="fixture://synthetic",
    )
    with pytest.raises(FutureInformationError, match="was not received until"):
        validate_observations(match, MORNING, [late_delivery])


def test_an_observation_at_or_after_kickoff_is_refused(match, kickoff) -> None:
    in_play = OddsSnapshot(
        snapshot_id="odds-in-play",
        match_id="m-0001",
        market=Market.ONE_X_TWO,
        selection=Selection.HOME,
        decimal_odds=1.5,
        data_time=kickoff + timedelta(minutes=10),
        collected_at=kickoff + timedelta(minutes=10),
        source="fixture://synthetic",
    )
    with pytest.raises(FutureInformationError):
        validate_observations(match, kickoff + timedelta(minutes=20), [in_play])


def test_a_features_at_or_after_kickoff_is_refused(match, kickoff, odds_snapshot) -> None:
    with pytest.raises(FutureInformationError, match="is not before kickoff"):
        validate_observations(match, kickoff, [odds_snapshot])


def test_a_quote_from_another_fixture_is_refused(match, kickoff) -> None:
    other = OddsSnapshot(
        snapshot_id="odds-other",
        match_id="m-9999",
        market=Market.ONE_X_TWO,
        selection=Selection.HOME,
        decimal_odds=2.0,
        data_time=MORNING - timedelta(hours=1),
        collected_at=MORNING - timedelta(hours=1),
        source="fixture://synthetic",
    )
    with pytest.raises(ValidationError, match="belongs to match"):
        validate_observations(match, MORNING, [other])


def test_valid_observations_are_returned_in_time_order(match) -> None:
    def quote(snapshot_id: str, hours_before: int) -> OddsSnapshot:
        moment = MORNING - timedelta(hours=hours_before)
        return OddsSnapshot(
            snapshot_id=snapshot_id,
            match_id="m-0001",
            market=Market.ONE_X_TWO,
            selection=Selection.HOME,
            decimal_odds=2.0 + hours_before / 100,
            data_time=moment,
            collected_at=moment,
            source="fixture://synthetic",
        )

    unordered = [quote("c", 1), quote("a", 5), quote("b", 3)]
    ordered = validate_observations(match, MORNING, unordered)
    assert [o.snapshot_id for o in ordered] == ["a", "b", "c"], (
        "result order must not depend on caller order"
    )


def test_featurisation_is_honestly_unimplemented(match, odds_snapshot) -> None:
    """Guards pass, then the layer admits it cannot build features yet."""
    with pytest.raises(NotImplementedYetError, match="feature construction is not implemented"):
        build_features(match, MORNING, [odds_snapshot])


# ---------------------------------------------------------------------------
# Snapshot knowledge
# ---------------------------------------------------------------------------


def _snapshot(match) -> DataSnapshot:
    """A snapshot covering 08:00-12:00, finalised at 13:00.

    It holds two quotes: one that reached us at 09:00, and one from the same
    upstream moment that only landed at 12:30.
    """
    provenance = DataProvenance(
        source="fixture://synthetic",
        collected_at=MORNING + timedelta(hours=1),
        data_time_start=MORNING - timedelta(hours=4),
        data_time_end=MORNING,
        version="fixture-2026-09-18.1",
        schema="core-0.0.1",
    )
    return DataSnapshot(
        provenance=provenance,
        matches=(match,),
        odds=(
            OddsSnapshot(
                snapshot_id="odds-known",
                match_id="m-0001",
                market=Market.ONE_X_TWO,
                selection=Selection.HOME,
                decimal_odds=2.2,
                data_time=MORNING - timedelta(hours=4),
                collected_at=MORNING - timedelta(hours=3),
                source="fixture://synthetic",
            ),
            OddsSnapshot(
                snapshot_id="odds-not-yet-arrived",
                match_id="m-0001",
                market=Market.ONE_X_TWO,
                selection=Selection.DRAW,
                decimal_odds=3.4,
                data_time=MORNING - timedelta(hours=4),
                collected_at=MORNING + timedelta(minutes=30),
                source="fixture://synthetic",
            ),
        ),
    )


def test_a_snapshot_cannot_describe_the_future(kickoff) -> None:
    with pytest.raises(Exception, match="later than"):
        DataProvenance(
            source="s",
            collected_at=MORNING,
            data_time_start=MORNING - timedelta(hours=1),
            data_time_end=MORNING + timedelta(hours=1),
            version="v",
            schema="s",
        )


def test_a_snapshot_cannot_hold_a_row_outside_its_covered_window(match) -> None:
    provenance = DataProvenance(
        source="s",
        collected_at=MORNING + timedelta(hours=1),
        data_time_start=MORNING - timedelta(hours=4),
        data_time_end=MORNING,
        version="v",
        schema="s",
    )
    stray_quote = OddsSnapshot(
        snapshot_id="odds-outside-window",
        match_id="m-0001",
        market=Market.ONE_X_TWO,
        selection=Selection.HOME,
        decimal_odds=2.2,
        data_time=MORNING + timedelta(hours=3),
        collected_at=MORNING + timedelta(hours=3),
        source="fixture://synthetic",
    )
    with pytest.raises(Exception, match="outside the window"):
        DataSnapshot(provenance=provenance, odds=(stray_quote,))


def test_knowable_at_excludes_a_quote_that_had_not_arrived_yet(match) -> None:
    """The 12:30 delivery was still in transit at 12:00."""
    known = _snapshot(match).knowable_at(MORNING)
    assert [o.snapshot_id for o in known.odds] == ["odds-known"]


def test_knowable_at_excludes_fixtures_before_the_version_was_finalised(match) -> None:
    """No fixture is claimed before the version carrying it was pulled."""
    known = _snapshot(match).knowable_at(MORNING)
    assert known.matches == ()


def test_knowable_at_is_empty_before_anything_arrived(match) -> None:
    before = _snapshot(match).knowable_at(MORNING - timedelta(days=1))
    assert before.odds == ()
    assert before.matches == ()


def test_knowable_at_returns_everything_once_it_has_all_arrived(match) -> None:
    later = _snapshot(match).knowable_at(MORNING + timedelta(hours=2))
    assert len(later.odds) == 2
    assert len(later.matches) == 1


# ---------------------------------------------------------------------------
# Store reconstruction
# ---------------------------------------------------------------------------


def test_state_as_of_hides_a_result_recorded_later(
    match, prediction, recommendation, result
) -> None:
    """The replay must not see a scoreline it had not been told yet."""
    store = RecordStore()
    store.record_match(match)
    store.record_prediction(prediction)
    store.record_recommendation(recommendation)
    store.record_result(result)

    before_recording = result.recorded_at - timedelta(minutes=1)
    state = store.state_as_of(before_recording)
    assert state.results == (), "the scoreline was not yet known at that instant"
    assert len(state.predictions) == 1

    after_recording = result.recorded_at
    assert len(store.state_as_of(after_recording).results) == 1


def test_state_as_of_hides_a_prediction_created_later(match, prediction) -> None:
    store = RecordStore()
    store.record_match(match)
    store.record_prediction(prediction)
    assert store.state_as_of(prediction.created_at - timedelta(seconds=1)).predictions == ()
    assert len(store.state_as_of(prediction.created_at).predictions) == 1


def test_a_prediction_created_after_kickoff_is_refused(match, kickoff) -> None:
    late = Prediction(
        prediction_id="pred-post",
        match_id="m-0001",
        created_at=kickoff + timedelta(minutes=5),
        as_of=kickoff + timedelta(minutes=4),
        model_version="synthetic",
        data_version="d",
        probability_home=0.4,
        probability_draw=0.3,
        probability_away=0.3,
    )
    store = RecordStore()
    store.record_match(match)
    with pytest.raises(FutureInformationError, match="not before kickoff"):
        store.record_prediction(late)


def test_state_as_of_refuses_naive_datetimes(match) -> None:
    store = RecordStore()
    store.record_match(match)
    with pytest.raises(ValidationError, match="timezone-aware"):
        store.state_as_of(datetime(2026, 9, 20, 12, 0))


def test_missing_references_are_refused(result) -> None:
    store = RecordStore()
    with pytest.raises(UnknownReferenceError, match="unknown match"):
        store.record_result(result)


# ---------------------------------------------------------------------------
# The predictor interface cannot reach the future
# ---------------------------------------------------------------------------


def test_prediction_request_rejects_features_built_later(match, prediction) -> None:
    from football_betting.features import FeatureSet

    later_features = FeatureSet(
        match_id="m-0001",
        as_of=MORNING + timedelta(hours=1),
        feature_version="v0",
        values={},
    )
    with pytest.raises(FutureInformationError, match="later than the requested as_of"):
        PredictionRequest(
            match=match,
            features=later_features,
            as_of=MORNING,
            created_at=MORNING,
            data_version="d",
        )


def test_prediction_request_rejects_features_for_another_match(match) -> None:
    from football_betting.features import FeatureSet

    wrong_match = FeatureSet(match_id="m-9999", as_of=MORNING, feature_version="v0", values={})
    with pytest.raises(FutureInformationError, match="not 'm-0001'"):
        PredictionRequest(
            match=match,
            features=wrong_match,
            as_of=MORNING,
            created_at=MORNING,
            data_version="d",
        )


def test_the_placeholder_predictor_refuses_to_predict(match) -> None:
    from football_betting.features import FeatureSet

    request = PredictionRequest(
        match=match,
        features=FeatureSet(match_id="m-0001", as_of=MORNING, feature_version="v0", values={}),
        as_of=MORNING,
        created_at=MORNING,
        data_version="d",
    )
    with pytest.raises(NotImplementedYetError):
        UnimplementedPredictor().predict(request)
