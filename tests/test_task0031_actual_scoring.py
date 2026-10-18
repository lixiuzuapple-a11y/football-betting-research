import datetime as dt
from tools.task0031_actual_scoring import quote,metric

M={"had":{"h":"2.0","d":"3.0","a":"4.0","hf":"0","df":"0","af":"0","updateDate":"2026-10-11","updateTime":"15:00:00"},"matchDate":"2026-10-11","matchTime":"18:00:00","matchStatus":"Selling","sellStatus":1,"poolList":[{"poolCode":"HAD","poolStatus":"Selling"}]}
def test_time_cutoff_and_de_vig():
 q=quote(M,"2026-10-11T16:00:00+08:00","strict")
 assert q and abs(sum(q["p"])-1)<1e-12
 assert quote(M,"2026-10-11T18:00:00+08:00","strict") is None
 assert quote(M,"2026-10-11T14:00:00+08:00","strict") is None
def test_status_guard():
 assert quote({**M,"matchStatus":"Closed"},"2026-10-11T16:00:00+08:00","strict") is None
 assert quote({**M,"matchStatus":"Closed"},"2026-10-11T16:00:00+08:00","numeric") is not None
def test_metrics_known():
 x=metric([{"p":[.8,.1,.1],"y":0}])
 assert x["n"]==1 and x["accuracy"]==1
 assert abs(x["logloss"]+__import__("math").log(.8))<1e-12
 assert abs(x["brier_sum"]-.06)<1e-12
