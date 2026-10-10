import pytest
from tools.task0022_result_join import strict_join

def test_strict_join_flags_missing_score_and_conflicts():
    source={"123":{"businessDate":"2026-10-09","homeTeamId":1,"awayTeamId":2}}
    r=[{"matchId":123,"businessDate":"2026-10-09","homeTeamId":1,"awayTeamId":2}]
    assert strict_join(source,r)[0]["status"]=="SCORE_NOT_VERIFIED"
    r[0]["homeTeamId"]=3
    assert strict_join(source,r)[0]["status"]=="CONFLICT"
    assert strict_join(source,[{"matchId":"456"}])[0]["status"]=="UNMATCHED"
    with pytest.raises(ValueError):strict_join(source,[{"matchId":"123"},{"matchId":"123"}])
