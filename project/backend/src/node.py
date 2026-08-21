"""Search node: state plus the history needed to reconstruct a plan."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from state import State


@dataclass(slots=True)
class Node:
    state: State
    parent: "Node | None" = None
    action: dict[str, Any] | None = None
    path_cost: int = 0
    depth: int = 0

    @property
    def g(self) -> int:
        return self.path_cost

    def child(self, state: State, action: dict[str, Any], cost: int) -> "Node":
        return Node(
            state=state,
            parent=self,
            action=action,
            path_cost=self.path_cost + int(cost),
            depth=self.depth + 1,
        )

    def plan(self) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        node: Node | None = self
        while node is not None and node.action is not None:
            actions.append(dict(node.action))
            node = node.parent
        actions.reverse()
        return actions
