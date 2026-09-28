"""Guard the TASK-0006 systemd unit template (TASK-0006 §8, TASK-0005 F6).

The TASK-0005 rejection was caused by declaring ``StartLimitIntervalSec`` in
``[Service]``, where systemd silently ignores it. The same trap is right next
door for the sealed-run unit, so the section placement and the frozen-run
command line are asserted here rather than trusted.

The unit is parsed by hand for the same reason as the TASK-0005 guard: a unit
may legitimately repeat ``Environment=``, which :mod:`configparser` cannot
represent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

UNIT_PATH = Path(__file__).resolve().parents[1] / "deploy" / "evlab-task0006.service"

#: Keys systemd only honours in [Unit]. Declaring one in [Service] is silently
#: ignored - the exact defect the reviewer observed in the TASK-0005 journal.
UNIT_ONLY_KEYS = ("StartLimitIntervalSec", "StartLimitBurst")


def _parse_unit(path: Path) -> dict[str, list[tuple[str, str]]]:
    sections: dict[str, list[tuple[str, str]]] = {}
    current: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, [])
            continue
        if current is None or "=" not in line:
            continue
        key, _, value = line.partition("=")
        sections[current].append((key.strip(), value.strip()))
    return sections


@pytest.fixture(scope="module")
def unit() -> dict[str, list[tuple[str, str]]]:
    return _parse_unit(UNIT_PATH)


def _values(unit: dict[str, list[tuple[str, str]]], section: str, key: str) -> list[str]:
    return [value for name, value in unit.get(section, []) if name == key]


def _first(unit: dict[str, list[tuple[str, str]]], section: str, key: str) -> str:
    values = _values(unit, section, key)
    assert values, f"{key} missing from [{section}]"
    return values[0]


def test_unit_template_exists() -> None:
    assert UNIT_PATH.is_file()


def test_start_limit_keys_are_in_unit_section(unit: dict[str, list[tuple[str, str]]]) -> None:
    assert _first(unit, "Unit", "StartLimitIntervalSec") == "300"
    assert _first(unit, "Unit", "StartLimitBurst") == "5"
    service_keys = {name for name, _ in unit.get("Service", [])}
    for key in UNIT_ONLY_KEYS:
        assert key not in service_keys, f"{key} must not be declared in [Service]"


def test_restart_policy_is_bounded(unit: dict[str, list[tuple[str, str]]]) -> None:
    assert _first(unit, "Service", "Restart") == "on-failure"
    assert _first(unit, "Service", "RestartSec") == "15"
    assert _first(unit, "Service", "Type") == "simple"


def test_runs_as_the_unprivileged_user_with_injected_commit(
    unit: dict[str, list[tuple[str, str]]],
) -> None:
    assert _first(unit, "Service", "User") == "ubuntu"
    assert _first(unit, "Service", "Group") == "ubuntu"
    environment = _values(unit, "Service", "Environment")
    assert any("EVLAB_DEPLOYED_COMMIT" in entry for entry in environment), environment


def test_exec_start_declares_the_sealed_phase_and_fresh_root(
    unit: dict[str, list[tuple[str, str]]],
) -> None:
    exec_start = _first(unit, "Service", "ExecStart")
    assert "-m football_betting.prospective" in exec_start
    assert "--dataset-phase PROSPECTIVE_SEALED" in exec_start
    assert "--data-root /home/ubuntu/evlab-data/task0006-sealed-%RUN_ID%" in exec_start
    # The runtime data root must live outside the Git working tree.
    after_data_root = exec_start.split("--data-root", 1)[1]
    assert "/home/ubuntu/football-betting-research" not in after_data_root
    # The frozen 60-second cadence is part of the sealed contract.
    assert "--round-interval 60" in exec_start


def test_no_forbidden_runtime_capability(unit: dict[str, list[tuple[str, str]]]) -> None:
    """No inbound port, container runtime, browser automation or proxy (§8)."""
    managed = [
        f"{key}={value}"
        for section, entries in unit.items()
        for key, value in entries
        if section in {"Unit", "Service", "Install"}
    ]
    blob = "\n".join(managed).lower()
    for forbidden in ("docker", "scrapling", "playwright", "selenium", "proxy=", "vpn"):
        assert forbidden not in blob, f"[{forbidden}] is not allowed on the sealed unit"


def test_install_section_enables_the_unit(unit: dict[str, list[tuple[str, str]]]) -> None:
    assert _first(unit, "Install", "WantedBy") == "multi-user.target"
