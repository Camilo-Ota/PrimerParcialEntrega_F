"""Action generation (Applicable) and deterministic Result transitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from state import State


@dataclass(frozen=True, slots=True)
class Action:
    op: str
    cost: int
    data: tuple[tuple[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"op": self.op, "cost": self.cost, **dict(self.data)}


class ActionModel:
    def __init__(self, scenario: dict[str, Any]):
        self.scenario = scenario
        self.costs = scenario.get("action_costs", {})
        self.battery_max = int(scenario["robot"]["battery_max"])
        self.capacity = int(scenario["robot"]["cargo_capacity"])
        self.corridors = list(scenario.get("corridors", []))
        self.doors = {x["id"]: x for x in scenario.get("doors", [])}
        self.panels = {x["id"]: x for x in scenario.get("panels", [])}
        self.stations = {x["id"]: x for x in scenario.get("stations", [])}
        self.chargers = {x["id"]: x for x in scenario.get("chargers", [])}
        self.keys = {x["id"]: x for x in scenario.get("keys", [])}
        self.tools = {x["id"]: x for x in scenario.get("tools", [])}
        self.materials = {x["type"]: x for x in scenario.get("materials", [])}
        self._dead_items_cache: dict[tuple[tuple[str, str], ...], set[str]] = {}

    def initial_state(self) -> State:
        ground: dict[str, dict[str, int]] = {}
        for key in self.scenario.get("keys", []):
            ground.setdefault(key["zone"], {})[key["id"]] = 1
        for tool in self.scenario.get("tools", []):
            ground.setdefault(tool["zone"], {})[tool["id"]] = 1
        for mat in self.scenario.get("materials", []):
            ground.setdefault(mat["zone"], {})[mat["type"]] = ground.setdefault(mat["zone"], {}).get(mat["type"], 0) + int(mat["count"])

        environment: dict[str, str] = {}
        environment.update({f"door:{d['id']}": str(d["state"]) for d in self.doors.values()})
        environment.update({f"panel:{p['id']}": str(p["state"]) for p in self.panels.values()})
        environment.update({f"station:{s['id']}": str(s["state"]) for s in self.stations.values()})
        return State.from_parts(
            self.scenario["robot"]["start"],
            int(self.scenario["robot"]["battery_start"]),
            {},
            ground,
            environment,
        )

    def _cost(self, name: str, default: int) -> int:
        return int(self.costs.get(name, default))

    def _corridor(self, frm: str, to: str) -> dict[str, Any] | None:
        for corridor in self.corridors:
            if corridor.get("from") == frm and corridor.get("to") == to:
                return corridor
        return None

    def _item_weight(self, item: str) -> int:
        if item in self.keys:
            return int(self.keys[item].get("weight", 1))
        if item in self.tools:
            return int(self.tools[item].get("weight", 1))
        if item in self.materials:
            return int(self.materials[item].get("weight", 1))
        return 1

    def _inventory_weight(self, inventory: dict[str, int]) -> int:
        return sum(self._item_weight(k) * v for k, v in inventory.items())

    def _is_tool(self, item: str) -> bool:
        return item in self.tools

    def _is_key(self, item: str) -> bool:
        return item in self.keys

    def _dead_items(self, state: State) -> set[str]:
        env = state.environment_dict()
        dead: set[str] = set()
        for door_id, door in self.doors.items():
            if env.get(f"door:{door_id}") == "OPEN":
                key = door.get("key")
                if key:
                    dead.add(str(key))
        for panel_id, panel in self.panels.items():
            if env.get(f"panel:{panel_id}") == "OK":
                tool = panel.get("requires", {}).get("tool")
                if tool:
                    # Only kill a tool when no still-damaged panel needs it.
                    if not any(
                        env.get(f"panel:{pid}") != "OK"
                        and p.get("requires", {}).get("tool") == tool
                        for pid, p in self.panels.items()
                    ):
                        dead.add(str(tool))
        return dead

    def _required_items(self, state: State) -> dict[str, int]:
        """Return the minimum quantities of items still required by pending tasks.

        This is a sound successor-generation filter: an item is relevant only if
        some still-closed door needs its key or some still-damaged panel needs
        that tool/material. Extra copies cannot satisfy any additional
        precondition in this scenario model and only create strictly more costly
        manipulation branches.
        """
        env = state.environment_dict()
        required: dict[str, int] = {}

        for door_id, door in self.doors.items():
            if env.get(f"door:{door_id}") == "CLOSED" and door.get("key"):
                key = str(door["key"])
                required[key] = max(required.get(key, 0), 1)

        for panel_id, panel in self.panels.items():
            if env.get(f"panel:{panel_id}") != "DAMAGED":
                continue
            req = panel.get("requires", {})
            for field in ("tool", "material"):
                item = req.get(field)
                if item:
                    item = str(item)
                    required[item] = required.get(item, 0) + 1

        return required

    def _item_is_relevant(self, state: State, item: str) -> bool:
        if item in self._dead_items(state):
            return False
        required = self._required_items(state)
        inv = state.inventory_dict()
        # Never pick an additional copy beyond the amount still required.
        return inv.get(item, 0) < required.get(item, 0)

    def applicable(self, state: State) -> list[Action]:
        actions: list[Action] = []
        inv = state.inventory_dict()
        ground = state.ground_dict()
        env = state.environment_dict()
        pos = state.robot_position
        battery = state.battery

        # MOVE: only direct, currently open/unblocked corridors.
        for corridor in self.corridors:
            if corridor.get("from") != pos:
                continue
            cost = int(corridor["cost"])
            if battery < cost:
                continue
            door = corridor.get("door")
            if door and env.get(f"door:{door}") != "OPEN":
                continue
            actions.append(Action("MOVE", cost, (("from", pos), ("to", corridor["to"]))))

        # RECHARGE.
        if battery < self.battery_max:
            cost = self._cost("recharge", 1)
            if battery >= cost:
                for charger_id, charger in self.chargers.items():
                    if charger.get("zone") == pos:
                        actions.append(Action("INTERACT", cost, (("target", charger_id), ("action", "RECHARGE"))))

        # PICKUP, aggregated by item type/id.
        for item, count in ground.get(pos, {}).items():
            if count <= 0 or not self._item_is_relevant(state, item):
                continue
            cost = self._cost("pickup", 1)
            if battery < cost:
                continue
            if self._inventory_weight(inv) + self._item_weight(item) <= self.capacity:
                actions.append(Action("PICKUP", cost, (("item", item),)))

        # INTERACT: doors, repairs and station activation.
        interact_cost = self._cost("interact", 1)
        if battery >= interact_cost:
            for door_id, door in self.doors.items():
                if env.get(f"door:{door_id}") != "CLOSED":
                    continue
                if pos not in tuple(door.get("between", [])):
                    continue
                key = door.get("key")
                if inv.get(key, 0) > 0:
                    actions.append(Action("INTERACT", interact_cost, (("target", door_id), ("action", "OPEN_DOOR"))))

            for panel_id, panel in self.panels.items():
                if env.get(f"panel:{panel_id}") != "DAMAGED" or panel.get("zone") != pos:
                    continue
                req = panel.get("requires", {})
                tool = req.get("tool")
                material = req.get("material")
                if tool and inv.get(tool, 0) <= 0:
                    continue
                if material and inv.get(material, 0) <= 0:
                    continue
                actions.append(Action("INTERACT", interact_cost, (("target", panel_id), ("action", "REPAIR"), ("consumes", material))))

            for station_id, station in self.stations.items():
                if env.get(f"station:{station_id}") != "OFFLINE" or station.get("zone") != pos:
                    continue
                req = station.get("requires", {})
                if any(env.get(f"panel:{pid}") != "OK" for pid in req.get("panels_ok", [])):
                    continue
                if any(env.get(f"station:{sid}") != "ONLINE" for sid in req.get("stations_online", [])):
                    continue
                actions.append(Action("INTERACT", interact_cost, (("target", station_id), ("action", "ACTIVATE"))))

        # DROP: restrict successors to capacity-releasing situations.  The
        # simulator accepts any legal DROP, but the search does not enumerate
        # arbitrary placements.  A DROP is generated only when a relevant
        # object in the current zone does not fit and dropping a carried item
        # can make that pickup fit.  Dead objects remain eligible because they
        # no longer have future utility but still consume physical capacity.
        drop_cost = self._cost("drop", 1)
        if inv and battery >= drop_cost:
            local = ground.get(pos, {})
            pickup_candidates = [
                item for item, count in local.items()
                if count > 0
                and self._item_is_relevant(state, item)
                and self._inventory_weight(inv) + self._item_weight(item) > self.capacity
            ]

            if pickup_candidates:
                current_weight = self._inventory_weight(inv)
                dead = self._dead_items(state)
                for item in sorted(inv):
                    remaining_weight = current_weight - self._item_weight(item)
                    if any(
                        remaining_weight + self._item_weight(candidate) <= self.capacity
                        for candidate in pickup_candidates
                    ):
                        # Relevant items are also allowed here because a plan
                        # may need to free capacity temporarily; the important
                        # restriction is that the DROP must solve a concrete
                        # local capacity conflict rather than relocate an
                        # object arbitrarily.
                        if item in dead or self._item_is_relevant(state, item):
                            actions.append(Action("DROP", drop_cost, (("item", item),)))

        return actions

    def result(self, state: State, action: Action) -> State:
        data = action.as_dict()
        if state.battery < action.cost:
            raise ValueError("Insufficient battery")
        inv = state.inventory_dict()
        ground = state.ground_dict()
        env = state.environment_dict()
        pos = state.robot_position
        battery = state.battery - action.cost

        op = action.op
        if op == "MOVE":
            return state.with_parts(robot_position=data["to"], battery=battery)

        if op == "PICKUP":
            item = data["item"]
            if ground.get(pos, {}).get(item, 0) <= 0:
                raise ValueError(f"{item} is not on the ground at {pos}")
            ground[pos][item] -= 1
            if ground[pos][item] <= 0:
                del ground[pos][item]
            inv[item] = inv.get(item, 0) + 1
            return self._canonicalize_dead(state.with_parts(battery=battery, inventory=inv, ground=ground, environment=env))

        if op == "DROP":
            item = data["item"]
            if inv.get(item, 0) <= 0:
                raise ValueError(f"{item} is not in inventory")
            inv[item] -= 1
            if inv[item] <= 0:
                del inv[item]
            ground.setdefault(pos, {})[item] = ground.setdefault(pos, {}).get(item, 0) + 1
            return self._canonicalize_dead(state.with_parts(battery=battery, inventory=inv, ground=ground, environment=env))

        if op == "INTERACT":
            target, subaction = data["target"], data["action"]
            if subaction == "RECHARGE":
                return state.with_parts(battery=self.battery_max)
            if subaction == "OPEN_DOOR":
                env[f"door:{target}"] = "OPEN"
            elif subaction == "REPAIR":
                panel = self.panels[target]
                material = panel.get("requires", {}).get("material")
                if material:
                    inv[material] -= 1
                    if inv[material] <= 0:
                        del inv[material]
                env[f"panel:{target}"] = "OK"
            elif subaction == "ACTIVATE":
                env[f"station:{target}"] = "ONLINE"
            else:
                raise ValueError(f"Unknown interaction {subaction}")
            return self._canonicalize_dead(state.with_parts(battery=battery, inventory=inv, environment=env))

        raise ValueError(f"Unknown op {op}")

    def _canonicalize_dead(self, state: State) -> State:
        dead = self._dead_items(state)
        if not dead:
            return state.canonicalized()
        inv = state.inventory_dict()
        ground = state.ground_dict()
        # Dead objects remain in the carried inventory because their physical
        # weight still matters to cargo capacity. Their ground position is
        # irrelevant and is therefore removed from the search representation.
        for item in dead:
            for zone in list(ground):
                ground[zone].pop(item, None)
                if not ground[zone]:
                    del ground[zone]
        return state.with_parts(inventory=inv, ground=ground)


def applicable(scenario: dict[str, Any], state: State) -> list[Action]:
    return ActionModel(scenario).applicable(state)


def result(scenario: dict[str, Any], state: State, action: Action) -> State:
    return ActionModel(scenario).result(state, action)
