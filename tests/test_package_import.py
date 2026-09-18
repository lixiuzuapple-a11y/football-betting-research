"""Requirement 1: the project package imports cleanly, layer by layer."""

from __future__ import annotations

import importlib

import pytest

import football_betting


def test_top_level_metadata_is_present() -> None:
    assert football_betting.__version__
    assert football_betting.STAGE == "research-recommendation"


def test_layer_registry_covers_the_documented_layers() -> None:
    assert football_betting.LAYERS == (
        "domain",
        "data",
        "features",
        "models",
        "odds",
        "decision",
        "records",
        "evaluation",
        "backtest",
    )


@pytest.mark.parametrize("layer", football_betting.LAYERS)
def test_every_layer_is_importable(layer: str) -> None:
    module = importlib.import_module(f"football_betting.{layer}")
    assert module.__doc__, f"football_betting.{layer} has no module docstring"


def test_layers_expose_a_public_surface() -> None:
    for layer in football_betting.LAYERS:
        module = importlib.import_module(f"football_betting.{layer}")
        assert getattr(module, "__all__", None), f"{layer} does not declare __all__"


def test_source_tree_is_type_marked() -> None:
    """``py.typed`` must ship, or downstream type checking silently no-ops."""
    from pathlib import Path

    package_dir = Path(football_betting.__file__).parent
    assert (package_dir / "py.typed").is_file()
