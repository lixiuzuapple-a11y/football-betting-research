from tools.task0034_espn_bridge import espn_identity,canonical
from tools.task0034_identity_aliases import sporttery_to_espn,espn_to_fd,OFFICIAL_TO_ESPN

def sample(date="2026-10-10T14:00:00Z", home="AVL",away="BRE"):
    return {"date":date,"id":"fixtureA","competitions":[{"competitors":[
        {"homeAway":"home","team":{"id":"10","abbreviation":home}},
        {"homeAway":"away","team":{"id":"20","abbreviation":away}}]}]}

def test_beijing_utc_midnight_and_two_sides():
    assert espn_identity("英超",sample())==("英超","2026-10-10","22:00:00","AVL","BRE")
    assert espn_identity("英超",sample("2026-10-10T16:30:00Z"))[:3]==("英超","2026-10-11","00:30:00")
    assert espn_identity("英超",sample(home="BRE",away="AVL"))[3:]==("BRE","AVL")

def test_authorized_aliases_do_not_guess():
    assert sporttery_to_espn("英超","ASV")=="AVL"
    assert sporttery_to_espn("英超","BRN")=="BRE"
    assert sporttery_to_espn("英超","ASW")=="ASW" # unknown stays unknown
    assert sporttery_to_espn("德甲","ASV")=="ASV" # league scoped
    for league,table in OFFICIAL_TO_ESPN.items():
        assert len(set(table.values()))==len(table) # no two aliases collapse

def test_exact_football_data_names_only():
    names={"Aston Villa","Man City","Man United"}
    assert espn_to_fd("英超","Manchester City",names)=="Man City"
    assert espn_to_fd("英超","Manchester United",names)=="Man United"
    assert espn_to_fd("英超","Manchester C",names) is None
    assert espn_to_fd("西甲","Manchester City",names) is None

def test_canonical_safe_normalization():
    assert canonical("Atlético Madrid")=="atleticomadrid"
    assert canonical("Atlético Madrid")!=canonical("Ath Madrid")
