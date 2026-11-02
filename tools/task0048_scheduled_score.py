"""TASK0048: scheduled automatic *post-match* official blind scoring.

Only accepts actual remotely acknowledged, local-Git-anchored TASK0046
forecasts. No forecast is recalculated, no result is used before kickoff,
and incomplete/delayed official data never silently become a scored sample.
Every attempt has a unique immutable raw result root and a create-only journal.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path

from tools.phase2_forecast_lab import _create_only
from tools.task0044_forward_orchestrator import (
    MIN_SCORE_DELAY_HOURS, aware, fetch_and_score, verified_freeze,
)
from tools.task0047_independent_blind_score_qa import independent_audit

UTC = dt.timezone.utc
MAX_CANDIDATES = 10
SHA40 = re.compile(r"[a-f0-9]{40}\Z")
LEDGER_NAME = re.compile(r"task0046_forward_\d{8}T\d{6}Z_[a-f0-9]{12}\.json\Z")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prior_success(score_base: Path, ledger: str) -> bool:
    for path in sorted((score_base / "journal").glob("*.json")):
        event = json.loads(path.read_bytes())
        if event.get("ledger_file") != ledger or event.get("status") != "INDEPENDENT_SCORE_ACCEPTED":
            continue
        audit = Path(event["audit_file"])
        score = Path(event["score_file"])
        if (not audit.is_file() or not score.is_file()
                or digest(audit) != event.get("audit_sha256")
                or digest(score) != event.get("score_sha256")):
            raise ValueError("previous accepted score evidence altered")
        return True
    return False


def anchored_candidate(repo: Path, forward_base: Path, event: dict,
                       now: dt.datetime) -> dict:
    """Do not trust the forward journal alone as evidence of publication."""
    proof = event["commit_result"]
    commit = proof["git_head"]
    if (not SHA40.fullmatch(commit) or proof["remote_head"] != commit
            or proof.get("status") != "PUSHED_GIT_PRE_KICKOFF_LOCAL_CLOCK"):
        raise ValueError("missing verified Git remote commitment")
    ledger_path = Path(proof["ledger"]).resolve()
    if ledger_path.parent != (repo / "research").resolve() or not LEDGER_NAME.fullmatch(ledger_path.name):
        raise ValueError("ledger outside approved research path")
    freeze_path = Path(event["capture_result"]["path"]).resolve()
    run_root = Path(event["run_root"]).resolve()
    if freeze_path != run_root / "NEW_FORECAST_FREEZE.json" or not run_root.is_relative_to(
        (forward_base / "runs").resolve()
    ):
        raise ValueError("untrusted or relocated frozen forecast source")
    if not ledger_path.is_file() or not freeze_path.is_file():
        raise ValueError("committed forecast source missing; preserve failure")
    rel = "research/" + ledger_path.name
    git_blob = subprocess.run(["git","show",f"{commit}:{rel}"],cwd=repo,
                              check=True,capture_output=True,timeout=15).stdout
    actual_blob = ledger_path.read_bytes()
    if git_blob != actual_blob and git_blob != actual_blob.replace(b"\r\n",b"\n"):
        raise ValueError("Git-anchored prediction ledger differs from working file")
    subprocess.run(["git","merge-base","--is-ancestor",commit,"refs/remotes/origin/main"],
                   cwd=repo,check=True,capture_output=True,timeout=15)
    committer_time = subprocess.run(["git","show","-s","--format=%cI",commit],
                                   cwd=repo,check=True,capture_output=True,
                                   text=True,timeout=15).stdout.strip()
    frozen, ledger = verified_freeze(freeze_path, ledger_path)
    freeze_sha = digest(freeze_path)
    if (proof["frozen_file_sha256"] != freeze_sha or
            ledger["frozen_file_sha256"] != freeze_sha):
        raise ValueError("frozen source SHA changed after Git commitment")
    first = min(aware(r["kickoff_utc"]) for r in frozen["predictions"])
    latest = max(aware(r["kickoff_utc"]) for r in frozen["predictions"])
    published = aware(committer_time)
    if published >= first or aware(frozen["frozen_at_utc"]) >= first:
        raise ValueError("retroactive Git commit/prediction, not prospective")
    return {
        "ledger_file": ledger_path.name,
        "ledger_path": ledger_path,
        "ledger_rel": rel,
        "freeze": freeze_path,
        "anchor": commit,
        "earliest_kickoff_utc": first.isoformat(),
        "latest_kickoff_utc": latest.isoformat(),
        "due": now >= latest + dt.timedelta(hours=MIN_SCORE_DELAY_HOURS),
        "match_count": len(frozen["predictions"]),
    }


def run(*, repo: Path, forward_base: Path, score_base: Path,
        now: dt.datetime | None = None,
        score_fn=fetch_and_score, audit_fn=independent_audit) -> dict:
    now = (now or dt.datetime.now(UTC))
    if now.utcoffset() is None:
        raise ValueError("timezone-aware scoring time required")
    now = now.astimezone(UTC)
    repo, forward_base, score_base = repo.resolve(), forward_base.resolve(), score_base.resolve()
    journal_root = score_base / "journal"
    journal_root.mkdir(parents=True,exist_ok=True)
    events = []
    for path in sorted((forward_base / "journal").glob("run-*.json")):
        record = json.loads(path.read_bytes())
        if record.get("status") != "PUSHED_GIT_PRE_KICKOFF_LOCAL_CLOCK":
            continue
        events.append(record)
    if len(events) > MAX_CANDIDATES:
        raise ValueError("too many frozen cohorts for bounded scorer; manual QA required")
    output = {"task":"TASK0048", "checked_at_utc":now.isoformat(),
              "eligible_committed_cohorts":len(events), "results":[]}
    for old in events:
        run_id = now.strftime("score-%Y%m%dT%H%M%S%fZ-")+uuid.uuid4().hex[:8]
        evidence = score_base / "attempts" / run_id
        entry = {"attempt_id":run_id, "started_at_utc":now.isoformat(),
                 "status":"FAILED_RETAIN_ALL_EVIDENCE", "source_forward_run":old.get("run_root")}
        try:
            plan = anchored_candidate(repo, forward_base, old, now)
            entry.update({k:v for k,v in plan.items() if k in (
                "ledger_file","anchor","earliest_kickoff_utc",
                "latest_kickoff_utc","match_count")})
            if prior_success(score_base,plan["ledger_file"]):
                entry["status"]="ALREADY_INDEPENDENTLY_ACCEPTED"
            elif not plan["due"]:
                entry["status"]="WAIT_KICKOFF_PLUS_THREE_HOURS"
            else:
                # Existing official-only original scorer owns exact source
                # capture/time/identity SHA and creates an immutable raw root.
                result = score_fn(frozen_path=plan["freeze"],
                                  ledger_path=plan["ledger_path"],
                                  out_root=evidence)
                entry["raw_result_root"]=str(evidence)
                entry["official_score_result"]=result
                # Review *independently* from the original raw result bytes,
                # Git-anchored vectors, original source and scoring metrics.
                audit = audit_fn(repo=repo,freeze=plan["freeze"],
                                 ledger=plan["ledger_path"],result_root=evidence,
                                 anchor=plan["anchor"],ledger_git_path=plan["ledger_rel"])
                audit_path = evidence / "INDEPENDENT_AUDIT.json"
                audit_sha = _create_only(audit_path,audit)
                entry["audit_file"]=str(audit_path)
                entry["audit_sha256"]=audit_sha
                entry["score_file"]=str(evidence / "BLIND_SCORE.json")
                entry["score_sha256"]=digest(evidence / "BLIND_SCORE.json")
                entry["status"]="INDEPENDENT_SCORE_ACCEPTED"
        except Exception as exc:
            entry["error_type"]=type(exc).__name__
            entry["error"]=str(exc)[:500]
            entry["status"]="FAILED_RETAIN_ALL_EVIDENCE"
        _create_only(journal_root/(run_id+".json"),entry)
        output["results"].append({k:entry[k] for k in ("attempt_id","status","ledger_file",
                                                       "error") if k in entry})
    output["status"] = "NO_COMMITTED_NEW_PROSPECTS" if not events else (
        "ATTEMPTS_REQUIRE_REVIEW" if any(r["status"]=="FAILED_RETAIN_ALL_EVIDENCE"
            for r in output["results"]) else "SCORING_CHECK_COMPLETE")
    return output


def main() -> None:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--repo",required=True,type=Path)
    a.add_argument("--forward-base",required=True,type=Path)
    a.add_argument("--score-base",required=True,type=Path)
    args=a.parse_args()
    result=run(repo=args.repo,forward_base=args.forward_base,score_base=args.score_base)
    print(json.dumps(result,ensure_ascii=False))
    if result["status"]=="ATTEMPTS_REQUIRE_REVIEW":
        raise SystemExit(2)


if __name__=="__main__":
    main()
