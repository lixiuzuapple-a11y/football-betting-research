"""TASK0039 adversarial gates for external entity integrity and AFC history."""
import datetime as dt
import hashlib
import json
import pytest
from tools.task0038_teams import HF_TEAM_BRIDGE
from tools.task0039_afc_prior_safety import (
    ESPN_AFC_TO_HF, SKIP_ESPN_AFC_IDS, parse_espn_prior,
    distrust_country_mismatches, fit_chronological, FIRST_TRAIN,
    SOURCE_CUTOFF, dav_probs,
)

def test_al_ahli_means_jeddah_not_bahrain_and_mapping_is_unique():
    assert HF_TEAM_BRIDGE["Al Ahli"]=={"id":922,"hf_name":"Al-Ahli Jeddah"}
    assert ESPN_AFC_TO_HF["8346"]==(922,"Al-Ahli Jeddah")
    assert ESPN_AFC_TO_HF["790"]==(1528,"Shabab Al Ahli Dubai")
    assert 100005580 not in [pair[0] for pair in ESPN_AFC_TO_HF.values()]
    assert len(set(a for a,_ in ESPN_AFC_TO_HF.values()))==22
    assert set(SKIP_ESPN_AFC_IDS)=={"8217","9655"}

def test_cross_country_same_id_is_distrusted():
    rows=[(569,100,"Norway")]*8+[(569,200,"Morocco")]*7
    z=distrust_country_mismatches(rows,{569,100,200})
    assert "569" in z and "100" not in z

def test_country_aliases_not_false_collisions():
    rows=[(922,935,"Saudi-Arabia")]*6+[(922,937,"Saudi Arabia")]*9
    rows+= [(1532,1550,"UAE")]*7+[(1532,1550,"United-Arab-Emirates")]*8
    assert distrust_country_mismatches(rows,{922,935,937,1532,1550})=={}

def test_same_time_games_are_updated_together_and_not_future():
    t=dt.datetime(2025,9,15,15)
    g,elo,played=fit_chronological([(t,11,12,3,0),(t,11,13,0,1)],[])
    assert played[11]==2 and g.find(12)==g.find(13)
    assert abs(elo[11]-1500)<20
    with pytest.raises(ValueError,match="future/old"):
        fit_chronological([(SOURCE_CUTOFF,11,12,1,0)],[])

def test_espn_source_sha_tamper_detected_before_read(tmp_path):
    (tmp_path/"ESPN-AFC-MANIFEST.json").write_text(
        json.dumps({"sources":[{"year":"2025","response_sha256":"0"*64,"n_raw":1}]}),encoding="utf-8")
    (tmp_path/"ESPN-AFC-RAW-2025.json").write_text('{"events":[]}',encoding="utf-8")
    with pytest.raises(ValueError,match="SHA mismatch"):
        parse_espn_prior(tmp_path)

def test_2026_oct_future_not_in_2025_26_training(tmp_path):
    def event(event_id,date):
        return {"id":event_id,"date":date,
                "status":{"type":{"name":"STATUS_FULL_TIME","shortDetail":"FT"}},
                "competitions":[{"competitors":[
                    {"homeAway":"home","team":{"id":"8346"},"score":"2"},
                    {"homeAway":"away","team":{"id":"7138"},"score":"1"}]}]}
    files=[("2025",[event("001","2025-10-01T16:00Z")]),
           ("2026",[event("002","2026-10-15T16:00Z")])]
    sources=[]
    for yr,events in files:
        raw=json.dumps({"events":events}).encode()
        (tmp_path/f"ESPN-AFC-RAW-{yr}.json").write_bytes(raw)
        sources.append({"year":yr,"response_sha256":hashlib.sha256(raw).hexdigest(),"n_raw":len(events)})
    (tmp_path/"ESPN-AFC-MANIFEST.json").write_text(json.dumps({"sources":sources}),encoding="utf-8")
    real,n=parse_espn_prior(tmp_path)
    assert n==2 and len(real)==1
    assert real[0]["espn_id"]=="001"
    assert real[0]["gh"]==2 and real[0]["ga"]==1
