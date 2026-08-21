"""Public agent facade."""
from __future__ import annotations

from typing import Any

from search import solve


def build_plan(scenario: dict[str, Any]) -> dict[str, Any]:
    return solve(scenario)
