"""Uniform-Cost Graph Search with battery dominance."""
from __future__ import annotations

import heapq
from dataclasses import dataclass
from itertools import count
from typing import Any

from actions import ActionModel
from node import Node
from state import State


@dataclass(slots=True)
class SearchResult:
    node: Node | None
    expanded: int


class UCSAgent:
    def __init__(self, scenario: dict[str, Any]):
        self.model = ActionModel(scenario)
        self.scenario = scenario
        self.expanded = 0

    def goal_test(self, state: State) -> bool:
        env = state.environment_dict()
        targets = self.scenario.get("goal", {}).get("stations_online", [])
        return all(env.get(f"station:{sid}") == "ONLINE" for sid in targets)

    def solve_node(self) -> SearchResult:
        initial = Node(self.model.initial_state())
        frontier: list[tuple[int, int, Node]] = []
        serial = count()
        heapq.heappush(frontier, (0, next(serial), initial))

        # CLOSED[W] = maximum residual battery seen when W was expanded.
        closed: dict[tuple[Any, ...], int] = {}
        # Best queued pair used to lazily discard strictly dominated OPEN nodes.
        best_open: dict[tuple[Any, ...], list[tuple[int, int]]] = {}

        while frontier:
            g, _, node = heapq.heappop(frontier)
            state = node.state
            world = state.world_key()

            queued = best_open.get(world)
            if queued is not None:
                # Remove this exact queued pair if present.
                try:
                    queued.remove((g, state.battery))
                except ValueError:
                    pass
                if not queued:
                    best_open.pop(world, None)

            closed_battery = closed.get(world)
            if closed_battery is not None and state.battery <= closed_battery:
                continue

            # UCS checks the goal when a node is extracted, never on generation.
            if self.goal_test(state):
                return SearchResult(node=node, expanded=self.expanded)

            closed[world] = state.battery
            self.expanded += 1

            for action in self.model.applicable(state):
                child_state = self.model.result(state, action).canonicalized()
                child_g = node.g + action.cost
                child_world = child_state.world_key()

                previous_closed = closed.get(child_world)
                if previous_closed is not None and child_state.battery <= previous_closed:
                    continue

                # If an OPEN route has no better cost and at least as much battery,
                # the candidate cannot improve any future plan.
                existing = best_open.get(child_world, [])
                dominated = any(existing_g <= child_g and existing_battery >= child_state.battery for existing_g, existing_battery in existing)
                if dominated:
                    continue

                child = node.child(child_state, action.as_dict(), action.cost)
                heapq.heappush(frontier, (child_g, next(serial), child))
                best_open.setdefault(child_world, []).append((child_g, child_state.battery))

        return SearchResult(node=None, expanded=self.expanded)


def solve(scenario: dict[str, Any]) -> dict[str, Any]:
    agent = UCSAgent(scenario)
    result = agent.solve_node()
    if result.node is None:
        return {
            "solution_found": False,
            "total_cost": None,
            "steps": [],
            "message": "FAILURE",
        }

    return {
        "solution_found": True,
        "total_cost": result.node.g,
        "steps": result.node.plan(),
        "message": "UCS solution found.",
    }
