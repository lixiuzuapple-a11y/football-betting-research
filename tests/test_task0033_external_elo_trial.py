import math
from tools.task0033_external_elo_trial import elo_p,de_vig,score,update

def test_elo_probabilities():
 p=elo_p(1500,1500)
 assert len(p)==3 and abs(sum(p)-1)<1e-12
 assert p[0]>p[2]
 assert elo_p(1700,1500)[0]>p[0]

def test_market_solely_comparator():
 assert de_vig({"AvgH":"2","AvgD":"4","AvgA":"4"})==[.5,.25,.25]
 assert de_vig({"AvgH":"0","AvgD":"4","AvgA":"4"}) is None

def test_elo_update_and_score():
 h,a=update(1500,1500,0)
 assert h>1500 and a<1500
 assert score([.7,.2,.1],0)[2]==1
 assert math.isclose(score([.7,.2,.1],0)[0],-math.log(.7))
