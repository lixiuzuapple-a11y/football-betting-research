import math
import pytest
from tools.task0038_teams import HF_TEAM_BRIDGE
from tools.task0038_common_elo_model_gate import dav_probs,elo_update,metrics,DSU,TRAIN_START,CUTOFF,K,HOME_ADV,DRAW_WEIGHT

def test_predeclared_parameters_and_dates():
    assert (K,HOME_ADV,DRAW_WEIGHT)==(20.,50.,.7)
    assert TRAIN_START.isoformat()=="2025-07-01T00:00:00"
    assert CUTOFF.isoformat()=="2026-07-05T00:00:00"

def test_davidson_three_way_proper_probability():
    for home,away in [(1500,1500),(1900,1400),(1200,1740)]:
        p=dav_probs(home,away)
        assert len(p)==3 and all(0<x<1 for x in p)
        assert sum(p)==pytest.approx(1.,abs=1e-12)

def test_elo_win_and_loss_zero_sum():
    a,b=elo_update(1500,1500,4,0)
    assert a>1500 and b<1500
    assert a+b==pytest.approx(3000)
    a,b=elo_update(1500,1500,0,5)
    assert a<1500 and b>1500
    assert a+b==pytest.approx(3000)

def test_connected_component_requires_observed_edge():
    g=DSU()
    g.union(1,2);g.union(3,4)
    assert g.find(1)==g.find(2)
    assert g.find(1)!=g.find(4)
    g.union(2,3)
    assert g.find(1)==g.find(4)

def test_wrong_probability_scores_worse():
    p=[{"y":0,"model":[.8,.1,.1],"market":[.1,.1,.8]},
       {"y":1,"model":[.1,.8,.1],"market":[.1,.1,.8]},
       {"y":2,"model":[.1,.1,.8],"market":[.8,.1,.1]}]
    m=metrics(p,"model");o=metrics(p,"market")
    assert m["n"]==3 and m["accuracy"]==1.
    assert m["logloss"]<o["logloss"]
    assert m["brier3"]<o["brier3"]
    assert m["rps"]<o["rps"]

def test_hf_aliases_are_frozen_id_based():
    assert len(HF_TEAM_BRIDGE)==70
    assert HF_TEAM_BRIDGE["Internazionale"]["hf_name"]=="Inter"
    assert HF_TEAM_BRIDGE["Internazionale"]["id"]==159
    assert HF_TEAM_BRIDGE["Palmeiras"]["id"]==423
    assert HF_TEAM_BRIDGE["Arsenal"]["id"]==3
    assert len({v["id"] for v in HF_TEAM_BRIDGE.values()})==70
