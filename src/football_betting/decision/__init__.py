"""Decision layer: forecast versus price, expressed as a recorded opinion.

Responsibility boundary
-----------------------
Inputs: a prediction and a market quote. Output: a ``Recommendation`` row.

``BUY`` is not a command. No module in this package reads a recommendation and
acts on it, and there is no execution path to act with. See
``docs/project-charter.md`` section 6.3 and section 6.
"""

from __future__ import annotations

from .engine import DecisionPolicy, decide, make_recommendation_id

__all__ = [
    "DecisionPolicy",
    "decide",
    "make_recommendation_id",
]
