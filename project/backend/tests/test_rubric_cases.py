"""Required rubric tests: equivalence, relevance, cost, failure and alternatives."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from actions import ActionModel  # noqa: E402
from search import UCSAgent, solve  # noqa: E402
from state import State  # noqa: E402


def base_scenario() -> dict:
    return {
        "robot": {"start": "A", "battery_start": 50, "battery_max": 50, "cargo_capacity": 3},
        "zones": [],
        "corridors": [],
        "doors": [],
        "keys": [],
        "tools": [],
        "materials": [],
        "panels": [],
        "chargers": [],
        "stations": [],
        "goal": {"stations_online": ["S"]},
        "action_costs": {"pickup": 1, "drop": 1, "interact": 1, "recharge": 1},
    }


def scenario_with_corridors(corridors: list[dict], *, goal_zone: str = "G") -> dict:
    s = base_scenario()
    s["corridors"] = corridors
    s["stations"] = [{"id": "S", "zone": goal_zone, "state": "OFFLINE", "requires": {}}]
    return s


def test_case_1_equivalent_histories_produce_same_logical_state() -> None:
    """Case 1: ordering/representation history must not create a new State."""
    state_from_history_a = State.from_parts(
        "Z2",
        40,
        {"KEY_BLUE": 1, "FUSE": 2, "TOOL_X": 1},
        {"Z1": {"FUSE": 1, "CHIP": 1}, "Z3": {"KEY_RED": 1}},
        {"door:D1": "OPEN", "panel:P1": "OK", "station:S": "OFFLINE"},
    )
    state_from_history_b = State.from_parts(
        "Z2",
        40,
        {"TOOL_X": 1, "FUSE": 2, "KEY_BLUE": 1},
        {"Z3": {"KEY_RED": 1}, "Z1": {"CHIP": 1, "FUSE": 1}},
        {"station:S": "OFFLINE", "panel:P1": "OK", "door:D1": "OPEN"},
    )

    assert state_from_history_a == state_from_history_b
    assert hash(state_from_history_a) == hash(state_from_history_b)
    assert state_from_history_a.world_key() == state_from_history_b.world_key()


def test_case_2_relevant_information_keeps_states_distinct() -> None:
    """Case 2: changing a future-relevant fluent must change the State."""
    closed = State.from_parts(
        "Z2", 40, {"KEY_BLUE": 1}, {}, {"door:D1": "CLOSED", "station:S": "OFFLINE"}
    )
    opened = State.from_parts(
        "Z2", 40, {"KEY_BLUE": 1}, {}, {"door:D1": "OPEN", "station:S": "OFFLINE"}
    )

    assert closed != opened
    assert closed.world_key() != opened.world_key()

    scenario = base_scenario()
    scenario["corridors"] = [{"from": "Z2", "to": "Z3", "cost": 1, "door": "D1"}]
    scenario["doors"] = [{"id": "D1", "key": "KEY_BLUE", "state": "CLOSED", "between": ["Z2", "Z3"]}]
    model = ActionModel(scenario)
    assert not any(a.op == "MOVE" for a in model.applicable(closed))
    assert any(a.op == "MOVE" for a in model.applicable(opened))

    # The environment fluent is part of the canonical world key and changes
    # which successor actions are applicable.
    assert closed.environment_dict()["door:D1"] != opened.environment_dict()["door:D1"]


def test_case_3_fewer_actions_is_not_always_lower_cost() -> None:
    """Case 3: UCS minimizes path cost, not number of actions."""
    scenario = scenario_with_corridors(
        [
            # 2 moves + activation = 3 actions, cost 21.
            {"from": "A", "to": "B", "cost": 1},
            {"from": "B", "to": "G", "cost": 20},
            # 3 moves + activation = 4 actions, cost 7.
            {"from": "A", "to": "C", "cost": 2},
            {"from": "C", "to": "D", "cost": 2},
            {"from": "D", "to": "G", "cost": 2},
        ]
    )

    result = solve(scenario)
    assert result["solution_found"] is True
    assert result["total_cost"] == 7
    assert [step["to"] for step in result["steps"] if step["op"] == "MOVE"] == ["C", "D", "G"]
    # UCS selected four actions (3 MOVE + 1 ACTIVATE), although a 3-action
    # route exists (2 MOVE + 1 ACTIVATE).
    assert len(result["steps"]) == 4


def test_case_4_impossible_mission_returns_failure_and_terminates() -> None:
    """Case 4: an unreachable goal must return explicit FAILURE, not hang."""
    scenario = base_scenario()
    scenario["stations"] = [
        {"id": "S", "zone": "B", "state": "OFFLINE", "requires": {"panels_ok": ["P"]}}
    ]
    scenario["panels"] = [
        {"id": "P", "zone": "B", "state": "DAMAGED", "requires": {"tool": "T", "material": "FUSE"}}
    ]
    # No corridor, tool, or material exists. The frontier is finite and empty.

    result = solve(scenario)
    assert result["solution_found"] is False
    assert result["message"] == "FAILURE"
    assert result["steps"] == []


def test_case_5_alternative_routes_keep_the_lower_cost_route() -> None:
    """Case 5: same final world condition via different routes; UCS keeps cheapest."""
    scenario = scenario_with_corridors(
        [
            {"from": "A", "to": "B", "cost": 3},
            {"from": "B", "to": "G", "cost": 3},
            {"from": "A", "to": "C", "cost": 1},
            {"from": "C", "to": "G", "cost": 10},
        ]
    )

    result = solve(scenario)
    assert result["solution_found"] is True
    assert result["total_cost"] == 7
    moves = [step["to"] for step in result["steps"] if step["op"] == "MOVE"]
    assert moves == ["B", "G"]

    # Both routes reach exactly the same goal world (robot at G, station S online),
    # but UCS must retain the cheaper route.
    assert sum(step["cost"] for step in result["steps"]) == result["total_cost"]
