from __future__ import annotations

from football_betting.analysis.b01 import (
    collapse_episodes,
    proxy_edges,
    qualifies,
    threshold_key,
)


def _row(
    round_seq: int,
    edge: float,
    *,
    variant: str = "v1",
    match: str = "m1",
    side: str = "H",
):
    return {
        "round_seq": round_seq,
        "proxy_implied_edge": edge,
        "source_variant": variant,
        "match_id": match,
        "side": side,
        "observed_at": f"2026-10-01T00:{round_seq:02d}:00+00:00",
    }


def test_proxy_edges_are_multiplicative_devig_times_sporttery_price() -> None:
    edges = proxy_edges((2.0, 4.0, 4.0), (2.2, 3.8, 3.8))
    assert abs(edges["H"] - 0.1) < 1e-12
    assert abs(edges["D"] - (-0.05)) < 1e-12
    assert abs(edges["A"] - (-0.05)) < 1e-12


def test_threshold_semantics_are_frozen() -> None:
    assert threshold_key(0.0) == "gt0"
    assert threshold_key(0.02) == "ge2"
    assert qualifies(1e-9, 0.0)
    assert not qualifies(0.0, 0.0)
    assert qualifies(0.02, 0.02)
    assert not qualifies(0.0199, 0.02)


def test_episode_collapse_requires_consecutive_round_sequence() -> None:
    rows = [_row(1, 0.03), _row(2, 0.04), _row(4, 0.05), _row(5, -0.01)]
    episodes = collapse_episodes(rows, 0.02)
    assert [e["rounds"] for e in episodes] == [2, 1]


def test_episode_collapse_separates_variant_side_and_fixture() -> None:
    rows = [
        _row(1, 0.03),
        _row(2, 0.03, variant="v2"),
        _row(2, 0.03, side="D"),
        _row(2, 0.03, match="m2"),
    ]
    episodes = collapse_episodes(rows, 0.02)
    assert len(episodes) == 4
