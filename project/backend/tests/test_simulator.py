"""Regression tests for the physical simulator contract."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from simulator import apply_step, goal_satisfied, initial_state, load_scenario  # noqa: E402


def test_initial_state_matches_scenario() -> None:
    scenario = load_scenario()
    state = initial_state(scenario)
    assert state["zone"] == scenario["robot"]["start"]
    assert state["battery"] == scenario["robot"]["battery_start"]


def test_goal_is_based_on_final_station_state() -> None:
    scenario = load_scenario()
    state = initial_state(scenario)
    assert not goal_satisfied(scenario, state) if scenario["goal"]["stations_online"] else True



def test_pickup_uses_actual_item_weight_for_capacity() -> None:
    """PICKUP must enforce the item's declared weight, not a hard-coded unit weight."""
    scenario = {
        "robot": {
            "start": "A",
            "battery_start": 10,
            "battery_max": 10,
            "cargo_capacity": 1,
        },
        "doors": [],
        "panels": [],
        "stations": [],
        "keys": [],
        "tools": [{"id": "HEAVY_TOOL", "zone": "A", "weight": 2, "repairs": []}],
        "materials": [],
        "chargers": [],
        "goal": {"stations_online": []},
        "action_costs": {"pickup": 1, "drop": 1, "interact": 1, "recharge": 1},
    }
    state = initial_state(scenario)

    try:
        apply_step(
            scenario,
            state,
            {"op": "PICKUP", "item": "HEAVY_TOOL", "cost": 1},
        )
    except AssertionError as exc:
        assert "cargo full" in str(exc)
    else:
        raise AssertionError(
            "PICKUP incorrectly accepted an item heavier than remaining capacity"
        )
