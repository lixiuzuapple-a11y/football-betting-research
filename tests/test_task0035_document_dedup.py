"""TASK0035 document-vs-canonical-research first-pass audit ledger invariants."""
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"research"/"task0035_document_dedup_ledger_20261022.json"

def test_exactly_ten_papers_nine_github_ten_data_five_phases():
    doc=json.loads(LEDGER.read_text(encoding="utf-8"))
    rows=doc["rows"]
    assert len(rows)==34
    assert Counter(r["kind"] for r in rows)=={"paper":10,"github":9,"data":10,"spec":5}
    assert len({(r["kind"],r["item"]) for r in rows})==len(rows)
    assert Counter(r["status"] for r in rows)=={"A":9,"B":14,"C":7,"D":4}
    assert len(doc["supplemental_discoveries"])==3
    assert set(doc["tier_policy"])=={"A","B","C","D"}

def test_prior_work_is_not_queued_for_revalidation():
    doc=json.loads(LEDGER.read_text(encoding="utf-8"))
    rows=doc["rows"]
    old=[r for r in rows if r["status"]=="A"]
    assert old
    assert all(r["existing_evidence"] and r["evidence_ref"] for r in old)
    assert any("TASK0034" in r["evidence_ref"] for r in old)

def test_corrigendum_is_preserved_not_original_roi():
    doc=json.loads(LEDGER.read_text(encoding="utf-8"))
    row=next(r for r in doc["rows"] if "Walsh & Joshi" in r["item"])
    assert row["status"]=="C"
    assert "-9.77%" in row["gap"] and "-26.78%" in row["gap"]
    assert "+34.69%" in row["gap"]
    assert "2025.100627" in row["source_url"]
