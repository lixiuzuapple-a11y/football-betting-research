import math
import pytest
from tools.audit_category_b_original_dc import market_price,probabilities,metric

def test_market_odds_used_only_for_comparator():
    p=market_price({"AvgH":"2.0","AvgD":"4.0","AvgA":"4.0"})
    assert p==[0.5,0.25,0.25]
    assert market_price({"AvgH":"0.5","AvgD":"4","AvgA":"4"}) is None

def test_original_model_probs_must_sum_to_one():
    assert probabilities({"home_win":0.6,"draw":0.25,"away_win":0.15}) == pytest.approx([0.6,0.25,0.15])
    with pytest.raises(ValueError):
        probabilities({"home_win":0.5,"draw":0.2,"away_win":0.1})
    with pytest.raises(ValueError):
        probabilities({"home_win":-0.1,"draw":0.3,"away_win":0.8})

def test_metric_is_three_class_sum_brier():
    rows=[{"y":0,"model":[0.8,0.1,0.1]}]
    s=metric(rows,"model")
    assert s["n"]==1
    assert math.isclose(s["log_loss"],-math.log(0.8))
    assert math.isclose(s["brier_sum"],0.06)
    assert s["accuracy"]==1.0
