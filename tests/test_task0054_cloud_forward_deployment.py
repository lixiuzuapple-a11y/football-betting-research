"""TASK0054 fail-closed deployment controls. Runtime proof is separate."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "deploy" / "Run-Task0054-CloudForward.sh").read_text()
SERVICE = (ROOT / "deploy" / "evlab-task0054-cloud-forward.service").read_text()
TIMER = (ROOT / "deploy" / "evlab-task0054-cloud-forward.timer").read_text()


def test_cloud_runner_cannot_target_unapproved_repo():
    assert "git@github.com:lixiuzuapple-a11y/football-betting-research.git" in RUNNER
    assert "remote get-url origin" in RUNNER
    assert "branch --show-current" in RUNNER
    assert "refs/remotes/origin/main" in RUNNER
    assert "merge --ff-only" in RUNNER
    assert "status --porcelain --untracked-files=all" in RUNNER


def test_cloud_runner_does_not_skip_normal_source_and_publish_gates():
    assert "tools.task0046_forward_publication" in RUNNER
    assert "--mode publish" in RUNNER
    assert "--source-commit" in RUNNER
    assert "sha256sum" in RUNNER
    assert "13d373dbab8363e606cfaf39c478b6035c35c86ad0ffcbf4c53e6e5014f63f2f" in RUNNER
    assert "eb3c37793866a27f8c1520c78a69e6098fdf79f08622b37fed64070fa1f8748f" in RUNNER
    assert "NTPSynchronized" in RUNNER
    assert "--mode probe" not in RUNNER


def test_cloud_runner_remembers_start_and_final_exit():
    assert '"phase":"STARTED"' in RUNNER
    assert '"phase":"FINISHED"' in RUNNER
    assert "trap finish EXIT" in RUNNER
    assert "exec \"$PYTHON\"" not in RUNNER
    assert "umask 077" in RUNNER


def test_one_writer_service_is_read_only_except_dedicated_repo_and_evidence():
    assert "User=ubuntu" in SERVICE
    assert "NoNewPrivileges=yes" in SERVICE
    assert "ProtectSystem=strict" in SERVICE
    assert "ReadWritePaths=/home/ubuntu/evlab-forward-publisher-20261108" in SERVICE
    assert "ReadOnlyPaths=/home/ubuntu/evlab-forward-shadow-20261108" in SERVICE
    assert "/usr/bin/flock -n" in SERVICE
    assert "/home/ubuntu/evlab-forward-publisher-20261108/one-writer.lock" in SERVICE
    assert "NoNewPrivileges=no" not in SERVICE
    assert "RootDirectory=" not in SERVICE


def test_daily_timer_has_explicit_local_clock_and_no_quick_loop():
    assert "OnCalendar=*-*-* 11:15:00 Asia/Shanghai" in TIMER
    assert "Persistent=true" in TIMER
    assert "RandomizedDelaySec=0" in TIMER
    assert "OnUnitActiveSec=" not in TIMER
    assert "Unit=evlab-task0054-cloud-forward.service" in TIMER


def test_no_other_repo_or_betting_reference_in_new_entrypoint():
    combined = RUNNER + SERVICE + TIMER
    for banned in (
        "evlab-sfc14-r9", "sfc14", "r9", "curl -X POST",
        "bet365", "place_bet", "下注", "sudo ",
        "git push --force", "git reset --hard", "git clean -fd",
        "ssh-agent", "gho_", "github_pat_"
    ):
        assert banned not in combined
