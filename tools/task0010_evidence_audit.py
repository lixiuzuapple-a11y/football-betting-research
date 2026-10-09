"""Read-only EV-Lab repo evidence-chain audit. Standard library only.

Run: python tools/task0010_evidence_audit.py
May be rerun after new TASKs. Never modifies repository/data.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> bool:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return completed.returncode == 0


def inspect() -> dict:
    tasks = []
    missing = []
    documented_exceptions = []
    for i in range(1, 11):
        task_id = f"TASK-{i:04d}"
        matches = list((ROOT / "TASKS").glob(f"{task_id}-*.md"))
        report = ROOT / "REPORTS" / f"{task_id}.md"
        review = ROOT / "REVIEWS" / f"{task_id}.md"
        if len(matches) != 1:
            missing.append(f"{task_id}: expected one task, got {len(matches)}")
        for file in (report, review):
            if not file.is_file():
                if i == 3 and file == report and review.is_file() and "SUPERSEDED_BY_OWNER_HISTORY_BUNDLE" in review.read_text(encoding="utf-8"):
                    documented_exceptions.append(f"{task_id}: original executor report absent; explicit alternate Owner bundle closure")
                else:
                    missing.append(f"{task_id}: missing {file.relative_to(ROOT)}")
        status = "UNKNOWN"
        if len(matches) == 1:
            match = re.search(r"(?im)^-\s*Status:\s*(.+)$", matches[0].read_text(encoding="utf-8"))
            if match:
                status = match.group(1).strip()
        tasks.append({"id": task_id, "status_in_task": status,
                      "task": str(matches[0].relative_to(ROOT)) if len(matches) == 1 else None,
                      "report": report.is_file(), "review": review.is_file()})
    required = [
        "assets/team_name_map.json",
        "src/football_betting/analysis/d01b.py",
        "src/football_betting/analysis/b01.py",
        "tools/task0007_independent_audit.py",
        "tools/task0008_independent_audit.py",
        "results/task0007/summary.json",
        "results/task0008/summary.json",
        "history/MANIFEST.md",
    ]
    absent_assets = [f for f in required if not (ROOT / f).is_file()]
    task6 = (ROOT / "REVIEWS" / "TASK-0006.md").read_text(encoding="utf-8")
    task7 = (ROOT / "REVIEWS" / "TASK-0007.md").read_text(encoding="utf-8")
    task8 = (ROOT / "REVIEWS" / "TASK-0008.md").read_text(encoding="utf-8")
    decisions = {
        "task0006_strict_rejected": "REJECTED AS A STRICT SEALED RUN" in task6,
        "task0007_procedure_accepted": "Final task gate: **ACCEPTED**" in task7,
        "task0007_hypothesis_not_validated": "NOT VALIDATED" in task7,
        "task0008_procedure_accepted": "Decision: **ACCEPTED**" in task8,
        "task0008_hypothesis_not_validated": "NOT VALIDATED" in task8,
    }
    findings = {
        "task_count": len(tasks),
        "tasks": tasks,
        "missing_task_report_review": missing,
        "documented_exceptions": documented_exceptions,
        "missing_reusable_assets": absent_assets,
        "decision_phrase_checks": decisions,
        "tracked_task0007_results": git("ls-files", "--error-unmatch", "results/task0007/summary.json"),
        "tracked_task0008_results": git("ls-files", "--error-unmatch", "results/task0008/summary.json"),
        "stale_results_readme": "Currently empty" in (ROOT / "results" / "README.md").read_text(encoding="utf-8"),
    }
    findings["pass"] = (not missing and not absent_assets and
                        all(decisions.values()) and
                        findings["tracked_task0007_results"] and
                        findings["tracked_task0008_results"] and
                        not findings["stale_results_readme"])
    return findings


if __name__ == "__main__":
    result = inspect()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["pass"] else 1)
