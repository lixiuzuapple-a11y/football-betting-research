"""TASK0051 adversarial controls: bookmaker-probability history is NOT PIT."""
import datetime as dt
import math

import pytest

from tools import task0051_market_overlap_audit as audit


def source_fixture(*, minutes=0, country="Ireland"):
    return {"match_id": 1, "when": dt.datetime(2026, 6, 12, 17, 0)
            + dt.timedelta(minutes=minutes), "country": country,
            "league_id": 4, "gh": 3, "ga": 1}


def source_market(*, kickoff="2026-06-12T17:00:00+00:00",
                  country="Ireland", home="Derry City", away="Bohemians"):
    return {"kickoff_utc": kickoff, "country": country,
            "home": home, "away": away, "result": "2"}


def index_one(item=None):
    return {("derrycity", "bohemians"): {1: item or source_fixture()}}


def test_exact_name_time_country_and_single_identity_only():
    x, why = audit.associate(source_market(), index_one())
    assert x["match_id"] == 1 and why == "ok"
    # Published result is deliberately wrong; identity cannot look at outcomes.
    assert source_market()["result"] == "2"
    x, why = audit.associate(source_market(country="Brazil"), index_one())
    assert x is None and why == "unmatched_identity_or_time"
    x, why = audit.associate(source_market(away="Bohemians FC"), index_one())
    assert x is None and why == "unmatched_identity_or_time"
    x, why = audit.associate(source_market(kickoff="2026-06-12T18:02:00+00:00"), index_one())
    assert x is None and why == "unmatched_identity_or_time"


def test_ambiguous_ids_refused_without_score_tie_break():
    z = source_fixture()
    idx = index_one()
    idx[("derrycity", "bohemians")][2] = dict(z, match_id=2, gh=0, ga=2)
    x, why = audit.associate(source_market(), idx)
    assert x is None and why == "ambiguous"


def test_timezones_and_bad_dates_fail_closed():
    x, why = audit.associate(
        source_market(kickoff="2026-06-12T18:00:00+01:00"), index_one()
    )
    assert x["match_id"] == 1 and why == "ok"
    for bad in ("not-a-time", "2026-06-12T17:00:00", "2027-01-01T00:00:00Z"):
        x, reason = audit.associate(source_market(kickoff=bad), index_one())
        assert x is None and reason in ("bad_kickoff", "out_of_window")


def test_team_name_only_diacritic_and_punctuation_folding():
    assert audit.normalize_team("HJK Helsinki") == "hjkhelsinki"
    assert audit.normalize_team("St. Pátřick's") == "stpatricks"
    assert audit.normalize_team("FC United") != audit.normalize_team("United")


@pytest.mark.parametrize("raw", [
    ["", "3", "4"], ["0.5", "3", "4"],
    ["nan", "3", "4"], ["inf", "3", "4"],
    ["2", "-3", "4"], ["2", "3"],
])
def test_invalid_bookmaker_quotes_rejected(raw):
    assert audit.read_odds(raw) is None


def test_no_zero_or_nan_probabilities_enter_scoring():
    p = audit.read_odds(["2.0", "3.5", "4.2"])
    assert p is not None and sum(p) == pytest.approx(1.0)
    ll, brier = audit.metric(p, 2)
    assert ll == pytest.approx(-math.log(p[2]))
    assert brier == pytest.approx(sum((p[i]-int(i == 2))**2 for i in range(3)))
    for bad in ([0.0, .5, .5], [float("nan"), .5, .5],
                [1.0, .0, .0], [.5, .3, .3]):
        with pytest.raises(ValueError):
            audit.metric(bad, 1)


def test_market_fair_prob_unormalized_rounding_only():
    assert audit.read_fair(["0.3333", "0.3333", "0.3333"]) is not None
    assert audit.read_fair(["0.4", "0.3", "0.2"]) is None
    assert audit.read_fair(["0.4", "nan", "0.6"]) is None


def test_daily_bootstrap_fixed_seed_and_direction():
    v = [
        {"date": "2026-06-11", "market_logloss": .8, "poisson_logloss": 1.0},
        {"date": "2026-06-11", "market_logloss": .6, "poisson_logloss": 1.1},
        {"date": "2026-06-12", "market_logloss": .9, "poisson_logloss": 1.1},
    ]
    first = audit.daily_paired_bootstrap(v, draws=200)
    assert first == audit.daily_paired_bootstrap(v, draws=200)
    assert first["upper_95"] < 0
    assert first["days"] == 2
    assert audit.daily_paired_bootstrap(v[:2])["lower_95"] is None
