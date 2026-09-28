"""Guard the TASK-0005 systemd unit template (REVIEWS/TASK-0005.md F6).

The rejected revision declared ``StartLimitIntervalSec`` in ``[Service]``, where
systemd ignores it, so the effective interval silently stayed at the 10s
default. These tests keep the [Unit] placement and the restart policy honest
without needing a live host.

The unit file is parsed by hand rather than with :mod:`configparser`, because a
unit may legitimately repeat a key (``Environment=`` appears several times) and
``configparser`` would either raise or silently drop all but the last one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

UNIT_PATH = Path(__file__).resolve().parents[1] / "deploy" / "evlab-task0005.service"

#: Keys systemd only honours in [Unit]. Declaring one in [Service] is silently
#: ignored - exactly the defect the reviewer observed in the journal.
UNIT_ONLY_KEYS = ("StartLimitIntervalSec", "StartLimitBurst")


def _parse_unit(path: Path) -> dict[str, list[tuple[str, str]]]:
    """Split a systemd unit into ``{section: [(key, value), ...]}``."""
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
    # None of them may appear in [Service] - that is the F6 defect.
    service_keys = {name for name, _ in unit.get("Service", [])}
    for key in UNIT_ONLY_KEYS:
        assert key not in service_keys, f"{key} must not be declared in [Service]"


def test_restart_policy_is_bounded(unit: dict[str, list[tuple[str, str]]]) -> None:
    assert _first(unit, "Service", "Restart") == "on-failure"
    assert _first(unit, "Service", "RestartSec") == "15"
    assert _first(unit, "Service", "Type") == "simple"


def test_deployment_metadata_comes_from_the_environment(
    unit: dict[str, list[tuple[str, str]]],
) -> None:
    """Runs as the unprivileged service user; commit is injected, not read."""
    assert _first(unit, "Service", "User") == "ubuntu"
    environment = _values(unit, "Service", "Environment")
    assert any("EVLAB_DEPLOYED_COMMIT" in entry for entry in environment), environment


def test_exec_start_runs_the_package_module(unit: dict[str, list[tuple[str, str]]]) -> None:
    exec_start = _first(unit, "Service", "ExecStart")
    assert "-m football_betting.prospective" in exec_start
    assert "--data-root /home/ubuntu/evlab-data/task0005" in exec_start
    # The runtime data root must live outside the Git working tree.
    after_data_root = exec_start.split("--data-root", 1)[1]
    assert "/home/ubuntu/football-betting-research" not in after_data_root


def test_install_section_enables_the_unit(unit: dict[str, list[tuple[str, str]]]) -> None:
    assert _first(unit, "Install", "WantedBy") == "multi-user.target"
