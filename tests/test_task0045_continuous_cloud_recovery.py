"""TASK0045: immutable epochs, real raw integrity, restart watchdog, config safety."""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import task0045_cloud_cycle as cycle
from tools import task0045_cloud_health as health
from tools.task0017_official_only import SCHEMA

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 10, 30, 8, 0, tzinfo=UTC)
PIN = "a" * 40


def sample_epoch(base, observed=NOW, result="no_offer"):
    root = cycle.next_root(base, now=observed, suffix="evidence01")
    root.mkdir(parents=True)
    body = (b'{"success":true,"value":{"vtoolsConfig":'
            b'{"offLineSaleStatus":1,"onLineSaleStatus":1,'
            b'"onLineStopMessage":"\\u505c\\u6b62\\u9500\\u552e"}}}')
    sha = hashlib.sha256(body).hexdigest()
    rel = f"raw/{observed.date().strftime('%Y%m%d')}/{sha}.json.gz"
    file = root / rel
    file.parent.mkdir(parents=True)
    file.write_bytes(gzip.compress(body, mtime=0))
    db = sqlite3.connect(root / "official.sqlite3")
    db.execute(SCHEMA)
    db.execute(
        """INSERT INTO captures
           (observed_at_utc, request_url, http_status, result, match_count,
            raw_sha256,raw_path,raw_length,source_commit)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (observed.isoformat(), "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry",
         200, result, 0, sha, rel, len(body), PIN))
    db.commit()
    db.close()
    return root, file


def test_no_repeat_epoch_ids_and_reject_naive_clock(tmp_path):
    one = cycle.next_root(tmp_path, now=NOW, suffix="first")
    two = cycle.next_root(tmp_path, now=NOW, suffix="second")
    assert one != two and one.parent == tmp_path / "runs"
    with pytest.raises(ValueError, match="UTC timestamp"):
        cycle.next_root(tmp_path, now=NOW.replace(tzinfo=None))


def test_epoch_creation_and_term_outcome_retains_artifacts(tmp_path, monkeypatch):
    def stub(root, **kwargs):
        db = sqlite3.connect(root / "official.sqlite3")
        db.execute(SCHEMA)
        db.execute("""INSERT INTO captures (observed_at_utc,request_url,result,source_commit)
                       VALUES (?,?,?,?)""", (NOW.isoformat(), "official", "transport_error", PIN))
        db.commit()
        db.close()
        (root / "CONFIG.json").write_text("source")
        return 2
    monkeypatch.setattr(cycle, "collector_run", stub)
    state, root = cycle.one_epoch(tmp_path, source_commit=PIN, max_rounds=1, now=NOW,
                                  min_free_gib=0)
    assert state == 2
    fact = json.loads((root / "CYCLE_OUTCOME.json").read_text())
    assert fact["captures"] == 1
    assert fact["status_counts"] == {"transport_error": 1}
    assert fact["collector_exit"] == 2
    assert (root/"CONFIG.json").read_text() == "source"
    with pytest.raises(FileExistsError):
        (root / "CYCLE_OUTCOME.json").open("x")


def test_epoch_collector_exception_preserves_forensics(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("test simulated outage")
    monkeypatch.setattr(cycle, "collector_run", broken)
    status, root = cycle.one_epoch(tmp_path, source_commit=PIN, max_rounds=1,
                                   now=NOW, min_free_gib=0)
    assert status == 2
    o = json.loads((root / "CYCLE_OUTCOME.json").read_text())
    assert "simulated outage" in o["error"]
    assert o["sqlite"] == "NOT_CREATED"


def test_disk_guard_refuses_before_creating_source_root(tmp_path, monkeypatch):
    disk = shutil.disk_usage(tmp_path)
    monkeypatch.setattr(cycle.shutil, "disk_usage",
                        lambda *_: SimpleNamespace(free=0, total=disk.total))
    with pytest.raises(OSError, match="low disk"):
        cycle.one_epoch(tmp_path, source_commit=PIN, min_free_gib=3)
    assert not (tmp_path / "runs").exists()


def test_health_full_source_sha_with_legitimate_no_offer(tmp_path):
    root, rawfile = sample_epoch(tmp_path)
    state = {"ActiveState": "active", "MainPID": "123", "NRestarts": "0"}
    good = health.check(tmp_path, Path("tools/task0017_official_only.py"),
                        now=NOW+dt.timedelta(minutes=1), state=state, min_free_gib=0)
    assert good["status"] == "OK", good
    assert good["verified_raw_captures"] == 1
    assert good["status_counts"] == {"no_offer": 1}
    rawfile.write_bytes(gzip.compress(b'{"changed":true}', mtime=0))
    bad = health.check(tmp_path, Path("tools/task0017_official_only.py"),
                       now=NOW+dt.timedelta(minutes=1), state=state, min_free_gib=0)
    assert bad["status"] == "ALERT"
    assert "raw_integrity" in bad["reason"]


def test_health_unresponsive_or_down_detected(tmp_path):
    sample_epoch(tmp_path)
    live = {"ActiveState": "active", "MainPID": "123"}
    bad = health.check(tmp_path, Path("tools/task0017_official_only.py"),
                       now=NOW+dt.timedelta(minutes=9), state=live, min_free_gib=0)
    assert bad["status"] == "ALERT" and bad["reason"] == "collector_stale_or_future_clock"
    down = health.check(tmp_path, Path("tools/task0017_official_only.py"),
                        now=NOW+dt.timedelta(minutes=1),
                        state={"ActiveState": "failed", "MainPID": "0"},
                        min_free_gib=0)
    assert down["status"] == "ALERT" and down["reason"] == "collector_not_running"


def test_health_boot_grace(tmp_path):
    (tmp_path/"runs").mkdir()
    r = health.check(tmp_path, Path("tools/task0017_official_only.py"),
                     now=NOW, state={"ActiveState": "active", "MainPID": "444"},
                     min_free_gib=0)
    assert r["status"] == "STARTING"


def test_health_log_append_and_latest_atomic(tmp_path):
    status = {"status": "OK", "captures_in_epoch": 2}
    health.record(tmp_path, status)
    health.record(tmp_path, {"status": "ALERT", "reason": "stale"})
    path = tmp_path / "health"
    rows = (path / "events.jsonl").read_text().splitlines()
    assert len(rows) == 2
    assert json.loads(rows[0]) == status
    assert json.loads((path / "LATEST.json").read_text())["status"] == "ALERT"


def test_watchdog_restricts_systemd_restart_target(monkeypatch):
    calls = []
    monkeypatch.setattr(health.subprocess, "run",
                        lambda args, **kwargs: calls.append(args))
    health.restart_collector()
    assert calls == [["systemctl", "restart", health.UNIT]]
    with pytest.raises(ValueError, match="unapproved"):
        health.restart_collector("a-share-capture.service")


def test_systemd_units_persistent_restart_and_periodic_watchdog():
    collector = Path("deploy/evlab-task0045-official.service").read_text()
    timer = Path("deploy/evlab-task0045-health.timer").read_text()
    monitor = Path("deploy/evlab-task0045-health.service").read_text()
    assert "Restart=always" in collector and "RestartSec=30" in collector
    assert "StartLimitIntervalSec=0" in collector
    assert "WantedBy=multi-user.target" in collector
    assert "User=ubuntu" in collector
    assert "ReadWritePaths=/home/ubuntu/evlab-data/task0045-continuous" in collector
    assert "OnUnitActiveSec=2min" in timer
    assert "WantedBy=timers.target" in timer
    assert "task0045_cloud_health" in monitor
