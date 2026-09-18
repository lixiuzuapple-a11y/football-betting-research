"""Football Betting Recommendation & Research System.

A pre-match research pipeline: data -> features -> prediction -> odds ->
decision -> records -> evaluation -> backtest.

Two properties are load-bearing and are enforced in code, not just documented:

**Recommendation is not execution.** The system produces ``Recommendation`` rows
labelled ``BUY`` or ``PASS``. Nothing consumes those labels as an instruction,
and there is no wagering integration anywhere in this package. Automatic
betting is explicitly out of scope for stage 1.

**No future information.** Every artefact carries the instant it was created and
the information cutoff it used. Post-match objects are rejected as model inputs
at the type level.

Current status: infrastructure only. There is no data source, no feature
contract and no forecasting model. Those absences raise loudly rather than
degrading into plausible-looking output.
"""

from __future__ import annotations

__version__ = "0.0.1"

#: Stage of the project. Deliberately not called "1.0": this is a skeleton.
STAGE = "research-recommendation"

#: The eight functional layers, in dependency order. ``domain`` underpins them
#: all and depends on none of them.
LAYERS: tuple[str, ...] = (
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

__all__ = ["LAYERS", "STAGE", "__version__"]
