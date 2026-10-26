"""Phase3 safeguards: chronological batching, no outcome leakage, source integrity."""
import datetime as dt
import random

import pytest
from tools.phase3_multimodel_walkforward import Game, evaluate, deduplicate, poisson_1x2, State


def make(id, date, home, away, home_goals=2, away_goals=1, league=10):
    when=dt.datetime.combine(dt.date.fromisoformat(date), dt.time(19,0))
    return Game(id, when.date(), when, league, home, away, home_goals, away_goals)


def fixture_set():
    r=[]
    # Enough league and team home/away history to qualify full-model predictions.
    for i in range(100):
        a=100+(i%5)
        b=100+((i+1+i//5)%5)
        if a==b:
            b=100+((i+2)%5)
        r.append(make(i+1, "2025-12-"+str(1+i//4).zfill(2), a, b,
                      (i%4), (i+1)%3))
    r.append(make(10001, "2026-01-01", 100, 102, 1, 0))
    r.append(make(10002, "2026-01-02", 102, 100, 2, 1))
    return r


def test_probability_contract():
    for h,a in [(0.2,0.2),(2,1),(5,5)]:
        p=poisson_1x2(h,a)
        assert all(0<v<1 for v in p) and sum(p)==pytest.approx(1.0,abs=1e-12)
    with pytest.raises(ValueError,match="unsafe"):
        poisson_1x2(0,2)


def test_date_embargo_and_eligible_all_models():
    r=evaluate(fixture_set())
    assert r["test_rows"]==2
    assert r["train_latest_date_as_of_last_test"]=="2025-12-25"
    assert r["model_metrics"]["global_frequency"]["n"]==2
    assert r["model_metrics"]["league_frequency"]["n"]==2
    assert r["model_metrics"]["pooled_elo_davidson"]["n"]==2
    assert r["model_metrics"]["league_poisson"]["n"]==2
    for row in r["details"]:
        assert row["last_actual_training_date"] <= row["max_allowed_training_date"]


def test_no_future_label_contamination_and_order_independence():
    r=fixture_set()
    baseline=evaluate(r)
    changed=list(r)
    g=changed[-1]
    changed[-1]=make(g.id, g.date.isoformat(), g.home, g.away, 0, 8, g.league)
    after=evaluate(changed)
    assert [x["predictions"] for x in after["details"]] == [
        x["predictions"] for x in baseline["details"]
    ]
    shuffled=list(r)
    random.Random(20261026).shuffle(shuffled)
    assert [x["predictions"] for x in evaluate(shuffled)["details"]] == [
        x["predictions"] for x in baseline["details"]
    ]


def test_conflicting_duplicate_score_refused():
    r=fixture_set()
    g=r[0]
    with pytest.raises(ValueError, match="conflicting final scores"):
        deduplicate(r+[make(9999,g.date.isoformat(),g.home,g.away,9,9,g.league)])
    cleaned,n=deduplicate(r+[make(9999,g.date.isoformat(),g.home,g.away,g.gh,g.ga,g.league)])
    assert n==1
    assert len(cleaned)==len(r)


def test_training_rejects_unexpected_or_corrupted_match():
    with pytest.raises(ValueError,match="period"):
        evaluate([make(1,"2027-01-01",10,11)])
    with pytest.raises(ValueError,match="invalid fixture"):
        evaluate([make(2,"2026-01-01",11,11)])
    with pytest.raises(ValueError,match="provider row ID"):
        deduplicate([make(1,"2025-12-01",1,2),make(1,"2025-12-02",1,3)])


def test_date_only_embargo_blocks_previous_day():
    base=[make(i+1,"2025-12-15",i%3+10,(i+1)%3+10) for i in range(25)]
    a=make(200,"2025-12-31",10,11,3,0)
    b=make(201,"2026-01-01",10,11,1,0)
    x=evaluate(base+[a,b])
    y=evaluate(base+[make(200,"2025-12-31",10,11,0,8),b])
    assert x["details"][0]["predictions"]==y["details"][0]["predictions"]
    assert x["details"][0]["last_actual_training_date"]=="2025-12-15"
