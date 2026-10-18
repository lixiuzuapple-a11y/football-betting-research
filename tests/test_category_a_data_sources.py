from tools.audit_category_a_data_sources import exact_matches, final_score

FIXTURES={
    "1":{"leagueAbbName":"英超","matchDate":"2026-10-10","matchTime":"22:00:00",
         "homeTeamAbbEnName":"CHE","awayTeamAbbEnName":"BOU"},
    "2":{"leagueAbbName":"英超","matchDate":"2026-10-10","matchTime":"22:00:00",
         "homeTeamAbbEnName":"IPS","awayTeamAbbEnName":"FUL"},
    "3":{"leagueAbbName":"西甲","matchDate":"2026-10-10","matchTime":"22:00:00",
         "homeTeamAbbEnName":"CHE","awayTeamAbbEnName":"BOU"}
}

def event(home="CHE",away="BOU",status="STATUS_FULL_TIME",when="2026-10-10T14:00Z"):
    return {"id":"ESPN1","date":when,"status":{"type":{"name":status}},
            "competitions":[{"competitors":[
                {"homeAway":"home","team":{"abbreviation":home},"score":"5"},
                {"homeAway":"away","team":{"abbreviation":away},"score":"1"}]}]}

def test_strict_time_and_both_teams_and_league():
    assert exact_matches(FIXTURES,event())==["1"]
    assert exact_matches(FIXTURES,event("IPS","FUL"))==["2"]
    assert exact_matches(FIXTURES,event("BOU","CHE"))==[]
    assert exact_matches(FIXTURES,event(when="2026-10-10T13:59Z"))==[]

def test_multiple_events_same_kickoff_do_not_merge():
    assert exact_matches(FIXTURES,event())==["1"]
    assert exact_matches(FIXTURES,event("IPS","FUL"))==["2"]

def test_live_score_not_a_final_label():
    assert final_score(event())==[5,1]
    assert final_score(event(status="STATUS_SECOND_HALF")) is None
    assert final_score(event(status="STATUS_SCHEDULED")) is None

def test_malformed_espn_response_is_not_matchable():
    assert exact_matches(FIXTURES,{"id":"junk"})==[]
    assert final_score({"id":"junk"}) is None
