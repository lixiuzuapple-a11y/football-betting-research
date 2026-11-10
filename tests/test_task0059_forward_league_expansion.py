"""TASK0059: competition expansion must never weaken the original team/PIT gate."""
import datetime as dt

import pytest

from tools import task0043_prospective_multimodel_freeze as gate

UTC = dt.timezone.utc
FROZEN_AT = dt.datetime(2026, 11, 7, 8, 0, tzinfo=UTC)
OLD = {
    "法甲": (9, "Ligue 1", "France"),
    "挪超": (23, "Eliteserien", "Norway"),
}
NEW = {
    "英超": (1, "Premier League", "England"),
    "西甲": (5, "La Liga", "Spain"),
    "意甲": (7, "Serie A", "Italy"),
    "德甲": (11, "Bundesliga", "Germany"),
    "荷甲": (13, "Eredivisie", "Netherlands"),
    "葡超": (14, "Primeira Liga", "Portugal"),
    "日职": (21, "J1 League", "Japan"),
    "韩职": (38, "K League 1", "South Korea"),
    "巴甲": (19, "Serie A", "Brazil"),
    "英冠": (2, "Championship", "England"),
    "法乙": (10, "Ligue 2", "France"),
    "德乙": (12, "2. Bundesliga", "Germany"),
}
PREAPPROVED = {"13": (19, "曼彻斯特联"), "2": (14, "阿斯顿维拉")}


def fixture(*, league="英超", home_id="13", away_id="2",
            home="曼彻斯特联", away="阿斯顿维拉",
            match_date="2026-11-08", match_time="00:30"):
    return {
        "matchId": "2042632", "leagueAbbName": league,
        "matchDate": match_date, "matchTime": match_time,
        "homeTeamId": home_id, "awayTeamId": away_id,
        "homeTeamAllName": home, "awayTeamAllName": away,
    }


def test_all_14_league_ids_names_countries_are_explicit_frozen_exact():
    assert gate.ELIGIBLE_LEAGUES == {**OLD, **NEW}
    assert len(gate.ELIGIBLE_LEAGUES) == 14
    assert len({x[0] for x in gate.ELIGIBLE_LEAGUES.values()}) == 14
    assert gate.EXPECTED_HISTORY_MANIFEST == (
        "eb3c37793866a27f8c1520c78a69e6098fdf79f08622b37fed64070fa1f8748f"
    )
    assert gate.EXPECTED_BRIDGE_SHA == (
        "13d373dbab8363e606cfaf39c478b6035c35c86ad0ffcbf4c53e6e5014f63f2f"
    )


def test_new_epl_identity_with_old_approved_both_teams_can_qualify():
    allowed, rejected = gate.qualify_fixtures([fixture()], PREAPPROVED, FROZEN_AT)
    assert rejected == {}
    assert len(allowed) == 1
    assert allowed[0]["hf_league_id"] == 1
    assert allowed[0]["hf_home_id"] == 19
    assert allowed[0]["hf_away_id"] == 14
    assert allowed[0]["official_home_id"] == "13"


@pytest.mark.parametrize("change,reason", [
    ({"league": "英联杯"}, "league_not_approved_for_forward_model"),
    ({"home_id": "777777"}, "missing_preapproved_both_team_identity"),
    ({"away_id": "888888"}, "missing_preapproved_both_team_identity"),
    ({"away_id": "13"}, "missing_preapproved_both_team_identity"),
    ({"home": "Manchester United"}, "approved_team_name_conflict"),
    ({"away": "阿斯顿维拉U21"}, "approved_team_name_conflict"),
    ({"match_date": "2026-11-07", "match_time": "15:30"},
     "not_future_at_freeze"),
])
def test_expansion_rejects_unverified_teams_names_or_postkickoff(change, reason):
    allowed, rejected = gate.qualify_fixtures(
        [fixture(**change)], PREAPPROVED, FROZEN_AT
    )
    assert not allowed
    assert rejected == {reason: 1}


def test_new_and_old_leagues_do_not_change_original_team_ids():
    # A freshly approved league never confers an identity exemption.
    for name in gate.ELIGIBLE_LEAGUES:
        rows, rejected = gate.qualify_fixtures(
            [fixture(league=name, home_id="999999")], PREAPPROVED, FROZEN_AT
        )
        assert not rows
        assert rejected["missing_preapproved_both_team_identity"] == 1


def test_no_unrelated_club_bridge_or_new_history_is_auto_authorized():
    from tools.task0038_teams import HF_TEAM_BRIDGE
    assert len(HF_TEAM_BRIDGE) == 70
    assert gate.EXPECTED_HISTORY_ROWS == 53705
    assert gate.HISTORY_LAST_EXCLUSIVE == dt.date(2026, 7, 5)
    assert gate.HISTORY_AVAILABLE_AT < FROZEN_AT


def test_old_task0058_observed_coverage_retains_original_two_league_policy():
    # Prior descriptive 34 / 3 / 1 cohort must not silently become 34 / N / N.
    from tools.task0058_forward_supply_audit import TASK0058_FROZEN_LEAGUES
    assert TASK0058_FROZEN_LEAGUES == OLD
    new, new_rejected = gate.qualify_fixtures([fixture()], PREAPPROVED, FROZEN_AT)
    prior, prior_rejected = gate.qualify_fixtures(
        [fixture()], PREAPPROVED, FROZEN_AT,
        approved_leagues=TASK0058_FROZEN_LEAGUES,
    )
    assert len(new) == 1 and not new_rejected
    assert prior == []
    assert prior_rejected == {"league_not_approved_for_forward_model": 1}


def test_explicit_old_policy_still_accepts_original_ligue1_fixture():
    from tools.task0058_forward_supply_audit import TASK0058_FROZEN_LEAGUES
    bridge = {"179": (214, "朗斯"), "182": (209, "马赛")}
    match = fixture(league="法甲", home_id="179", away_id="182",
                    home="朗斯", away="马赛")
    accepted, rejected = gate.qualify_fixtures(
        [match], bridge, FROZEN_AT,
        approved_leagues=TASK0058_FROZEN_LEAGUES,
    )
    assert len(accepted) == 1
    assert rejected == {}
    assert accepted[0]["hf_league_id"] == 9
