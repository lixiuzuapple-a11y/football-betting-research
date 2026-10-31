"""TASK0046: guarded scheduled prospective publication, reusing TASK0044.

Only official pre-match source, already approved identity and frozen historical
models. If no qualified new fixtures, retain evidence and make no Git commit.
New frozen predictions become research-eligible only when the *exact* file hash
and vectors are in a verified, remotely pushed Git ledger before every kickoff.
This is a research pipeline, never a price/EV/betting/score pipeline.
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
    aware, capture_and_freeze, verified_freeze, MODEL_KEYS,
)

UTC = dt.timezone.utc
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
LEDGER_GLOB = ("task0043_pre_kickoff_multimodel_freeze_*.json",
               "task0046_forward_*.json")
MIN_LEAD = dt.timedelta(minutes=60)


def hex64(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def read_previous(repo: Path) -> list[Path]:
    root = repo / "research"
    return sorted(p for glob in LEDGER_GLOB for p in root.glob(glob))


def build_ledger(frozen_path: Path, *, now: dt.datetime,
                 previous: list[Path]) -> dict:
    """Validate immutable local forecast before any proposed Git publication."""
    if now.utcoffset() is None:
        raise ValueError("publication time must be aware")
    now = now.astimezone(UTC)
    frozen = json.loads(frozen_path.read_bytes())
    if (frozen.get("task") != "TASK0043"
            or frozen.get("market_prices_input_to_models") is not False
            or frozen.get("new_results_input_to_models") is not False
            or frozen.get("no_bet_or_buy") is not True):
        raise ValueError("forbidden forecast input or invalid freeze")
    freeze_time = aware(frozen["frozen_at_utc"])
    if freeze_time > now or now - freeze_time > dt.timedelta(minutes=30):
        raise ValueError("freeze timestamp is future or stale")
    capture = frozen["capture"]
    observed = aware(capture["received_utc"])
    if observed > freeze_time or freeze_time - observed > dt.timedelta(hours=6):
        raise ValueError("invalid capture time order/age")
    if not hex64(capture.get("sha256")):
        raise ValueError("invalid original source SHA256")
    hist = frozen["history"]
    train_day = dt.date.fromisoformat(hist["last_training_date"])
    if train_day >= freeze_time.date():
        raise ValueError("historical training date cannot be on/after freeze day")
    published = aware(hist["published_at_utc"])
    if published > freeze_time:
        raise ValueError("historical training source not published before freeze")
    for item in (hist["source_fixture_sha256"], hist["source_manifest_sha256"],
                 frozen["identity_ledger_sha256"]):
        if not hex64(item):
            raise ValueError("invalid historical/identity SHA256")
    predictions = frozen["predictions"]
    if (not isinstance(predictions, list) or not predictions
            or frozen.get("model_qualified") != len(predictions)):
        raise ValueError("empty or inconsistent model cohort")
    older = set()
    for path in previous:
        ledger = json.loads(path.read_bytes())
        if ledger.get("status") != "PRE_KICKOFF_FROZEN_RESEARCH_ONLY":
            raise ValueError("prior Git ledger not a frozen commitment")
        ids = [str(r["matchId"]) for r in ledger["predictions"]]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate prior committed fixtures")
        older.update(ids)
    seen = set()
    kickoff_times = []
    for pred in predictions:
        mid = str(pred["matchId"])
        kickoff = aware(pred["kickoff_utc"])
        if mid in seen or mid in older:
            raise ValueError("duplicate or previously committed fixture")
        seen.add(mid)
        if freeze_time >= kickoff or now + MIN_LEAD >= kickoff:
            raise ValueError("too late for independently published pre-kickoff anchor")
        if pred["official_home_id"] == pred["official_away_id"]:
            raise ValueError("invalid official opponent identity")
        models = pred["models_1x2_home_draw_away"]
        if set(models) != set(MODEL_KEYS):
            raise ValueError("forecast model keys changed")
        kickoff_times.append(kickoff)
    earliest = min(kickoff_times)
    return {
        "task": "TASK0043", "status": "PRE_KICKOFF_FROZEN_RESEARCH_ONLY",
        "record_schema": "EVLAB_TASK0046_FORWARD_V1",
        "frozen_file_sha256": hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
        "official_raw_sha256": capture["sha256"],
        "frozen_at_utc": frozen["frozen_at_utc"],
        "official_received_utc": capture["received_utc"],
        "published_source_commit": capture["capture_source_commit"],
        "identity_ledger_sha256": frozen["identity_ledger_sha256"],
        "historical_fixture_sha256": hist["source_fixture_sha256"],
        "historical_manifest_sha256": hist["source_manifest_sha256"],
        "training_last_date": train_day.isoformat(),
        "training_published_at_utc": hist["published_at_utc"],
        "model_keys": list(MODEL_KEYS),
        "qualified": len(predictions),
        "predictions": predictions,
        "minimum_kickoff_utc": earliest.isoformat(),
        "commit_preflight_utc": now.isoformat(),
        "market_quote_status": "UNVERIFIED_NOT_INCLUDED",
        "market_quote_time_utc": None,
        "market_odds": None,
        "official_result_status": "PENDING",
        "no_market_ev_or_profit_claim": True,
        "no_bet_or_buy": True,
    }


def git(repo: Path, *args: str, timeout: int = 35) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                            text=True, timeout=timeout, check=True)
    return result.stdout.strip()


def git_preflight(repo: Path) -> None:
    origin = git(repo, "remote", "get-url", "origin")
    if not re.search(r"github\.com[:/]lixiuzuapple-a11y/football-betting-research(?:\.git)?\Z", origin):
        raise ValueError("refuse to publish to unexpected Git remote")
    if git(repo, "branch", "--show-current") != "main":
        raise ValueError("refuse to auto-commit outside main")
    if git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("refuse to auto-commit in dirty workspace")
    git(repo, "fetch", "origin", "main")
    if git(repo, "rev-parse", "HEAD") != git(repo, "rev-parse", "refs/remotes/origin/main"):
        raise ValueError("local main diverged from origin; manual QA required")


def publish(repo: Path, ledger: dict, frozen_path: Path, *, now: dt.datetime,
            git_fn=git) -> dict:
    # Require the current physical time to remain safely before kickoff.
    if now.utcoffset() is None or now.astimezone(UTC) + MIN_LEAD >= aware(ledger["minimum_kickoff_utc"]):
        raise ValueError("publication deadline elapsed")
    root = repo / "research"
    filename = (f"task0046_forward_{now.astimezone(UTC):%Y%m%dT%H%M%SZ}_"
                f"{ledger['frozen_file_sha256'][:12]}.json")
    path = root / filename
    if path.exists():
        raise FileExistsError("Git commitment path exists")
    # No Git source mutation until all shape checks have passed.
    _create_only(path, ledger)
    verified_freeze(frozen_path, path)
    try:
        if dt.datetime.now(UTC) + MIN_LEAD >= aware(ledger["minimum_kickoff_utc"]):
            raise ValueError("publication deadline elapsed before git commit")
        git_fn(repo, "add", "--", "research/" + filename)
        git_fn(repo, "commit", "-m", f"research(evlab): freeze {ledger['qualified']} prospective fixtures before kickoff")
        head = git_fn(repo, "rev-parse", "HEAD")
        git_fn(repo, "push", "origin", "main", timeout=70)
        remote = git_fn(repo, "ls-remote", "origin", "refs/heads/main", timeout=25)
        if remote.split()[0] != head:
            raise ValueError("remote Git commitment not verified")
        if dt.datetime.now(UTC) >= aware(ledger["minimum_kickoff_utc"]):
            raise ValueError("remote verified only at/after kickoff: not admissible")
    except Exception:
        # Never rewrite or delete a failed commitment or freeze. The incident
        # remains visible in working tree and run event journal for review.
        raise
    return {"status": "PUSHED_GIT_PRE_KICKOFF_LOCAL_CLOCK",
            "ledger": str(path), "ledger_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "frozen_file_sha256": ledger["frozen_file_sha256"],
            "git_head": head, "remote_head": remote.split()[0],
            "earliest_kickoff_utc": ledger["minimum_kickoff_utc"],
            "remote_verification_utc_local_clock": dt.datetime.now(UTC).isoformat(),
            "time_authority_limit": "Local clock and Git commit dates are not independent authenticated timestamps.",
            "qualified": ledger["qualified"]}


def one_run(*, repo: Path, evidence_base: Path, identity: Path, history: Path,
            commit: str, mode: str = "publish",
            now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(UTC)
    if now.utcoffset() is None:
        raise ValueError("timezone-aware run clock required")
    repo = repo.resolve()
    evidence_base = evidence_base.resolve()
    if mode not in ("publish", "probe"):
        raise ValueError("unsupported forward mode")
    event = {"task": "TASK0046", "mode": mode, "started_at_utc": now.isoformat()}
    run_root = evidence_base / "runs" / (
        now.astimezone(UTC).strftime("run-%Y%m%dT%H%M%S%fZ-") + uuid.uuid4().hex[:8])
    if run_root.exists():
        raise FileExistsError("run already exists")
    event["run_root"] = str(run_root)
    try:
        # No Git source mutation without a clean and expected exact remote.
        # Failed preflight is still logged as a create-only incident.
        if mode == "publish":
            git_preflight(repo)
        prior = read_previous(repo)
        result = capture_and_freeze(output_root=run_root, identity=identity,
                                    history=history, commit=commit,
                                    previous_ledgers=prior, now=now)
        event["capture_result"] = result
        if result["status"] == "FROZEN_LOCALLY_NOT_GIT_ANCHORED":
            frozen_path = Path(result["path"])
            current_time = dt.datetime.now(UTC)
            ledger = build_ledger(frozen_path, now=current_time, previous=prior)
            if mode == "publish":
                event["commit_result"] = publish(repo, ledger, frozen_path, now=current_time)
                event["status"] = "PUSHED_GIT_PRE_KICKOFF_LOCAL_CLOCK"
            else:
                event["status"] = "PROBE_LOCAL_UNANCHORED_NOT_ADMISSIBLE"
        else:
            event["status"] = result["status"]
    except Exception as exc:
        event["status"] = "FAILED_RETAIN_ALL_EVIDENCE"
        event["error_type"] = type(exc).__name__
        event["error"] = str(exc)[:500]
    finally:
        (evidence_base / "journal").mkdir(parents=True, exist_ok=True)
        _create_only(evidence_base / "journal" / (run_root.name + ".json"), event)
    return event


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--evidence-base", required=True, type=Path)
    ap.add_argument("--identity", required=True, type=Path)
    ap.add_argument("--history", required=True, type=Path)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--mode", choices=("probe", "publish"), default="publish")
    a = ap.parse_args()
    output = one_run(repo=a.repo, evidence_base=a.evidence_base,
                     identity=a.identity, history=a.history,
                     commit=a.source_commit, mode=a.mode)
    print(json.dumps(output, ensure_ascii=False))
    if output["status"] == "FAILED_RETAIN_ALL_EVIDENCE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
