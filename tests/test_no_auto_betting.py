"""Scope guard: there is no automatic betting capability in this package.

The charter forbids execution in stage 1. A prohibition that lives only in a
document erodes quietly, so it is asserted here instead: no execution module, no
execution callable, and no reference to a wagering endpoint.

These tests inspect source text and the import graph. They are not a security
boundary - they are a tripwire that makes accidental scope creep show up as a red
build rather than as a paragraph in a release note.
"""

from __future__ import annotations

import ast
from pathlib import Path

import football_betting
from football_betting.domain import Decision, Match, Prediction
from football_betting.records import RecordStore

PACKAGE_DIR = Path(football_betting.__file__).parent

#: Directory or module names that must not exist anywhere in the package.
FORBIDDEN_MODULE_NAMES = frozenset(
    {
        "betting",
        "execution",
        "executor",
        "staking",
        "wallet",
        "bookmaker_api",
        "order",
        "orders",
        "place_bet",
    }
)

#: Callable names that would imply the system acts on a recommendation.
FORBIDDEN_CALLABLE_NAMES = frozenset(
    {
        "place_bet",
        "placebets",
        "submit_bet",
        "submitbets",
        "execute_bet",
        "executebet",
        "execute_recommendation",
        "send_order",
        "auto_bet",
    }
)

#: Substrings that would indicate a live wagering integration.
FORBIDDEN_SOURCE_FRAGMENTS = (
    "api.betfair",
    "betfair.com",
    "pinnacle.com/api",
    "bet365.com",
    "place_order",
    "placeOrder",
    "submitOrder",
)

SOURCE_FILES = tuple(sorted(PACKAGE_DIR.rglob("*.py")))


def test_the_guard_has_something_to_inspect() -> None:
    assert len(SOURCE_FILES) >= 10, "the guard is pointless if it inspects nothing"


def test_no_execution_module_exists() -> None:
    present = {path.parent.name for path in SOURCE_FILES} | {path.stem for path in SOURCE_FILES}
    collision = present & FORBIDDEN_MODULE_NAMES
    assert not collision, f"forbidden module names present: {sorted(collision)}"


def test_no_execution_callable_is_defined_anywhere() -> None:
    offenders: list[str] = []
    for path in SOURCE_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                node.name.lower() in FORBIDDEN_CALLABLE_NAMES
            ):
                offenders.append(f"{path.name}:{node.lineno} {node.name}")
    assert not offenders, f"execution callables found: {offenders}"


def test_no_wagering_endpoint_is_referenced() -> None:
    offenders: list[str] = []
    for path in SOURCE_FILES:
        text = path.read_text(encoding="utf-8")
        offenders.extend(
            f"{path.name}: {fragment}"
            for fragment in FORBIDDEN_SOURCE_FRAGMENTS
            if fragment in text
        )
    assert not offenders, f"wagering integration found: {offenders}"


def test_runtime_dependencies_stay_empty() -> None:
    """Stage 1 is standard-library only, which makes an integration conspicuous."""
    pyproject = PACKAGE_DIR.parents[1] / "pyproject.toml"
    assert pyproject.is_file(), "pyproject.toml should sit at the repository root"
    assert "dependencies = []" in pyproject.read_text(encoding="utf-8"), (
        "adding a runtime dependency is a decision that deserves a review, not a side effect"
    )


def test_a_buy_decision_is_inert(match: Match, prediction: Prediction, recommendation) -> None:
    """Recording a BUY must not conjure a bet. Only a human creates those."""
    store = RecordStore()
    store.record_match(match)
    store.record_prediction(prediction)
    store.record_recommendation(recommendation)

    assert recommendation.decision is Decision.BUY
    assert store.counts()["bets"] == 0
