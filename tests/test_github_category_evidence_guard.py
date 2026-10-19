"""Audit only: category completion and source-provenance assertions (no prediction code)."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"research"/"github_category_decision_20261018.json"

def _data():
    return json.loads(LEDGER.read_text(encoding="utf-8"))

def test_all_18_repos_unique_in_one_category_and_decided():
    data=_data()
    rows=data["rows"]
    assert len(rows)==18
    assert len({r["repo"] for r in rows})==18
    assert data["counts"]=={"A_DATA":4,"B_MODELS":5,"C_RESEARCH_QA":4,"D_SPECIALIZED":5}
    for key,count in data["counts"].items():
        selected=[r for r in rows if r["category"]==key]
        assert len(selected)==count
        assert all(r["verification_state"].startswith("completed") for r in selected)

def test_generated_sports_fixture_cannot_be_promoted_to_real_benchmark():
    rows={r["repo"]:r for r in _data()["rows"]}
    generated=rows["Divyadhole/world-cup-match-predictor"]["category_d"]
    assert generated["data_nature"]=="synthetic"
    assert generated["allow_in_real_benchmark"] is False
    assert all(r["category_d"]["allow_in_real_benchmark"] is False
               for r in rows.values() if r["category"]=="D_SPECIALIZED")
