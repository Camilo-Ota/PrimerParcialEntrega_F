"""Canonical search state for the Emergency Control agent.

The State contains only physical/logical fluents. Search-history metadata
(g, parent, action and depth) belongs to Node.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _sorted_pairs(values: Mapping[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((str(k), int(v)) for k, v in values.items() if int(v) > 0))


def _canonical_ground(values: Mapping[str, Mapping[str, int]]) -> tuple[tuple[str, tuple[tuple[str, int], ...]], ...]:
    rows: list[tuple[str, tuple[tuple[str, int], ...]]] = []
    for zone, items in values.items():
        pairs = _sorted_pairs(items)
        if pairs:
            rows.append((str(zone), pairs))
    return tuple(sorted(rows))


@dataclass(frozen=True, slots=True)
class State:
    """Immutable, hashable physical state.

    inventory and ground are canonical tuples.  Equivalent consumables are
    represented by quantities instead of object-instance IDs.
    """

    robot_position: str
    battery: int
    inventory: tuple[tuple[str, int], ...]
    ground: tuple[tuple[str, tuple[tuple[str, int], ...]], ...]
    environment: tuple[tuple[str, str], ...]

    @classmethod
    def from_parts(
        cls,
        robot_position: str,
        battery: int,
        inventory: Mapping[str, int],
        ground: Mapping[str, Mapping[str, int]],
        environment: Mapping[str, str],
    ) -> "State":
        return cls(
            robot_position=str(robot_position),
            battery=int(battery),
            inventory=_sorted_pairs(inventory),
            ground=_canonical_ground(ground),
            environment=tuple(sorted((str(k), str(v)) for k, v in environment.items())),
        )

    def inventory_dict(self) -> dict[str, int]:
        return dict(self.inventory)

    def ground_dict(self) -> dict[str, dict[str, int]]:
        return {zone: dict(items) for zone, items in self.ground}

    def environment_dict(self) -> dict[str, str]:
        return dict(self.environment)

    def world_key(self) -> tuple[Any, ...]:
        """Physical configuration excluding battery, for battery dominance."""
        return (self.robot_position, self.inventory, self.ground, self.environment)

    def canonicalized(self) -> "State":
        """Return the canonical representation (already canonical by design)."""
        return self

    def with_parts(
        self,
        *,
        robot_position: str | None = None,
        battery: int | None = None,
        inventory: Mapping[str, int] | None = None,
        ground: Mapping[str, Mapping[str, int]] | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> "State":
        return State.from_parts(
            robot_position if robot_position is not None else self.robot_position,
            battery if battery is not None else self.battery,
            inventory if inventory is not None else self.inventory_dict(),
            ground if ground is not None else self.ground_dict(),
            environment if environment is not None else self.environment_dict(),
        )
