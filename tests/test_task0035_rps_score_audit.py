"""TASK0035: independently test ordinal 1X2 ranked probability score."""
import math
import pytest
from tools.task0035_rps_score_audit import rps3, audit

@pytest.mark.parametrize("label", [0, 1, 2])
def test_perfect_forecast_rps_zero(label):
    p=[float(i==label) for i in range(3)]
    assert rps3(p,label)==0

def test_worst_extreme_rps_one_and_middle_half():
    assert rps3([1,0,0],2)==1
    assert rps3([1,0,0],1)==0.5
    assert rps3([0,0,1],0)==1

def test_rps_is_symmetric_when_home_away_swap():
    p=[0.60,0.25,0.15]
    for label in (0,1,2):
        assert rps3(p,label)==pytest.approx(rps3(p[::-1],2-label))

def test_rps_rejects_non_probabilities():
    with pytest.raises(ValueError):rps3([.4,.4,.4],0)
    with pytest.raises(ValueError):rps3([-.1,.7,.4],1)
    with pytest.raises(ValueError):rps3([.2,.5,.3],3)

def test_identical_prognosis_has_zero_pair_difference():
    rows=[
        {"matchId":"x","day":"2026-10-10","y":0,"independent":[.5,.2,.3],"market":[.5,.2,.3]},
        {"matchId":"z","day":"2026-10-11","y":2,"independent":[.2,.2,.6],"market":[.2,.2,.6]}
    ]
    result=audit(rows,repetitions=60)
    assert result["n"]==2 and result["days"]==2
    assert result["delta_rps"]==0
    assert result["day_cluster_bootstrap95"]==[0,0]
