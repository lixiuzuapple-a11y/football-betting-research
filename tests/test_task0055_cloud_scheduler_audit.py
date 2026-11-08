"""TASK0055 proof requirements: only an actual 11:15/18:30 timed run qualifies."""
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from tools import task0055_cloud_scheduler_audit as a

DAY = dt.date(2026, 11, 8)
NOW = dt.datetime(2026, 11, 8, 19, 10, tzinfo=a.SHANGHAI)
STARTED = {"task": "TASK0054-SCORE", "phase": "STARTED",
           "at_utc": "2026-11-08T10:30:00Z"}
FINISHED = {"task": "TASK0054-SCORE", "phase": "FINISHED",
            "at_utc": "2026-11-08T10:30:05Z", "exit_code": 0}


def check(entries=None, *, trigger="Sun 2026-11-08 18:30:00 CST",
          now=NOW, enabled=True, active=True, result="success", exit_code=0):
    return a.audit(
        a.CONFIG["score"], [STARTED, FINISHED] if entries is None else entries,
        day=DAY, now=now, trigger=trigger,
        timer_active=active, timer_enabled=enabled,
        service_result=result, service_exit=exit_code, log_sha256="a" * 64,
    )


def test_real_daily_score_1830_accept():
    result = check()
    assert result["status"] == "PASS"
    assert result["issues"] == []
    assert result["actual_runs"]["successful_pairs"]
    assert result["observed_timer"] == "2026-11-08T18:30:00+08:00"


def test_manual_canary_at_1550_not_accepted_as_production():
    entries = [
        {"task": "TASK0054-SCORE", "phase": "STARTED", "at_utc": "2026-11-08T07:50:21Z"},
        {"task": "TASK0054-SCORE", "phase": "FINISHED",
         "at_utc": "2026-11-08T07:50:25Z", "exit_code": 0},
    ]
    result = check(entries)
    assert result["status"] == "FAIL"
    assert "NO_SUCCESSFUL_SCHEDULED_START_FINISH_PAIR" in result["issues"]


@pytest.mark.parametrize("trigger", ["", "Mon 2026-11-09 18:30:00 CST",
                                     "Sun 2026-11-08 19:00:00 CST"])
def test_missing_wrong_or_other_day_timer_trigger_rejected(trigger):
    assert "MISSING_EXACT_SCHEDULED_TIMER_TRIGGER" in check(trigger=trigger)["issues"]


def test_missing_finish_rejected_even_if_start_is_present():
    result = check([STARTED])
    assert result["status"] == "FAIL"
    assert "UNFINISHED_START" in result["actual_runs"]["anomalies"]


def test_nonzero_exit_never_passes():
    result = check([STARTED, dict(FINISHED, exit_code=4)])
    assert result["status"] == "FAIL"
    assert "NONZERO_EXIT:4" in result["actual_runs"]["anomalies"]


def test_restart_after_incomplete_run_is_identified_and_accepts_valid_recovery():
    second_start = dict(STARTED, at_utc="2026-11-08T10:35:01Z")
    second_end = dict(FINISHED, at_utc="2026-11-08T10:35:06Z")
    result = check([STARTED, second_start, second_end])
    assert result["status"] == "PASS_WITH_RECOVERY"
    assert "UNFINISHED_START" in result["actual_runs"]["anomalies"]


def test_disabled_timer_and_failed_service_cannot_be_misreported():
    assert check(enabled=False)["status"] == "FAIL"
    assert check(active=False)["status"] == "FAIL"
    assert check(result="exit-code", exit_code=1)["status"] == "FAIL"


def test_not_due_is_not_falsely_reported_as_success():
    early = dt.datetime(2026, 11, 8, 18, 33, tzinfo=a.SHANGHAI)
    assert check(now=early)["status"] == "NOT_DUE"


def test_forward_role_uses_its_own_schedule_and_task_name():
    config = a.CONFIG["forward"]
    start = {"task": "TASK0054", "phase": "STARTED", "at_utc": "2026-11-09T03:15:01Z"}
    end = {"task": "TASK0054", "phase": "FINISHED",
           "at_utc": "2026-11-09T03:15:08Z", "exit_code": 0}
    result = a.audit(config, [start, end], day=dt.date(2026, 11, 9),
                     now=dt.datetime(2026, 11, 9, 11, 45, tzinfo=a.SHANGHAI),
                     trigger="Mon 2026-11-09 11:15:00 CST",
                     timer_active=True, timer_enabled=True,
                     service_result="success", service_exit=0, log_sha256="b" * 64)
    assert result["status"] == "PASS"
    assert result["role"] == "TASK0054"


def test_create_only_audit_input_requires_full_json_lines(tmp_path):
    file = tmp_path / "INVOCATIONS.jsonl"
    file.write_text(json.dumps(STARTED), encoding="utf-8")
    with pytest.raises(ValueError, match="torn"):
        a.load_jsonl(file)
    data = (json.dumps(STARTED) + "\n" + json.dumps(FINISHED) + "\n").encode()
    file.write_bytes(data)
    records, digest = a.load_jsonl(file)
    assert len(records) == 2
    assert digest == hashlib.sha256(data).hexdigest()


def test_no_extra_betting_or_second_publisher(tmp_path):
    script = Path(a.__file__).read_text(encoding="utf-8")
    assert "tools.task0046_forward_publication --mode publish" not in script
    assert "place_bet" not in script
    assert "checkout" not in script
    assert a.CONFIG["forward"]["file"] != a.CONFIG["score"]["file"]
