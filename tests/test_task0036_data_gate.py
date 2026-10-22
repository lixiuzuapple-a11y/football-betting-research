import pytest
from datetime import datetime
from tools.task0036_hf_identity_gate import ABBR, sporttery_codes, name_pair_matches, normalize_named
from tools.task0036_strict_time_gate import assert_strict_temporal_fold, validate_all_folds

def test_hand_approved_sporttery_to_espn_both_teams():
    assert sporttery_codes("瑞超","MJB","DGF")==("MJA","DEG")
    assert sporttery_codes("荷甲","FCZ","CBU")==("PEC","CAM")
    assert sporttery_codes("美职","SLC","LAG")==("STL","LA")

def test_unknown_alias_is_rejected_and_is_league_scoped():
    assert sporttery_codes("美职","FEY","AZZ") is None
    assert sporttery_codes("荷甲","FEY","UNKNOWN") is None

def test_alias_mapping_cannot_collapse_two_clubs():
    for league,codes in ABBR.items():
        assert len(set(codes.values()))==len(codes),league
    with pytest.raises(ValueError):
        sporttery_codes("瑞超","MJB","MJB")

def test_exact_team_name_pair_is_ordered_and_not_fuzzy():
    assert name_pair_matches("Mjällby AIF","Degerfors IF","Mjallby","Degerfors")
    assert name_pair_matches("Feyenoord Rotterdam","AZ Alkmaar","Feyenoord","AZ Alkmaar")
    assert name_pair_matches("St. Louis CITY SC","LA Galaxy","St. Louis City","Los Angeles Galaxy")
    assert not name_pair_matches("AZ Alkmaar","Feyenoord Rotterdam","Feyenoord","AZ Alkmaar")
    assert not name_pair_matches("Mjällby AIF","Degerfors IF","Malmö FF","Kalmar")
    assert normalize_named("FC Utrecht")=="Utrecht"

def test_temporal_fold_accepts_strictly_earlier_datetime():
    ds=[datetime(2026,10,9),datetime(2026,10,10),datetime(2026,10,11),datetime(2026,10,12)]
    assert_strict_temporal_fold(ds,[0,1],[2,3])

def test_temporal_fold_rejects_same_day_and_future():
    ds=[datetime(2026,10,10)]*3+[datetime(2026,10,11)]
    with pytest.raises(ValueError,match="same-time"):
        assert_strict_temporal_fold(ds,[0,1],[2,3])
    with pytest.raises(ValueError,match="same-time"):
        assert_strict_temporal_fold(ds,[3],[0])

def test_temporal_fold_rejects_missing_group_and_invalid_index():
    with pytest.raises(ValueError):
        assert_strict_temporal_fold([datetime(2026,10,10)],[0],[])
    with pytest.raises(TypeError):
        assert_strict_temporal_fold(["2026-10-09","2026-10-10"],[0],[1])

def test_multifold_adapter_fails_when_middle_fold_leaks():
    ds=[datetime(2026,10,10),datetime(2026,10,11),datetime(2026,10,11),datetime(2026,10,12)]
    with pytest.raises(ValueError):
        validate_all_folds(ds,[([0],[1]),([0,1],[2,3])])
