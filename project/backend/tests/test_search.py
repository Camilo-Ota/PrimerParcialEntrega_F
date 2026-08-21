"""Tests for the UCS agent and canonical search state."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from actions import ActionModel  # noqa: E402
from node import Node  # noqa: E402
from search import UCSAgent  # noqa: E402
from state import State  # noqa: E402


def scenario() -> dict:
    return {
        "robot": {"start": "A", "battery_start": 10, "battery_max": 10, "cargo_capacity": 2},
        "corridors": [
            {"from": "A", "to": "B", "cost": 1},
            {"from": "B", "to": "A", "cost": 1},
        ],
        "doors": [], "keys": [], "tools": [], "materials": [], "panels": [],
        "chargers": [],
        "stations": [{"id": "S", "zone": "B", "state": "OFFLINE", "requires": {}}],
        "goal": {"stations_online": ["S"]},
        "action_costs": {"interact": 1, "pickup": 1, "drop": 1, "recharge": 1},
    }


def test_state_is_canonical_and_hashable() -> None:
    a = State.from_parts("A", 5, {"FUSE": 2, "TOOL": 1}, {"B": {"FUSE": 1}}, {"station:S": "OFFLINE"})
    b = State.from_parts("A", 5, {"TOOL": 1, "FUSE": 2}, {"B": {"FUSE": 1}}, {"station:S": "OFFLINE"})
    assert a == b
    assert hash(a) == hash(b)


def test_node_keeps_history_outside_state() -> None:
    state = State.from_parts("A", 5, {}, {}, {})
    node = Node(state, path_cost=7, depth=2, action={"op": "MOVE", "cost": 1})
    assert node.g == 7
    assert not hasattr(state, "parent")
    assert not hasattr(state, "path_cost")


def test_ucs_returns_goal_on_extraction() -> None:
    result = UCSAgent(scenario()).solve_node()
    assert result.node is not None
    assert result.node.g == 2
    assert result.node.plan()[-1]["action"] == "ACTIVATE"


def test_recharge_is_deterministic() -> None:
    s = scenario()
    s["chargers"] = [{"id": "C", "zone": "A"}]
    model = ActionModel(s)
    state = model.initial_state().with_parts(battery=5)
    recharge = next(a for a in model.applicable(state) if a.as_dict().get("action") == "RECHARGE")
    result = model.result(state, recharge)
    assert result.battery == 10


def test_drop_generation_handles_weighted_items_below_full_capacity() -> None:
    """DROP must work when the payload is below capacity but a heavy item does not fit."""
    s = {
        "robot": {"start": "A", "battery_start": 20, "battery_max": 20, "cargo_capacity": 5},
        "corridors": [],
        "doors": [{"id": "D", "key": "KEY", "state": "CLOSED", "between": ["A", "B"]}],
        "keys": [{"id": "KEY", "color": "x", "zone": "A", "weight": 4}],
        "tools": [{"id": "TOOL", "repairs": "X", "zone": "B", "weight": 2}],
        "materials": [],
        "panels": [{"id": "P", "zone": "B", "state": "OK", "requires": {"tool": "TOOL", "material": "X"}}],
        "stations": [{"id": "S", "zone": "A", "state": "OFFLINE", "requires": {}}],
        "chargers": [],
        "goal": {"stations_online": ["S"]},
        "action_costs": {"interact": 1, "pickup": 1, "drop": 1, "recharge": 1},
    }
    model = ActionModel(s)
    state = State.from_parts(
        "A",
        20,
        {"TOOL": 1},
        {"A": {"KEY": 1}},
        {"door:D": "CLOSED", "panel:P": "OK", "station:S": "OFFLINE"},
    )
    drops = [
        a for a in model.applicable(state)
        if a.op == "DROP" and a.as_dict().get("item") == "TOOL"
    ]
    assert len(drops) == 1
