"""Requirement 2: the core data models instantiate and enforce their invariants."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from football_betting.domain import (
    BetRecord,
    BetRecordStatus,
    Decision,
    Experiment,
    ExperimentStatus,
    Market,
    Match,
    MatchPhase,
    MatchResult,
    MatchStatus,
    OddsSnapshot,
    Prediction,
    Recommendation,
    Selection,
    Team,
    ValidationError,
)


def test_team_instantiates() -> None:
    team = Team(team_id="team-home", name="Home FC", league="EPL")
    assert team.team_id == "team-home"
    assert team.name == "Home FC"


def test_match_instantiates_and_is_frozen(match: Match) -> None:
    assert match.match_id == "m-0001"
    assert match.status is MatchStatus.SCHEDULED
    with pytest.raises(FrozenInstanceError):
        match.league = "Serie A"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (timedelta(hours=-1), MatchPhase.PRE_MATCH),
        (timedelta(minutes=1), MatchPhase.LIVE),
        (timedelta(hours=2, minutes=59), MatchPhase.LIVE),
        (timedelta(hours=3), MatchPhase.POST_MATCH),
        (timedelta(days=1), MatchPhase.POST_MATCH),
    ],
)
def test_phase_at_classifies_the_timeline(
    match: Match, kickoff: datetime, offset: timedelta, expected: MatchPhase
) -> None:
    assert match.phase_at(kickoff + offset) is expected


def test_match_rejects_identical_teams(kickoff: datetime) -> None:
    with pytest.raises(ValidationError, match="must differ"):
        Match(
            match_id="m",
            league="EPL",
            season="2026-27",
            kickoff_at=kickoff,
            home_team_id="same",
            away_team_id="same",
        )


def test_odds_snapshot_instantiates(odds_snapshot: OddsSnapshot) -> None:
    assert odds_snapshot.decimal_odds == pytest.approx(2.20)
    assert odds_snapshot.market is Market.ONE_X_TWO
    assert odds_snapshot.selection is Selection.HOME


def test_odds_snapshot_rejects_odds_at_or_below_one(kickoff: datetime) -> None:
    with pytest.raises(ValidationError, match=r"must be > 1\.0"):
        OddsSnapshot(
            snapshot_id="odds",
            match_id="m-0001",
            market=Market.ONE_X_TWO,
            selection=Selection.HOME,
            decimal_odds=1.0,
            data_time=kickoff - timedelta(hours=8),
            collected_at=kickoff - timedelta(hours=7),
            source="fixture://synthetic",
        )


def test_odds_snapshot_rejects_data_newer_than_collection(kickoff: datetime) -> None:
    with pytest.raises(ValidationError, match="must not be later than"):
        OddsSnapshot(
            snapshot_id="odds",
            match_id="m-0001",
            market=Market.ONE_X_TWO,
            selection=Selection.HOME,
            decimal_odds=2.0,
            data_time=kickoff - timedelta(hours=7),
            collected_at=kickoff - timedelta(hours=8),
            source="fixture://synthetic",
        )


def test_prediction_instantiates(prediction: Prediction) -> None:
    assert prediction.match_id == "m-0001"
    assert prediction.probabilities() == pytest.approx((0.50, 0.26, 0.24))


def test_prediction_rejects_as_of_after_creation(kickoff: datetime) -> None:
    with pytest.raises(ValidationError, match="as_of"):
        Prediction(
            prediction_id="p",
            match_id="m-0001",
            created_at=kickoff - timedelta(hours=8),
            as_of=kickoff - timedelta(hours=7),
            model_version="v",
            data_version="d",
            probability_home=0.5,
            probability_draw=0.3,
            probability_away=0.2,
        )


def test_recommendation_instantiates(recommendation: Recommendation) -> None:
    assert recommendation.decision is Decision.BUY
    assert recommendation.odds == pytest.approx(2.20)
    assert recommendation.implied_probability == pytest.approx(1 / 2.20)
    assert recommendation.edge == pytest.approx(0.10)
    assert recommendation.reason


def test_bet_record_instantiates(bet_record: BetRecord) -> None:
    assert bet_record.status is BetRecordStatus.RECORDED
    assert bet_record.profit is None, "an unsettled bet has no profit"


def test_bet_record_computes_profit_when_settled(bet_record: BetRecord) -> None:
    settled = BetRecord(
        bet_record_id=bet_record.bet_record_id,
        recommendation_id=bet_record.recommendation_id,
        match_id=bet_record.match_id,
        placed_at=bet_record.placed_at,
        recorded_at=bet_record.recorded_at,
        stake=bet_record.stake,
        decimal_odds=bet_record.decimal_odds,
        status=BetRecordStatus.SETTLED,
        payout=22.0,
    )
    assert settled.profit == pytest.approx(12.0)


def test_match_result_instantiates_and_indexes(result: MatchResult) -> None:
    assert result.outcome_index == 0, "2-1 is a home win"
    assert result.phase is MatchPhase.POST_MATCH


def test_match_result_rejects_negative_goals(kickoff: datetime) -> None:
    with pytest.raises(ValidationError, match="must be >= 0"):
        MatchResult(
            match_id="m",
            kickoff_at=kickoff,
            finished_at=kickoff + timedelta(hours=2),
            recorded_at=kickoff + timedelta(hours=3),
            home_goals=-1,
            away_goals=0,
        )


def test_match_result_rejects_recording_before_the_final_whistle(kickoff: datetime) -> None:
    with pytest.raises(ValidationError, match="recorded_at"):
        MatchResult(
            match_id="m",
            kickoff_at=kickoff,
            finished_at=kickoff + timedelta(hours=2),
            recorded_at=kickoff + timedelta(hours=1),
            home_goals=1,
            away_goals=0,
        )


def test_experiment_instantiates(kickoff: datetime) -> None:
    experiment = Experiment(
        experiment_id="exp-0001",
        hypothesis="A rising market implies information",
        data_version="fixture-2026-09-18.1",
        model_version="none",
        created_at=kickoff - timedelta(days=1),
        parameters={"min_edge": 0.02},
    )
    assert experiment.status is ExperimentStatus.PLANNED
    assert experiment.result is None


def test_experiment_parameters_are_read_only(kickoff: datetime) -> None:
    parameters = {"min_edge": 0.02}
    experiment = Experiment(
        experiment_id="exp-0002",
        hypothesis="h",
        data_version="d",
        model_version="m",
        created_at=kickoff - timedelta(days=1),
        parameters=parameters,
    )
    parameters["min_edge"] = 0.99  # mutate the caller's dict afterwards
    assert experiment.parameters["min_edge"] == pytest.approx(0.02)
    with pytest.raises(TypeError):
        experiment.parameters["min_edge"] = 0.5  # type: ignore[index]


def test_naive_datetimes_are_rejected_everywhere(kickoff: datetime) -> None:
    naive = datetime(2026, 9, 20, 18, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        Match(
            match_id="m",
            league="EPL",
            season="2026-27",
            kickoff_at=naive,
            home_team_id="a",
            away_team_id="b",
        )
    with pytest.raises(ValidationError, match="timezone-aware"):
        MatchResult(
            match_id="m",
            kickoff_at=kickoff,
            finished_at=kickoff + timedelta(hours=2),
            recorded_at=datetime(2026, 9, 20, 21, 0),
            home_goals=0,
            away_goals=0,
        )


def test_utc_normalisation_helper() -> None:
    from football_betting.domain import to_utc

    offset_time = datetime(2026, 9, 20, 20, 0, tzinfo=timezone(timedelta(hours=2)))
    assert to_utc(offset_time, "t") == datetime(2026, 9, 20, 18, 0, tzinfo=timezone.utc)
