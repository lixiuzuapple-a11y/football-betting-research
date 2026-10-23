import datetime as dt
from tools.task0037_reviewed_cup_links import APPROVED
from tools.task0037_cup_identity_audit import official_to_event_match, CHAMPIONS

def fixture():
    return {"leagueAbbName":"欧冠","matchDate":"2026-10-14","matchTime":"00:45:00","homeTeamId":"179","awayTeamId":"1060","homeTeamAbbEnName":"LEN","awayTeamAbbEnName":"SPO"}
def original():
    return {"official_h_zh":"朗斯","official_a_zh":"里斯本竞技","official_hid":"179","official_aid":"1060","official_hcode":"LEN","official_acode":"SPO"}
def event():
    return {"id":"401915418","league":"欧冠","utc":dt.datetime(2026,10,13,16,45),"home_id":"100","away_id":"200","home":"Lens","away":"Sporting CP"}
def approval():
    return {"event_id":"401915418","official_chinese":["朗斯","里斯本竞技"],"espn_display":["Lens","Sporting CP"]}
def test_correct_identity_with_no_score_or_odds_input():
    assert official_to_event_match(fixture(),original(),approval(),event())
def test_same_kickoff_wrong_teams_rejected():
    e=event();e["home"]="Sabah FK";e["away"]="Slavia Prague"
    assert not official_to_event_match(fixture(),original(),approval(),e)
def test_team_id_and_order_matters():
    f=fixture();f["homeTeamId"]="1060"
    assert not official_to_event_match(f,original(),approval(),event())
    a=approval();a["official_chinese"].reverse()
    assert not official_to_event_match(fixture(),original(),a,event())
def test_wrong_league_and_1_minute_offset_rejected():
    e=event();e["league"]="欧罗巴"
    assert not official_to_event_match(fixture(),original(),approval(),e)
    e=event();e["utc"]+=dt.timedelta(minutes=1)
    assert not official_to_event_match(fixture(),original(),approval(),e)
def test_frozen_cup_approval_35_unique():
    assert len(APPROVED)==35
    assert len(set(x["event_id"] for x in APPROVED.values()))==35
    assert set(CHAMPIONS)=={"欧冠","欧罗巴","欧协联","亚冠精英","解放者杯"}
