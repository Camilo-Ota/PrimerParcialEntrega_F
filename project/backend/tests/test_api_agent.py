"""End-to-end search-plan validation against the simulator contract."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from agent import build_plan  # noqa: E402
from simulator import goal_satisfied, load_scenario, simulate  # noqa: E402


def test_generated_plan_is_legal_and_reaches_goal() -> None:
    scenario = load_scenario()
    plan = build_plan(scenario)
    assert plan["solution_found"] is True, plan
    assert set(plan.keys()) == {"solution_found", "total_cost", "steps", "message"}
    assert plan["total_cost"] == sum(int(step["cost"]) for step in plan["steps"])
    assert all(step["op"] in {"MOVE", "PICKUP", "DROP", "INTERACT"} for step in plan["steps"])
    final = simulate(scenario, plan["steps"])
    assert goal_satisfied(scenario, final)
    assert final["energy_spent"] == plan["total_cost"]
